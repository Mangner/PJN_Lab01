"""Czyszczenie dat: `DD.MM.RRRR` na ISO `RRRR-MM-DD`."""

from __future__ import annotations

import re
from datetime import date

from bajtoparser.parsing.braki import normalizuj

WZORZEC_DATY = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")


def czysc_date(surowa: str | None) -> str | None:
    """Zwraca datę ISO albo None dla braku danych i dat niepoprawnych (np. 31.02.2026)."""
    tekst = normalizuj(surowa)
    if tekst is None:
        return None
    dopasowanie = WZORZEC_DATY.fullmatch(tekst)
    if dopasowanie is None:
        return None
    dzien, miesiac, rok = (int(czesc) for czesc in dopasowanie.groups())
    try:
        return date(rok, miesiac, dzien).isoformat()
    except ValueError:
        return None
