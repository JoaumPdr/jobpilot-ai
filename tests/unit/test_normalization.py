"""Testes das funções puras de normalização de vagas (F1-T04).

POR QUÊ: estas funções decidem se duas vagas parecem iguais. Os testes cobrem
as variações reais de planilha/portal (acentos, caixa, espaços, parâmetros de
rastreio) sem banco e sem rede — o mesmo cenário que o CI roda.
"""

from __future__ import annotations

import pytest

from app.models import Seniority, WorkMode
from app.services.normalization import (
    canonicalize_url,
    clean_text,
    comparison_text,
    job_fingerprint,
    normalize_seniority,
    normalize_work_mode,
)

# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, ""),
        ("  ", ""),
        ("  Ana   Silva ", "Ana Silva"),
        ("Engenheira\n de\tDados", "Engenheira de Dados"),
        ("São  Paulo", "São Paulo"),
    ],
)
def test_clean_text_preserves_accents_and_case(raw: str | None, expected: str) -> None:
    """A exibição mantém acentos/caixa; só espaços são normalizados."""
    assert clean_text(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  São   Paulo ", "sao paulo"),
        ("JÚNIOR", "junior"),
        ("Híbrido", "hibrido"),
        ("AÇÃO", "acao"),
        (None, ""),
    ],
)
def test_comparison_text_removes_accents_and_case(
    raw: str | None, expected: str
) -> None:
    """A comparação/dedup usa a forma sem acento e minúscula."""
    assert comparison_text(raw) == expected


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Remoto", WorkMode.REMOTO),
        ("home office", WorkMode.REMOTO),
        ("REMOTA", WorkMode.REMOTO),
        ("à distância", WorkMode.REMOTO),
        ("Híbrido", WorkMode.HIBRIDO),
        ("hybrid", WorkMode.HIBRIDO),
        ("Presencial", WorkMode.PRESENCIAL),
        ("on-site", WorkMode.PRESENCIAL),
        ("", WorkMode.DESCONHECIDO),
        ("qualquer lugar", WorkMode.DESCONHECIDO),
    ],
)
def test_normalize_work_mode(raw: str, expected: WorkMode) -> None:
    """Sinônimos PT/EN são mapeados; o resto vira 'desconhecido'."""
    assert normalize_work_mode(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Estágio", Seniority.ESTAGIO),
        ("estagiário", Seniority.ESTAGIO),
        ("Intern", Seniority.ESTAGIO),
        ("Júnior", Seniority.JUNIOR),
        ("jr", Seniority.JUNIOR),
        ("Pleno", Seniority.PLENO),
        ("mid-level", Seniority.PLENO),
        ("Sênior", Seniority.SENIOR),
        ("SR", Seniority.SENIOR),
        ("Especialista", Seniority.ESPECIALISTA),
        ("Specialist", Seniority.ESPECIALISTA),
        ("Gerente", Seniority.DESCONHECIDO),
        (None, Seniority.DESCONHECIDO),
    ],
)
def test_normalize_seniority(raw: str | None, expected: Seniority) -> None:
    """Senioridade segue a mesma regra de sinônimos e fallback."""
    assert normalize_seniority(raw) == expected


# ---------------------------------------------------------------------------
# URL canônica
# ---------------------------------------------------------------------------


def test_canonicalize_url_removes_tracking_and_orders_params() -> None:
    """Parâmetros de rastreio saem; os demais ficam ordenados."""
    raw = (
        "HTTPS://Portal.COM:443/vagas//123/"
        "?utm_source=newsletter&b=2&a=1&fbclid=xyz#topo"
    )

    assert canonicalize_url(raw) == "https://portal.com/vagas/123?a=1&b=2"


def test_canonicalize_url_keeps_meaningful_query() -> None:
    """ID/parâmetros relevantes não são tratados como rastreio."""
    assert (
        canonicalize_url("https://portal.com/vaga?jobId=42&source=portal")
        == "https://portal.com/vaga?jobId=42&source=portal"
    )


def test_canonicalize_url_assumes_https_without_scheme() -> None:
    """CSV costuma trazer o domínio sem esquema."""
    assert canonicalize_url("  portal.com/vagas/7  ") == "https://portal.com/vagas/7"


def test_canonicalize_url_drops_default_port_and_fragment() -> None:
    """Porta padrão e fragmento não distinguem vagas."""
    assert (
        canonicalize_url("http://portal.com:80/vaga#descricao")
        == "http://portal.com/vaga"
    )


def test_canonicalize_url_is_idempotent() -> None:
    """Canonizar de novo não muda mais nada."""
    once = canonicalize_url("https://portal.com/vaga/?utm_medium=email")
    assert canonicalize_url(once) == once


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "ftp://portal.com/vaga",
        "javascript:alert(1)",
        "https:///sem-host",
    ],
)
def test_canonicalize_url_rejects_invalid_values(raw: str) -> None:
    """URL inválida vira ValueError para o importador rejeitar a linha."""
    with pytest.raises(ValueError):
        canonicalize_url(raw)


# ---------------------------------------------------------------------------
# Fingerprint
# ---------------------------------------------------------------------------


def test_fingerprint_is_stable_across_spellings() -> None:
    """Caixa, acentos e espaços não mudam o hash."""
    first = job_fingerprint("Empresa X", "Engenheira de Dados", "São Paulo")
    second = job_fingerprint(" empresa  x ", "ENGENHEIRA DE DADOS", "sao  paulo")

    assert first == second
    assert len(first) == 64
    assert all(char in "0123456789abcdef" for char in first)


def test_fingerprint_changes_with_company_title_or_location() -> None:
    """Qualquer um dos três campos muda o hash."""
    base = job_fingerprint("Empresa X", "Engenheira de Dados", "São Paulo")

    assert job_fingerprint("Empresa Y", "Engenheira de Dados", "São Paulo") != base
    assert job_fingerprint("Empresa X", "Tech Lead", "São Paulo") != base
    assert job_fingerprint("Empresa X", "Engenheira de Dados", "Remoto") != base


def test_fingerprint_accepts_missing_location() -> None:
    """Localização ausente é tratada como string vazia, sem erro."""
    assert job_fingerprint("Empresa X", "Engenheira de Dados", None) != ""
