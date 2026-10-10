"""Deduplikacja rekordów po id (zostaje pierwsze wystąpienie)."""

from __future__ import annotations

from typing import Any


def deduplikuj(
    rekordy: list[dict[str, Any]], klucz: str = "id"
) -> tuple[list[dict[str, Any]], int]:
    """Zwraca (unikalne rekordy w kolejności wejścia, liczba usuniętych duplikatów).

    Rekord bez wartości klucza (brak lub pusty) nie da się porównać, więc zostaje.
    Lista wejściowa nie jest modyfikowana.
    """
    widziane: set[Any] = set()
    unikalne: list[dict[str, Any]] = []
    for rekord in rekordy:
        wartosc = rekord.get(klucz)
        if wartosc in (None, ""):
            unikalne.append(rekord)
            continue
        if wartosc in widziane:
            continue
        widziane.add(wartosc)
        unikalne.append(rekord)
    return unikalne, len(rekordy) - len(unikalne)
