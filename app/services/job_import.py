"""Importação de vagas por CSV com relatório por linha.

POR QUÊ: importar em lote não pode ser tudo-ou-nada. Uma linha com URL quebrada
ou salário inválido precisa ser **rejeitada com motivo e número da linha**, sem
derrubar as demais. O lote (`import_batches`) guarda os contadores e os erros, e
um único `commit` no fim mantém a importação rápida e atômica.

A deduplicação do lote usa só as camadas certas (identificador externo e URL
canônica): são elas que garantem "reimportar o mesmo arquivo = 0 inserções".
O fingerprint (camada 3, provável) continua sendo revisado na F1-T07.
"""

from __future__ import annotations

import csv
import io
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Protocol

from pydantic import ValidationError

from app.core.errors import ConflictError, InvalidDataError
from app.models import ImportBatch, ImportKind
from app.schemas.imports import ImportRowError
from app.schemas.jobs import JobCreate
from app.services.jobs import JobService
from app.services.normalization import canonicalize_url

# 5 MB cabem ~5 mil linhas com descrições curtas, com folga.
MAX_CSV_BYTES = 5 * 1024 * 1024

# O PLANO.md §6.1 exige as três primeiras; `url` entra porque é NOT NULL no
# modelo e é a base da dedup (desvio documentado em `docs/import-csv.md`).
REQUIRED_COLUMNS = ("title", "company", "description", "url")

# Colunas opcionais aceitas; qualquer outra é ignorada (planilhas costumam ter
# colunas extras que não usamos).
OPTIONAL_COLUMNS = (
    "location",
    "work_mode",
    "seniority",
    "employment_type",
    "salary_min",
    "salary_max",
    "currency",
    "source",
    "external_id",
    "posted_at",
)

_ROW_FIELD_LABELS = {
    "title": "title",
    "company": "company",
    "description": "description",
    "url": "url",
}


class RowFieldError(ValueError):
    """Erro de conversão de um campo da linha, com o nome do campo."""

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field


class ImportBatchRepositoryProtocol(Protocol):
    """Contrato mínimo do repositório de lotes."""

    def add(self, batch: ImportBatch) -> ImportBatch: ...

    def flush(self) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


class JobLookupProtocol(Protocol):
    """Contrato mínimo para pré-carregar as chaves de dedup em bloco."""

    def find_existing_canonical_urls(self, urls: Sequence[str]) -> set[str]: ...

    def find_existing_external_ids(
        self, keys: Sequence[tuple[str, str]]
    ) -> set[tuple[str, str]]: ...


