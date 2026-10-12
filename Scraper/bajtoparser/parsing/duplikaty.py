"""Deduplikacja rekordów po id (zostaje pierwsze wystąpienie)."""

from __future__ import annotations

from collections.abc import Callable
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


def rozne_duplikaty(
    rekordy: list[dict[str, Any]],
    klucz: str = "id",
    porownywane: Callable[[dict[str, Any]], Any] | None = None,
) -> list[Any]:
    """Zwraca wartości klucza duplikatów, które różnią się od pierwszego wystąpienia.

    `porownywane` sprowadza rekord do postaci porównywanej (np. oczyszczone pola listy),
    żeby różnice samego zapisu (pusta komórka `""` w tabeli vs brak elementu w karcie)
    nie liczyły się jako różnica. Każde id występuje w wyniku najwyżej raz.
    """
    postac = porownywane or (lambda rekord: rekord)
    pierwsze: dict[Any, Any] = {}
    rozne: list[Any] = []
    for rekord in rekordy:
        wartosc = rekord.get(klucz)
        if wartosc in (None, ""):
            continue
        if wartosc not in pierwsze:
            pierwsze[wartosc] = postac(rekord)
        elif postac(rekord) != pierwsze[wartosc] and wartosc not in rozne:
            rozne.append(wartosc)
    return rozne
