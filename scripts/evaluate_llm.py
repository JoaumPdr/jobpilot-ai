"""Compara afirmações de matching no golden set com uma execução local do LLM."""

import argparse
import http.client
import json
import sys
from collections import Counter
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from statistics import median
from time import perf_counter
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.llm.job_analysis import JobAnalysisOutput, JobAnalysisOutputError
from app.llm.providers import LLMProvider, LLMProviderError, LLMResponse, OllamaProvider
from app.matching.job_requirements import RequirementExtractor
from app.matching.knockouts import KnockoutResult
from app.matching.scoring import MatchLevel, ScoreResult
from app.matching.skill_taxonomy import SkillTaxonomy
from app.models import Candidate, Job, JobMatch
from app.repositories.matching import MatchRepository
from app.schemas.matching import MatchAnalysis
from app.services.job_analysis import JobAnalysisService
from app.services.llm_cache import LLMCacheService
from app.services.scoring import load_score_calculator
from app.services.skill_taxonomy import get_default_skill_taxonomy
from scripts.evaluate_matching import (
    DEFAULT_DATASET,
    DEFAULT_REPORT,
    LLM_REPORT_MARKER,
    ROOT,
    ExtractionCount,
    GoldenCase,
    GoldenSet,
    evaluate,
    extraction_counts,
    render_report,
    skill_key,
)

Claim = tuple[str, Literal["presente", "ausente"]]
DEFAULT_MAX_TOKENS = 640


@dataclass(frozen=True)
class CaseResult:
    case: GoldenCase
    score: Decimal | None
    baseline: Counter[ExtractionCount]
    augmented: Counter[ExtractionCount]
    status: str
    calls: int
    tokens: int | None
    cost: Decimal | None
    baseline_ms: float
    provider_ms: int
    elapsed_ms: float


@dataclass(frozen=True)
class Funnel:
    threshold: Decimal
    top_n: int
    selected: tuple[CaseResult, ...]

    @property
    def high(self) -> int:
        return sum(row.case.compatibility == "high" for row in self.selected)