class JobImportService:
    """Orquestra a importação CSV de vagas."""

    # Tamanho do bloco de chaves enviado ao banco por consulta.
    PREFETCH_CHUNK = 500

    def __init__(
        self,
        jobs: JobService,
        jobs_repository: JobLookupProtocol,
        batches: ImportBatchRepositoryProtocol,
    ) -> None:
        self._jobs = jobs
        self._lookup = jobs_repository
        self._batches = batches

    def import_csv(
        self,
        *,
        filename: str | None,
        content: bytes,
        source: str | None = None,
    ) -> ImportBatch:
        """Processa o CSV e devolve o lote com contadores e erros por linha.

        Levanta `InvalidDataError` (422) quando o problema é do arquivo inteiro
        (tamanho, codificação, cabeçalho) — nesse caso nenhum lote é criado.
        """
        text = self._decode(content)
        reader = csv.DictReader(io.StringIO(text))
        self._normalize_header(reader)

        batch_source = (source or "").strip() or "csv"
        batch = ImportBatch(
            source=batch_source,
            kind=ImportKind.CSV.value,
            filename=filename,
        )
        self._batches.add(batch)
        # O `id` e o `started_at` (default do banco) precisam existir antes de
        # ligar cada vaga ao lote.
        self._batches.flush()

        errors: list[ImportRowError] = []
        total = 0
        # Linhas válidas ficam em memória para a checagem de dedup em bloco.
        pending: list[tuple[int, JobCreate]] = []

        for row in reader:
            total += 1
            line = reader.line_num
            values = {
                key: value.strip() if isinstance(value, str) else value
                for key, value in row.items()
                if key
            }
            row_source = values.get("source") or batch_source

            missing = [field for field in REQUIRED_COLUMNS if not values.get(field)]
            if missing:
                for field in missing:
                    errors.append(
                        ImportRowError(
                            row=line,
                            field=_ROW_FIELD_LABELS[field],
                            message=f"Coluna obrigatória vazia: {field}.",
                        )
                    )
                continue

            try:
                payload = self._build_payload(values, row_source)
                data = JobCreate(**payload)
            except ValidationError as exc:
                for error in exc.errors():
                    location = ".".join(str(part) for part in error.get("loc", ()))
                    message = str(error.get("msg", "Valor inválido."))
                    # O Pydantic prefixa mensagens de validador com "Value error, ".
                    message = message.removeprefix("Value error, ")
                    errors.append(
                        ImportRowError(
                            row=line,
                            field=location or "row",
                            message=message,
                        )
                    )
                continue
            except ValueError as exc:
                field = getattr(exc, "field", "row")
                errors.append(ImportRowError(row=line, field=field, message=str(exc)))
                continue

            pending.append((line, data))

        rejected = total - len(pending)
        existing_urls, existing_external_ids = self._prefetch(pending)

        inserted = duplicates = 0
        # Chaves já vistas **neste lote**: a linha seguinte precisa enxergar a
        # anterior sem um flush individual por linha.
        seen_urls: set[str] = set()
        seen_external_ids: set[tuple[str, str]] = set()

        for line, data in pending:
            canonical_url = canonicalize_url(data.url)
            external_key = (data.source, data.external_id) if data.external_id else None
            duplicated = canonical_url in existing_urls or canonical_url in seen_urls
            if external_key is not None:
                duplicated = duplicated or (
                    external_key in existing_external_ids
                    or external_key in seen_external_ids
                )
            if duplicated:
                duplicates += 1
                continue

            try:
                self._jobs.prepare_job(
                    data,
                    import_batch_id=batch.id,
                    include_probable=False,
                    # As camadas 1 e 2 já foram checadas no bloco acima.
                    check_exact=False,
                )
            except ConflictError:
                duplicates += 1
                continue
            except ValueError as exc:
                # Normalização de URL/defesa extra: rejeita só a linha.
                field = getattr(exc, "field", "row")
                errors.append(ImportRowError(row=line, field=field, message=str(exc)))
                rejected += 1
                continue

            if external_key is not None:
                seen_external_ids.add(external_key)
            seen_urls.add(canonical_url)
            inserted += 1

        batch.total_rows = total
        batch.inserted = inserted
        batch.duplicates = duplicates
        batch.rejected = rejected
        batch.errors = [error.model_dump() for error in errors]
        batch.finished_at = datetime.now(UTC)
        self._batches.commit()
        return batch

    def _prefetch(
        self, pending: list[tuple[int, JobCreate]]
    ) -> tuple[set[str], set[tuple[str, str]]]:
        """Carrega em bloco as chaves de dedup já existentes no banco.

        POR QUÊ: uma consulta por linha custaria ~10 mil idas ao banco em 5 mil
        linhas. Em blocos de `PREFETCH_CHUNK`, são ~20 consultas no total.
        """
        urls = list({canonicalize_url(data.url) for _, data in pending})
        keys = list(
            {
                (data.source, data.external_id)
                for _, data in pending
                if data.external_id is not None
            }
        )

        existing_urls: set[str] = set()
        for start in range(0, len(urls), self.PREFETCH_CHUNK):
            existing_urls |= self._lookup.find_existing_canonical_urls(
                urls[start : start + self.PREFETCH_CHUNK]
            )

        existing_keys: set[tuple[str, str]] = set()
        for start in range(0, len(keys), self.PREFETCH_CHUNK):
            existing_keys |= self._lookup.find_existing_external_ids(
                keys[start : start + self.PREFETCH_CHUNK]
            )

        return existing_urls, existing_keys

    # ------------------------------------------------------------------
    # Arquivo
    # ------------------------------------------------------------------

    def _decode(self, content: bytes) -> str:
        """Valida tamanho e codificação do arquivo inteiro."""
        if len(content) > MAX_CSV_BYTES:
            limit_mb = MAX_CSV_BYTES // (1024 * 1024)
            raise InvalidDataError(
                f"Arquivo excede o limite de {limit_mb} MB.",
                details=[
                    {
                        "field": "file",
                        "message": f"Envie um CSV de até {limit_mb} MB.",
                    }
                ],
            )
        try:
            # `utf-8-sig` aceita arquivos com e sem BOM (Excel costuma incluir).
            return content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise InvalidDataError(
                "Arquivo CSV deve estar em UTF-8.",
                details=[
                    {
                        "field": "file",
                        "message": "Converta o arquivo para UTF-8 e tente novamente.",
                    }
                ],
            ) from exc

    def _normalize_header(self, reader: csv.DictReader) -> None:
        """Padroniza os nomes das colunas e exige as obrigatórias."""
        raw = reader.fieldnames or []
        normalized = [name.strip().lower() for name in raw]
        if not normalized:
            raise InvalidDataError(
                "CSV sem cabeçalho.",
                details=[
                    {
                        "field": "file",
                        "message": "A primeira linha deve conter os nomes das colunas.",
                    }
                ],
            )
        # Reatribuir antes de iterar faz as linhas já virem com chaves normalizadas.
        reader.fieldnames = normalized

        missing = [column for column in REQUIRED_COLUMNS if column not in normalized]
        if missing:
            raise InvalidDataError(
                "Cabeçalho do CSV incompleto.",
                details=[
                    {
                        "field": "file",
                        "message": (
                            "Colunas obrigatórias ausentes: " + ", ".join(missing) + "."
                        ),
                    }
                ],
            )

    # ------------------------------------------------------------------
    # Linha
    # ------------------------------------------------------------------

    def _build_payload(self, values: dict[str, str], source: str) -> dict[str, object]:
        """Converte a linha em payload do `JobCreate`, com mensagens claras."""
        return {
            "title": values["title"],
            "company": values["company"],
            "description": values["description"],
            "url": values["url"],
            "location": values.get("location") or None,
            "work_mode": values.get("work_mode") or None,
            "seniority": values.get("seniority") or None,
            "employment_type": values.get("employment_type") or None,
            "salary_min": self._parse_decimal(values.get("salary_min"), "salary_min"),
            "salary_max": self._parse_decimal(values.get("salary_max"), "salary_max"),
            "currency": values.get("currency") or None,
            "source": source,
            "external_id": values.get("external_id") or None,
            "posted_at": self._parse_datetime(values.get("posted_at")),
        }

    def _parse_decimal(self, value: str | None, field: str) -> Decimal | None:
        """Converte salário para `Decimal`; vazio vira `None`."""
        if not value:
            return None
        try:
            return Decimal(value)
        except InvalidOperation as exc:
            raise RowFieldError(
                field,
                f"{field} inválido: {value!r}. Use ponto decimal (ex.: 12000.00).",
            ) from exc

    def _parse_datetime(self, value: str | None) -> datetime | None:
        """Converte `posted_at` ISO 8601; vazio vira `None`."""
        if not value:
            return None
        raw = value[:-1] + "+00:00" if value.endswith("Z") else value
        try:
            return datetime.fromisoformat(raw)
        except ValueError as exc:
            raise RowFieldError(
                "posted_at",
                f"posted_at inválido: {value!r}. "
                "Use ISO 8601 (ex.: 2026-11-10T12:00:00Z).",
            ) from exc
