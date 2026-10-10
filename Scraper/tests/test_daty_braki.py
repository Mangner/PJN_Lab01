"""Testy czyszczenia dat (DD.MM.RRRR -> ISO) i obsługi braków danych."""

import pytest

from bajtoparser.parsing.braki import normalizuj
from bajtoparser.parsing.daty import czysc_date

NBSP = chr(0xA0)  # twarda spacja U+00A0


@pytest.mark.parametrize(
    ("surowa", "oczekiwana"),
    [
        ("04.12.2025", "2025-12-04"),
        ("03.01.2026", "2026-01-03"),
        ("28.08.2026", "2026-08-28"),
        (" 29.02.2024 ", "2024-02-29"),  # rok przestępny, białe znaki
    ],
)
def test_data_na_iso(surowa: str, oczekiwana: str) -> None:
    assert czysc_date(surowa) == oczekiwana


@pytest.mark.parametrize(
    "surowa",
    [
        "31.02.2026",
        "29.02.2025",
        "32.01.2026",
        "00.01.2026",
        "2026-01-03",
        "abc",
        "4.12.2025",
        "—",
        "",
        None,
    ],
)
def test_niepoprawna_data_to_none(surowa: str | None) -> None:
    assert czysc_date(surowa) is None


@pytest.mark.parametrize("surowa", ["—", "", "   ", NBSP, f" {NBSP} ", None])
def test_braki_to_none(surowa: str | None) -> None:
    assert normalizuj(surowa) is None


def test_wartosc_jest_obcinana() -> None:
    assert normalizuj("  Granit  ") == "Granit"


def test_twarda_spacja_wewnatrz_zamieniana_na_zwykla() -> None:
    assert normalizuj(f"12{NBSP}mies.") == "12 mies."


def test_myslnik_w_srodku_tekstu_to_nie_brak() -> None:
    assert normalizuj("Elektro-Świat") == "Elektro-Świat"
