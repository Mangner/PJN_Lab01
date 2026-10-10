"""Czyszczenie pól z listy i ze strony produktu (ocena, gwarancja, waga, wymiary...).

Każda funkcja przyjmuje surowy tekst i zwraca liczbę albo None. Format spoza
znanych wzorców (np. inna jednostka) też daje None, nigdy wyjątek.
"""

from __future__ import annotations

import re

from bajtoparser.parsing.braki import normalizuj
from bajtoparser.parsing.ceny import czysc_cene

LICZBA = r"(\d+(?:[.,]\d+)?)"


def _dopasuj(surowa: str | None, wzorzec: str) -> tuple[str, ...] | None:
    """Zwraca grupy dopasowania wzorca do całego (znormalizowanego) tekstu albo None."""
    tekst = normalizuj(surowa)
    if tekst is None:
        return None
    dopasowanie = re.fullmatch(wzorzec, tekst, flags=re.IGNORECASE)
    return dopasowanie.groups() if dopasowanie else None


def _float(tekst: str) -> float:
    return float(tekst.replace(",", "."))


def czysc_ocene(surowa: str | None) -> float | None:
    """Ocena `4,1` -> 4.1."""
    grupy = _dopasuj(surowa, LICZBA)
    return _float(grupy[0]) if grupy else None


def czysc_liczbe_opinii(surowa: str | None) -> int | None:
    """Liczba opinii `25` -> 25."""
    grupy = _dopasuj(surowa, r"(\d+)")
    return int(grupy[0]) if grupy else None


def czysc_gwarancje(surowa: str | None) -> int | None:
    """Gwarancja `24 mies.` -> 24 (miesiące)."""
    grupy = _dopasuj(surowa, r"(\d+)\s*mies\.?")
    return int(grupy[0]) if grupy else None


def czysc_wage(surowa: str | None) -> float | None:
    """Waga `1,47 kg` -> 1.47 (kg). Inne jednostki dają None."""
    grupy = _dopasuj(surowa, LICZBA + r"\s*kg")
    return _float(grupy[0]) if grupy else None


def czysc_wymiary(surowa: str | None) -> tuple[float, float, float] | None:
    """Wymiary `17 x 9 x 8 cm` -> (17.0, 9.0, 8.0) w centymetrach."""
    grupy = _dopasuj(surowa, rf"{LICZBA}\s*x\s*{LICZBA}\s*x\s*{LICZBA}\s*cm")
    if not grupy:
        return None
    dlugosc, szerokosc, wysokosc = (_float(g) for g in grupy)
    return dlugosc, szerokosc, wysokosc


def czysc_stan_magazynowy(surowa: str | None) -> int | None:
    """Stan magazynowy `158 szt.` -> 158."""
    grupy = _dopasuj(surowa, r"(\d+)\s*szt\.?")
    return int(grupy[0]) if grupy else None


def czysc_czas_dostawy(surowa: str | None) -> int | None:
    """Czas dostawy `8 dni roboczych` -> 8 (dni)."""
    grupy = _dopasuj(surowa, r"(\d+)\s+dni(?:\s+roboczych)?")
    return int(grupy[0]) if grupy else None


def czysc_zwrot(surowa: str | None) -> int | None:
    """Zwrot `30 dni na zwrot` -> 30 (dni)."""
    grupy = _dopasuj(surowa, r"(\d+)\s+dni\s+na\s+zwrot")
    return int(grupy[0]) if grupy else None


def czysc_koszt_dostawy(surowa: str | None) -> tuple[float | None, str | None]:
    """Koszt dostawy `14,99 zł` -> (14.99, "PLN"); `gratis` -> (0.0, None)."""
    tekst = normalizuj(surowa)
    if tekst is not None and tekst.casefold() == "gratis":
        return 0.0, None
    return czysc_cene(tekst)
