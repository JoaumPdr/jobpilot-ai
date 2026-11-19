"""Similaridade textual entre vagas — camada 4 da deduplicação.

POR QUÊ: as camadas 1–3 comparam igualdade (identificador, URL e fingerprint).
Duas vagas reais podem ser a mesma publicação com pequenas diferenças de
título ("Engenheiro de Dados Sênior" x "Engenheiro de Dados Sr."), que nenhuma
igualdade pega. A similaridade sinaliza essa possibilidade — **nunca** apaga ou
bloqueia: quem decide é o usuário, confirmando via `duplicate_of_job_id`.

O cálculo é feito sobre `comparison_text` (sem acentos, minúsculo, espaços
colapsados), então grafias diferentes do mesmo título recebem a mesma nota.
RapidFuzz é determinístico e não acessa rede, banco ou relógio.
"""

from __future__ import annotations

from rapidfuzz import fuzz

from app.services.normalization import comparison_text

# Limiar da camada 4. Abaixo disso o falso positivo vira ruído na revisão;
# acima, títulos como "Desenvolvedor Python" x "Desenvolvedor Python Pleno"
# aparecem como possível duplicata — o que é aceitável, porque só sinaliza.
SIMILARITY_THRESHOLD = 85.0


def title_similarity(left: str | None, right: str | None) -> float:
    """Nota de 0 a 100 para dois títulos, na forma comparável.

    `token_set_ratio` ignora ordem e repetição de palavras e dá 100 quando um
    título é subconjunto do outro. Títulos vazios recebem 0: sem texto não há
    evidência para sugerir duplicata.
    """
    first = comparison_text(left)
    second = comparison_text(right)
    if not first or not second:
        return 0.0
    if first == second:
        return 100.0
    return float(fuzz.token_set_ratio(first, second))


def is_similar(left: str | None, right: str | None) -> bool:
    """Indica se dois títulos passam do limiar da camada 4."""
    return title_similarity(left, right) >= SIMILARITY_THRESHOLD
