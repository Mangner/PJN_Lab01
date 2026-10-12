"""Czyszczenie całego rekordu: scalony rekord listy i szczegółów na wiersz wyjściowy.

Kolejność kolumn jest zdefiniowana tylko tutaj (`KOLUMNY`). Poza wartościami zwracana jest
lista pól „nierozpoznanych”: surowa wartość nie była brakiem (`—`, pusta), a mimo to
czyszczenie dało `None`. Chroni to przed cichym maskowaniem błędu parsera jako braku danych.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from bajtoparser.parsing.braki import normalizuj
from bajtoparser.parsing.ceny import czysc_cene
from bajtoparser.parsing.daty import czysc_date
from bajtoparser.parsing.pola import (
    czysc_czas_dostawy,
    czysc_gwarancje,
    czysc_koszt_dostawy,
    czysc_liczbe_opinii,
    czysc_ocene,
    czysc_stan_magazynowy,
    czysc_wage,
    czysc_wymiary,
    czysc_zwrot,
)

KOLUMNY: list[str] = [
    "id",
    "nazwa",
    "url",
    "kategoria",
    "producent",
    "cena",
    "waluta",
    "cena_poprzednia",
    "dostepnosc",
    "gwarancja_mies",
    "ocena",
    "liczba_opinii",
    "data_dodania",
    "opis",
    "ean",
    "kod_producenta",
    "kolor",
    "material",
    "waga_kg",
    "dlugosc_cm",
    "szerokosc_cm",
    "wysokosc_cm",
    "kraj_pochodzenia",
    "sprzedawca",
    "stan_magazynowy_szt",
    "czas_dostawy_dni",
    "koszt_dostawy",
    "waluta_dostawy",
    "zwrot_dni",
    "zrodlo",
]
"""Stała kolejność kolumn wyjściowych (jedyne miejsce, w którym jest zdefiniowana)."""

KOLUMNY_LISTY: list[str] = KOLUMNY[: KOLUMNY.index("data_dodania") + 1]
"""Kolumny pochodzące z listy (bez `zrodlo`): podstawa porównania duplikatów."""

POLA_SZCZEGOLOW: tuple[str, ...] = (
    "opis",
    "ean",
    "kod_producenta",
    "kolor",
    "material",
    "waga",
    "wymiary",
    "kraj_pochodzenia",
    "sprzedawca",
    "stan_magazynowy",
    "czas_dostawy",
    "koszt_dostawy",
    "zwrot",
)
"""Surowe pola strony produktu (13); przy błędzie strony wszystkie są None."""

KOLUMNY_CALKOWITE: frozenset[str] = frozenset(
    {"gwarancja_mies", "liczba_opinii", "stan_magazynowy_szt", "czas_dostawy_dni", "zwrot_dni"}
)
KOLUMNY_ZMIENNOPRZECINKOWE: frozenset[str] = frozenset(
    {
        "cena",
        "cena_poprzednia",
        "ocena",
        "waga_kg",
        "dlugosc_cm",
        "szerokosc_cm",
        "wysokosc_cm",
        "koszt_dostawy",
    }
)

WALUTA_GRATIS = "PLN"
"""Waluta kosztu dostawy `gratis` (0.0 zamiast None, żeby nie wyglądało jak brak danych)."""

# kolumna -> pole surowe; wartości tekstowe tylko normalizowane (nie mogą być nierozpoznane)
_POLA_TEKSTOWE: dict[str, str] = {
    "id": "id",
    "nazwa": "nazwa",
    "url": "url",
    "kategoria": "kategoria",
    "producent": "producent",
    "dostepnosc": "dostepnosc",
    "opis": "opis",
    "ean": "ean",
    "kod_producenta": "kod_producenta",
    "kolor": "kolor",
    "material": "material",
    "kraj_pochodzenia": "kraj_pochodzenia",
    "sprzedawca": "sprzedawca",
    "zrodlo": "zrodlo",
}

# kolumna -> (pole surowe, funkcja czyszcząca zwracająca wartość albo None)
_POLA_PRZETWARZANE: dict[str, tuple[str, Callable[[str | None], Any]]] = {
    "gwarancja_mies": ("gwarancja", czysc_gwarancje),
    "ocena": ("ocena", czysc_ocene),
    "liczba_opinii": ("liczba_opinii", czysc_liczbe_opinii),
    "data_dodania": ("data_dodania", czysc_date),
    "waga_kg": ("waga", czysc_wage),
    "stan_magazynowy_szt": ("stan_magazynowy", czysc_stan_magazynowy),
    "czas_dostawy_dni": ("czas_dostawy", czysc_czas_dostawy),
    "zwrot_dni": ("zwrot", czysc_zwrot),
}


def _czysc(surowy: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Zwraca (rekord oczyszczony w kolejności `KOLUMNY`, nazwy nierozpoznanych pól surowych)."""
    wynik: dict[str, Any] = dict.fromkeys(KOLUMNY)
    nierozpoznane: list[str] = []

    def sprawdz(pole: str, wartosc: Any) -> None:
        if wartosc is None and normalizuj(surowy.get(pole)) is not None:
            nierozpoznane.append(pole)

    for kolumna, pole in _POLA_TEKSTOWE.items():
        wynik[kolumna] = normalizuj(surowy.get(pole))

    for kolumna, (pole, funkcja) in _POLA_PRZETWARZANE.items():
        wynik[kolumna] = funkcja(surowy.get(pole))
        sprawdz(pole, wynik[kolumna])

    cena, waluta = czysc_cene(surowy.get("cena"), surowy.get("waluta"))
    wynik["cena"], wynik["waluta"] = cena, waluta
    sprawdz("cena", cena)

    poprzednia, waluta_poprzednia = czysc_cene(surowy.get("cena_poprzednia"), surowy.get("waluta"))
    if poprzednia is not None and waluta is not None and waluta_poprzednia != waluta:
        poprzednia = None  # inna waluta niż cena: nie zgadujemy przeliczenia
    wynik["cena_poprzednia"] = poprzednia
    sprawdz("cena_poprzednia", poprzednia)

    wymiary = czysc_wymiary(surowy.get("wymiary"))
    if wymiary is not None:
        wynik["dlugosc_cm"], wynik["szerokosc_cm"], wynik["wysokosc_cm"] = wymiary
    sprawdz("wymiary", wymiary)

    koszt_surowy = normalizuj(surowy.get("koszt_dostawy"))
    koszt, waluta_dostawy = czysc_koszt_dostawy(koszt_surowy)
    if koszt_surowy is not None and koszt_surowy.casefold() == "gratis":
        waluta_dostawy = WALUTA_GRATIS
    wynik["koszt_dostawy"], wynik["waluta_dostawy"] = koszt, waluta_dostawy
    sprawdz("koszt_dostawy", koszt)

    return wynik, nierozpoznane


def czysc_rekord(surowy: dict[str, Any]) -> dict[str, Any]:
    """Zwraca oczyszczony rekord (klucze w kolejności `KOLUMNY`, braki jako None).

    `surowy` to rekord listy scalony ze szczegółami produktu; brak kluczy szczegółów
    (np. po błędzie strony produktu) daje None w tych kolumnach.
    """
    return _czysc(surowy)[0]


def nierozpoznane_pola(surowy: dict[str, Any]) -> list[str]:
    """Zwraca nazwy pól surowych, które nie były brakiem, a czyszczenie dało None."""
    return _czysc(surowy)[1]


def czysc_rekord_z_kontrola(surowy: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Zwraca naraz rekord oczyszczony i listę nierozpoznanych pól (jedno czyszczenie)."""
    return _czysc(surowy)


def pola_listy(surowy: dict[str, Any]) -> dict[str, Any]:
    """Zwraca oczyszczone pola z listy (`KOLUMNY_LISTY`), np. do porównania duplikatów."""
    rekord = czysc_rekord(surowy)
    return {kolumna: rekord[kolumna] for kolumna in KOLUMNY_LISTY}
