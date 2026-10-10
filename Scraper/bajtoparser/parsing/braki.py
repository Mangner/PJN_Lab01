"""Obsługa braków danych: `—`, pusty tekst i same białe znaki to None."""

from __future__ import annotations

NBSP = "\u00a0"
MYSLNIK_BRAKU = "—"


def normalizuj(surowa: str | None) -> str | None:
    """Zwraca tekst bez białych znaków na brzegach (twarda spacja -> zwykła) albo None.

    Brak danych (None, pusty tekst, same spacje, samotne `—`) nigdy nie rzuca wyjątku.
    """
    if surowa is None:
        return None
    tekst = surowa.replace(NBSP, " ").strip()
    if not tekst or tekst == MYSLNIK_BRAKU:
        return None
    return tekst
