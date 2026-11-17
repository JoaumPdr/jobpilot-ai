"""Utilidades compartilhadas entre os schemas Pydantic do perfil."""

from __future__ import annotations

# Limite defensivo para itens de listas livres (títulos, locais, aliases).
MAX_LIST_ITEM_LENGTH = 200


def clean_string_list(value: list[str]) -> list[str]:
    """Remove espaços nas pontas e descarta itens vazios.

    POR QUÊ: listas chegam de UI/CSV; sem normalização, `[" Remoto ", ""]`
    viraria dois valores distintos no JSONB e quebraria filtros futuros.
    """
    cleaned: list[str] = []
    for item in value:
        text = item.strip()
        if not text:
            continue
        if len(text) > MAX_LIST_ITEM_LENGTH:
            raise ValueError(f"Item de lista excede {MAX_LIST_ITEM_LENGTH} caracteres.")
        cleaned.append(text)
    return cleaned