class MeasuredProvider:
    """Mede as chamadas do serviço, inclusive tentativas que retornam erro."""

    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider
        self.calls: list[tuple[int, int | None]] = []

    @property
    def name(self) -> str:
        return self._provider.name

    @property
    def model(self) -> str:
        return self._provider.model

    def complete(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        started = perf_counter()
        tokens = None
        try:
            result = self._provider.complete(
                system_prompt=system_prompt, user_prompt=user_prompt
            )
            if result.tokens_in is not None and result.tokens_out is not None:
                tokens = result.tokens_in + result.tokens_out
            return result
        finally:
            self.calls.append((int((perf_counter() - started) * 1000), tokens))


def reference_claims(
    case: GoldenCase, golden: GoldenSet, taxonomy: SkillTaxonomy
) -> set[Claim]:
    """Combina os rótulos manuais com os fatos explícitos do perfil sintético."""
    required = {skill_key(name, taxonomy) for name in (*case.required, *case.preferred)}
    present = {skill_key(name, taxonomy) for name in golden.candidate_skills}
    absent = {skill_key(name, taxonomy) for name in golden.confirmed_absent} - present
    return {(name, "presente") for name in required & present} | {
        (name, "ausente") for name in required & absent
    }


def baseline_claims(result: ScoreResult, taxonomy: SkillTaxonomy) -> set[Claim]:
    """Conta presença exata ou por alias e ausências explícitas como afirmações."""
    return {
        (skill_key(item.requirement.skill.canonical_name, taxonomy), "presente")
        for item in result.met
        if item.level in {MatchLevel.EXACT, MatchLevel.ALIAS}
    } | {
        (skill_key(item.requirement.skill.canonical_name, taxonomy), "ausente")
        for item in result.absent
    }


def _llm_claims(output: JobAnalysisOutput, taxonomy: SkillTaxonomy) -> set[Claim]:
    return {
        (skill_key(name, taxonomy), "presente") for name in output.matched_skills
    } | {(skill_key(name, taxonomy), "ausente") for name in output.missing_skills}


def compare_funnels(rows: Sequence[CaseResult]) -> list[Funnel]:
    """Simula uma grade fixa de limiares e limites sem consultar os rótulos na seleção."""
    ranked = sorted(
        (row for row in rows if row.score is not None),
        key=lambda row: (-(row.score or Decimal(0)), row.case.id),
    )
    return [
        Funnel(
            threshold,
            top_n,
            tuple(row for row in ranked if (row.score or Decimal(0)) >= threshold)[
                :top_n
            ],
        )
        for threshold in map(Decimal, ("0.50", "0.60", "0.70", "0.80"))
        for top_n in (3, 5, 10)
    ]


def choose_funnel(options: Sequence[Funnel]) -> Funnel:
    """Retém mais casos de alta compatibilidade e desempata pelo menor volume."""
    return max(
        options,
        key=lambda option: (
            option.high,
            -len(option.selected),
            option.threshold,
            -option.top_n,
        ),
    )


@contextmanager
def local_database() -> Iterator[sessionmaker[Session]]:
    """Usa uma base nova para medir as chamadas com cache vazio e persistência real."""
    base = make_url(settings.database_url)
    if base.host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("A avaliação requer um PostgreSQL local.")
    db_name = f"jobpilot_eval_{uuid4().hex}_test"
    target = base.set(database=db_name)
    admin = create_engine(base.set(database="postgres"), isolation_level="AUTOCOMMIT")
    engine = create_engine(target, hide_parameters=True)
    try:
        with admin.connect() as connection:
            connection.exec_driver_sql(f'CREATE DATABASE "{db_name}"')
        try:
            config = Config(str(ROOT / "alembic.ini"))
            url = target.render_as_string(hide_password=False).replace("%", "%%")
            config.set_main_option("sqlalchemy.url", url)
            command.upgrade(config, "head")
            yield sessionmaker(bind=engine, autoflush=False)
        finally:
            engine.dispose()
            with admin.connect() as connection:
                connection.exec_driver_sql(f'DROP DATABASE "{db_name}"')
    finally:
        admin.dispose()


def _insert_match(
    db: Session,
    candidate_id: UUID,
    golden: GoldenSet,
    case: GoldenCase,
    scored: ScoreResult,
) -> tuple[UUID, UUID]:
    job_id = uuid5(NAMESPACE_URL, f"jobpilot:{golden.source_revision}:{case.id}")
    url = f"https://example.invalid/golden/{case.id}"
    job = Job(
        id=job_id,
        title=case.role,
        company="Golden set",
        source="manual",
        url=url,
        canonical_url=url,
        fingerprint=case.id,
        description=case.description,
    )
    db.add(job)
    db.flush()
    match = JobMatch(
        candidate_id=candidate_id,
        job_id=job_id,
        scoring_version=scored.scoring_version,
        deterministic_score=scored.score,
        match_score=scored.score,
        analysis=MatchAnalysis.from_score(scored).model_dump(mode="json"),
        knockout_flags=[],
    )
    db.add(match)
    db.flush()
    return job_id, match.id


def evaluate_llm(
    golden: GoldenSet,
    sessions: sessionmaker[Session],
    provider: LLMProvider,
    *,
    progress: bool = False,
) -> list[CaseResult]:
    """Exercita o serviço integrado. Em falha do LLM, mantém as afirmações da base."""
    taxonomy = get_default_skill_taxonomy()
    extractor = RequirementExtractor(taxonomy)
    calculator = load_score_calculator()
    monitored = MeasuredProvider(provider)
    cache = LLMCacheService(monitored, sessions=sessions)
    with sessions.begin() as db:
        candidate = Candidate(
            name="Perfil sintético", resume_text="Perfil do golden set."
        )
        db.add(candidate)
        db.flush()
        candidate_id = candidate.id

    results: list[CaseResult] = []
    for case in golden.cases:
        start = perf_counter()
        scored = calculator.score(
            extractor.extract(case.description),
            golden.candidate_skills,
            knockouts=KnockoutResult(),
            confirmed_absent=golden.confirmed_absent,
        )
        baseline_ms = (perf_counter() - start) * 1000
        expected = reference_claims(case, golden, taxonomy)
        baseline = baseline_claims(scored, taxonomy)
        with sessions.begin() as db:
            job_id, match_id = _insert_match(db, candidate_id, golden, case, scored)

        augmented = baseline
        monitored.calls.clear()
        with sessions() as db:
            service = JobAnalysisService(MatchRepository(db), cache)
            start = perf_counter()
            try:
                result = service.analyze(candidate_id, job_id, scored.scoring_version)
                status = "reparo" if "+" in result.prompt_version else "válida"
                augmented = _llm_claims(result.analysis, taxonomy)
            except JobAnalysisOutputError:
                status = "saída inválida"
            except LLMProviderError:
                status = "falha do provedor"
            elapsed_ms = (perf_counter() - start) * 1000
            stored = db.get(JobMatch, match_id)
            if stored is None or stored.deterministic_score != scored.score:
                raise RuntimeError(f"Score determinístico divergente em {case.id}.")
            if stored.match_score != scored.score:
                raise RuntimeError(f"Score do ranking divergente em {case.id}.")

        counts = [tokens for _, tokens in monitored.calls if tokens is not None]
        local_cost = Decimal(0) if provider.name in {"fake", "ollama"} else None
        results.append(
            CaseResult(
                case,
                scored.score,
                extraction_counts(expected, baseline),
                extraction_counts(expected, augmented),
                status,
                len(monitored.calls),
                sum(counts) if len(counts) == len(monitored.calls) else None,
                local_cost,
                baseline_ms,
                sum(latency for latency, _ in monitored.calls),
                elapsed_ms,
            )
        )
        if progress:
            sys.stderr.write(
                f"{case.id} concluída ({len(results)}/{len(golden.cases)}).\n"
            )
            sys.stderr.flush()
    return results


def _accuracy(label: str, rows: Sequence[Counter[ExtractionCount]]) -> str:
    totals: Counter[ExtractionCount] = Counter()
    for counts in rows:
        totals.update(counts)
    tp, fp, fn = (totals[key] for key in ExtractionCount)
    precision = f"{tp / (tp + fp):.2%}" if tp + fp else "—"
    recall = f"{tp / (tp + fn):.2%}" if tp + fn else "—"
    return f"| {label} | {tp} | {fp} | {fn} | {precision} | {recall} |".replace(
        ".", ","
    )


def render_comparison(
    rows: Sequence[CaseResult],
    *,
    model: str,
    digest: str,
    version: str,
    max_tokens: int,
) -> str:
    """Publica medidas operacionais e a decisão do funil sem inserir conteúdo do LLM."""
    options = compare_funnels(rows)
    selected = choose_funnel(options)
    coverage = Counter(row.status for row in rows)
    total_cost = sum(
        (row.cost for row in rows if row.cost is not None), start=Decimal(0)
    )
    costs_missing = sum(row.cost is None for row in rows)
    lines = [
        "\n## Avaliação com LLM",
        "",
        (
            f"Ollama `{version}`, modelo `{model}`, digest `{digest}`. "
            f"Perfil sintético, {len(rows)} vagas, banco novo, cache inicialmente vazio e "
            f"limite de {max_tokens} tokens por resposta. Instruções `job-analysis-v2` "
            "e reparo `job-analysis-repair-v1`."
        ),
        "",
        (
            "A comparação usa afirmações de presença ou ausência por habilidade, "
            "com referência nos rótulos manuais e nos fatos do perfil. "
            "Relações aproximadas entram como sem confirmação. Em falha do LLM, "
            "a variante mantém as afirmações determinísticas."
        ),
        "",
        "| Variante | VP | FP | FN | Precisão | Revocação |",
        "|---|---:|---:|---:|---:|---:|",
        _accuracy("Determinístico", [row.baseline for row in rows]),
        _accuracy("Determinístico + LLM", [row.augmented for row in rows]),
        "",
        (
            f"A primeira tentativa foi válida em {coverage['válida']} vagas, e o reparo "
            f"produziu saída válida em {coverage['reparo']}. Houve {coverage['saída inválida']} "
            f"saídas inválidas e {coverage['falha do provedor']} falhas do provedor. "
            "O score e a ordem do ranking foram preservados."
        ),
        "",
        (
            f"Mediana determinística de {median(row.baseline_ms for row in rows):.3f} ms "
            f"e mediana do serviço LLM de {median(row.elapsed_ms for row in rows):.1f} ms. "
            f"Foram {sum(row.calls for row in rows)} chamadas, com custo conhecido "
            f"de USD {total_cost} e {costs_missing} vagas com custo indisponível."
        ),
        "",
        "| Vaga | Score | Análise | VP base → +LLM | Chamadas | Tokens | USD | Provedor (ms) | Serviço (ms) |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        score = f"{row.score:.4f}" if row.score is not None else "—"
        tokens = row.tokens if row.tokens is not None else "—"
        cost = row.cost if row.cost is not None else "—"
        correct = (
            f"{row.baseline[ExtractionCount.TP]} → {row.augmented[ExtractionCount.TP]}"
        )
        lines.append(
            f"| {row.case.id} | {score} | {row.status} | {correct} | {row.calls} | {tokens} | "
            f"{cost} | {row.provider_ms} | {row.elapsed_ms:.1f} |"
        )
    lines.extend(
        [
            "",
            "### Funil de custo",
            "",
            (
                "A grade aplica o limiar de score e quebra empates pelo identificador da vaga. "
                "A escolha maximiza a retenção das vagas de alta compatibilidade e prefere "
                "menos consultas, limiar maior e top-N menor em caso de empate."
            ),
            "",
            "| Limiar inclusivo | Top-N | Vagas selecionadas | Compatibilidade alta |",
            "|---:|---:|---:|---:|",
            *(
                f"| {item.threshold} | {item.top_n} | {len(item.selected)} | {item.high} |"
                for item in options
            ),
            "",
            (
                f"Funil do modo local sob demanda. Score **≥ {selected.threshold}** e "
                f"**top-{selected.top_n}**, com {len(selected.selected)} vagas selecionadas "
                f"e {selected.high} rotuladas como alta. O teto é de {2 * selected.top_n} "
                "chamadas lógicas por execução, incluindo reparos. O matching "
                "determinístico segue como referência para a decisão."
            ),
            "",
            (
                "A medição reflete uma execução local com um modelo e um perfil. "
                "A latência varia com a máquina, e o custo em USD refere-se à tarifa "
                "por chamada do provedor."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _ollama_metadata(port: int, model: str) -> tuple[str, str]:
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
    results = []
    try:
        for endpoint in ("/api/version", "/api/tags"):
            connection.request("GET", endpoint)
            response = connection.getresponse()
            if response.status != 200:
                raise RuntimeError(
                    "O Ollama local não respondeu à consulta de configuração."
                )
            results.append(json.loads(response.read()))
    finally:
        connection.close()
    version, tags = results
    for item in tags["models"]:
        if item["name"] == model:
            return version["version"], item["digest"]
    raise ValueError("O modelo informado precisa estar instalado no Ollama local.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-local", action="store_true", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--port", type=int, default=11434)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    version, digest = _ollama_metadata(args.port, args.model)
    golden = GoldenSet.model_validate_json(DEFAULT_DATASET.read_bytes())
    baseline = render_report(evaluate(golden))
    provider = OllamaProvider(args.model, args.port, 60, DEFAULT_MAX_TOKENS, 0)
    with local_database() as sessions:
        rows = evaluate_llm(golden, sessions, provider, progress=True)
    report = render_comparison(
        rows,
        model=args.model,
        digest=digest,
        version=version,
        max_tokens=DEFAULT_MAX_TOKENS,
    )
    args.output.write_text(
        baseline + LLM_REPORT_MARKER + report, encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
