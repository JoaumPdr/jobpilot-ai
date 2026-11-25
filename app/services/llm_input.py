"""Prepara a entrada delimitada e mínima para a análise LLM de uma vaga."""

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from unicodedata import category
from uuid import UUID

from app.llm.job_analysis import JobAnalysisPrompt, load_job_analysis_prompt
from app.schemas.matching import MatchAnalysis
from app.services.skill_taxonomy import get_default_skill_taxonomy

MAX_JOB_DESCRIPTION_CHARS = 8_000
_DELIMITER_ESCAPES = str.maketrans({"<": r"\u003c", ">": r"\u003e", "|": r"\u007c"})


@dataclass(frozen=True, slots=True)
class JobAnalysisInput:
    """Prompt versionado e mensagem de dados para a mesma análise."""

    prompt: JobAnalysisPrompt
    user_prompt: str = field(repr=False)


def _sanitize_description(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Mantém as linhas legíveis e descarta controles, formatação e pontos substitutos.
    return "".join(
        char
        for char in text
        if char in "\n\t" or category(char) not in {"Cc", "Cf", "Cs"}
    ).strip()


def _catalog_skill_names(terms: Iterable[str | None]) -> list[str]:
    # Nomes canônicos do catálogo evitam repassar texto livre cadastrado no perfil.
    taxonomy = get_default_skill_taxonomy()
    names: set[str] = set()
    for term in terms:
        if term is None:
            continue
        skill = taxonomy.lookup(term)
        if skill is not None:
            names.add(skill.canonical_name)
    return sorted(names)


def prepare_job_analysis_input(
    *,
    job_id: UUID,
    description: str | None,
    matching: MatchAnalysis,
) -> JobAnalysisInput:
    """Monta os dados da vaga e as habilidades pertinentes registradas no matching."""
    raw_description = description or ""
    payload = {
        "job_id": str(job_id),
        "job": {
            "description": _sanitize_description(
                raw_description[:MAX_JOB_DESCRIPTION_CHARS]
            ),
            "description_truncated": len(raw_description) > MAX_JOB_DESCRIPTION_CHARS,
        },
        "profile": {
            "skills": _catalog_skill_names(
                item.candidate_skill for item in matching.met
            ),
            "confirmed_absent": _catalog_skill_names(
                item.skill_name for item in matching.absent
            ),
        },
    }
    # O JSON mantém o texto dentro do campo, inclusive quando ele contém aspas.
    # Escapa delimitadores angulares e barras verticais no texto serializado.
    user_prompt = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    ).translate(_DELIMITER_ESCAPES)
    return JobAnalysisInput(prompt=load_job_analysis_prompt(), user_prompt=user_prompt)
