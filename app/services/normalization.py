"""Normalização e canonização de vagas — funções puras.

POR QUÊ: cadastro manual (F1-T05) e importação CSV (F1-T06) recebem o mesmo
dado escrito de formas diferentes ("São Paulo", "sao paulo ", "SÃO  PAULO").
Sem normalizar, a dedup por fingerprint e a busca por localização falham.

Regra do plano: normalizar **para comparação** sem alterar o texto exibido.
Por isso há duas funções de texto: `clean_text` (exibição) e `comparison_text`
(comparação/dedup). Nada aqui acessa banco, rede ou relógio — são funções
puras e, por isso, testáveis em milissegundos.
"""

from __future__ import annotations

import hashlib
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.models import Seniority, WorkMode

# Prefixo de campanha (Google Analytics etc.): qualquer chave `utm_*` é rastreio.
_TRACKING_PREFIXES = ("utm_",)
# Lista fechada e conservadora. `source`/`src` ficam de fora porque podem ser
# o identificador da vaga no portal, e removê-los fundiria vagas distintas.
_TRACKING_PARAMS = frozenset(
    {
        "fbclid",
        "gclid",
        "gbraid",
        "wbraid",
        "yclid",
        "msclkid",
        "mc_cid",
        "mc_eid",
        "igshid",
        "ref",
        "ref_src",
        "trk",
        "_hsenc",
    }
)
_ALLOWED_SCHEMES = frozenset({"http", "https"})
_DEFAULT_PORTS = {"http": 80, "https": 443}


def clean_text(value: str | None) -> str:
    """Apara as pontas e colapsa espaços internos, preservando acentos/caixa.

    Espaços, tabs e quebras de linha viram um único espaço — é o formato que
    queremos exibir em títulos, empresas e localizações.
    """
    if value is None:
        return ""
    return " ".join(value.split())


def comparison_text(value: str | None) -> str:
    """Forma comparável: sem acentos, minúscula e com espaços colapsados.

    Usada em fingerprint e em comparações de igualdade (ex.: nome de empresa).
    Não serve para exibir: devolve `sao paulo` para `São Paulo`.
    """
    cleaned = clean_text(value)
    # NFKD separa a letra do acento; descartar os combining marks remove o
    # acento e mantém a letra base (á → a), sem depender de locale.
    decomposed = unicodedata.normalize("NFKD", cleaned)
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return " ".join(without_accents.casefold().split())


def normalize_work_mode(value: str | None) -> WorkMode:
    """Mapeia modalidade escrita de várias formas para o enum do banco."""
    key = comparison_text(value)
    if key in {
        "remoto",
        "remota",
        "remote",
        "home office",
        "homeoffice",
        "teletrabalho",
        "a distancia",
        "anywhere",
    }:
        return WorkMode.REMOTO
    if key in {"hibrido", "hibrida", "hybrid"}:
        return WorkMode.HIBRIDO
    if key in {"presencial", "on site", "on-site", "onsite"}:
        return WorkMode.PRESENCIAL
    return WorkMode.DESCONHECIDO


def normalize_seniority(value: str | None) -> Seniority:
    """Mapeia senioridade escrita de várias formas para o enum do banco."""
    key = comparison_text(value)
    if key in {"estagio", "estagiario", "estagiaria", "intern", "internship"}:
        return Seniority.ESTAGIO
    if key in {"junior", "jr"}:
        return Seniority.JUNIOR
    if key in {"pleno", "pl", "mid", "mid level", "mid-level"}:
        return Seniority.PLENO
    if key in {"senior", "sr"}:
        return Seniority.SENIOR
    if key in {"especialista", "specialist"}:
        return Seniority.ESPECIALISTA
    return Seniority.DESCONHECIDO


def canonicalize_url(value: str | None) -> str:
    """Devolve a URL canônica usada na deduplicação (camada 2).

    Regras: esquema `http`/`https` (sem esquema assume `https`), host em
    minúsculas, porta padrão e fragmento descartados, barra final removida,
    parâmetros de rastreio descartados e os demais ordenados. A operação é
    idempotente: canonizar de novo devolve o mesmo valor.

    Levanta `ValueError` para URL vazia, sem host ou com esquema não suportado
    — o importador converte isso em linha rejeitada (F1-T06).
    """
    raw = (value or "").strip()
    if not raw:
        raise ValueError("URL vazia.")

    # CSV costuma trazer "portal.com/vaga/1" sem esquema; assumir HTTPS é
    # seguro e evita rejeitar linhas boas por um detalhe de planilha.
    if "://" not in raw:
        raw = f"https://{raw}"

    parts = urlsplit(raw)
    scheme = parts.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"Esquema de URL não suportado: {parts.scheme!r}.")

    host = (parts.hostname or "").lower().rstrip(".")
    if not host:
        raise ValueError("URL sem host.")

    netloc = host
    if parts.port is not None and parts.port != _DEFAULT_PORTS.get(scheme):
        netloc = f"{host}:{parts.port}"
    # Credenciais embutidas na URL não entram na forma canônica.
    path = parts.path or "/"
    # Barras duplicadas (`//`) não mudam o recurso e sujam a comparação.
    while "//" in path:
        path = path.replace("//", "/")
    if len(path) > 1:
        path = path.rstrip("/")

    query = urlencode(
        sorted(
            (key, val)
            for key, val in parse_qsl(parts.query, keep_blank_values=True)
            if key.lower() not in _TRACKING_PARAMS
            and not key.lower().startswith(_TRACKING_PREFIXES)
        )
    )
    # `fragment` (#secao) não identifica a vaga e é descartado.
    return urlunsplit((scheme, netloc, path, query, ""))


def job_fingerprint(
    company: str | None, title: str | None, location: str | None = None
) -> str:
    """SHA-256 de empresa + título + localização, na forma comparável.

    É a camada 3 da dedup: duas vagas com o mesmo trio em grafias diferentes
    geram o mesmo hash. O hash não é único no banco — apenas sinaliza.
    """
    payload = "|".join(
        (comparison_text(company), comparison_text(title), comparison_text(location))
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
