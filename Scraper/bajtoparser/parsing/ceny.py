"""Czyszczenie cen: tekst z symbolem waluty na (liczba float, kod waluty)."""

from __future__ import annotations

import re

from bajtoparser.parsing.braki import normalizuj

SYMBOLE_WALUT = {"zł": "PLN", "€": "EUR", "$": "USD"}


def _wykryj_walute(tekst: str, waluta: str | None) -> str | None:
    """Waluta po symbolu w tekście; gdy go brak, po kodzie z atrybutu `data-waluta`."""
    for symbol, kod in SYMBOLE_WALUT.items():
        if symbol in tekst:
            return kod
    return waluta.strip().upper() if waluta and waluta.strip() else None


def _na_liczbe(cyfry: str, waluta: str | None) -> float | None:
    """Zamienia ciąg cyfr z separatorami na liczbę, rozstrzygając separator po walucie.

    USD: przecinek to separator tysięcy, kropka dziesiętny (`$1,299.00`).
    PLN/EUR i brak waluty: przecinek dziesiętny, kropka lub spacja to tysiące (`1 299,00`).
    """
    if waluta == "USD":
        cyfry = cyfry.replace(",", "")
    elif "," in cyfry:
        cyfry = cyfry.replace(".", "").replace(",", ".")
    elif cyfry.count(".") > 1:
        cyfry = cyfry.replace(".", "")
    try:
        return float(cyfry)
    except ValueError:
        return None


def czysc_cene(surowa: str | None, waluta: str | None = None) -> tuple[float | None, str | None]:
    """Zwraca (cena, waluta) z surowego tekstu ceny; brak danych to (None, None).

    Waluta jest wykrywana po symbolu (`zł`, `€`, `$`), a dopiero potem po argumencie
    `waluta` (atrybut `data-waluta`). Waluty nie są przeliczane.
    """
    tekst = normalizuj(surowa)
    if tekst is None:
        return None, None
    kod = _wykryj_walute(tekst, waluta)
    cyfry = re.sub(r"[^\d.,]", "", tekst)
    if not re.search(r"\d", cyfry):
        return None, None
    wartosc = _na_liczbe(cyfry, kod)
    if wartosc is None:
        return None, None
    return wartosc, kod
