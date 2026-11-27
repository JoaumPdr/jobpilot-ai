"""Repositório de lotes de importação.

POR QUÊ: o lote é criado (e recebe `id` via flush) antes das vagas, para que
cada vaga já nasça ligada ao seu `import_batch_id`. O `commit` fica no serviço,
que fecha a transação só depois de processar todas as linhas.
"""

from __future__ import annotations

from app.models import ImportBatch
from app.repositories.base import BaseRepository


class ImportBatchRepository(BaseRepository):
    """Escritas de `import_batches`."""

    def add(self, batch: ImportBatch) -> ImportBatch:
        """Adiciona o lote à sessão."""
        self._db.add(batch)
        return batch

    def flush(self) -> None:
        """Envia o INSERT pendente para o banco e obtém o `id`/defaults."""
        self._db.flush()
