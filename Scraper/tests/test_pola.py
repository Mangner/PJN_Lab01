"""Testy czyszczenia pozostałych pól (ocena, opinie, gwarancja, szczegóły produktu).

Formaty pochodzą z rzeczywistych wartości w DOM (podstrona 1 i 20 stron produktów).
"""

import pytest

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

NBSP = chr(0xA0)  # twarda spacja U+00A0
BRAKI = ["—", "", "  ", None]


@pytest.mark.parametrize(
    ("surowa", "oczekiwana"), [("4,1", 4.1), ("5,0", 5.0), ("3,5", 3.5), ("4.6", 4.6)]
)
def test_ocena(surowa: str, oczekiwana: float) -> None:
    assert czysc_ocene(surowa) == oczekiwana


@pytest.mark.parametrize("surowa", [*BRAKI, "brak"])
def test_ocena_brak(surowa: str | None) -> None:
    assert czysc_ocene(surowa) is None


@pytest.mark.parametrize(("surowa", "oczekiwana"), [("25", 25), ("8", 8), ("120", 120)])
def test_liczba_opinii(surowa: str, oczekiwana: int) -> None:
    assert czysc_liczbe_opinii(surowa) == oczekiwana


@pytest.mark.parametrize("surowa", [*BRAKI, "dużo"])
def test_liczba_opinii_brak(surowa: str | None) -> None:
    assert czysc_liczbe_opinii(surowa) is None


@pytest.mark.parametrize(
    ("surowa", "oczekiwana"), [("24 mies.", 24), ("12 mies.", 12), ("60 mies.", 60)]
)
def test_gwarancja_w_miesiacach(surowa: str, oczekiwana: int) -> None:
    assert czysc_gwarancje(surowa) == oczekiwana


@pytest.mark.parametrize("surowa", BRAKI)
def test_gwarancja_brak(surowa: str | None) -> None:
    assert czysc_gwarancje(surowa) is None


@pytest.mark.parametrize(
    ("surowa", "oczekiwana"), [(f"1,47{NBSP}kg", 1.47), ("14,1 kg", 14.1), ("0,31 kg", 0.31)]
)
def test_waga_w_kg(surowa: str, oczekiwana: float) -> None:
    assert czysc_wage(surowa) == oczekiwana


def test_waga_w_nieznanej_jednostce_to_none() -> None:
    assert czysc_wage("250 g") is None


@pytest.mark.parametrize("surowa", BRAKI)
def test_waga_brak(surowa: str | None) -> None:
    assert czysc_wage(surowa) is None


@pytest.mark.parametrize(
    ("surowa", "oczekiwana"),
    [(f"17 x 9 x 8{NBSP}cm", (17.0, 9.0, 8.0)), ("55 x 112 x 172 cm", (55.0, 112.0, 172.0))],
)
def test_wymiary_w_cm(surowa: str, oczekiwana: tuple[float, float, float]) -> None:
    assert czysc_wymiary(surowa) == oczekiwana


@pytest.mark.parametrize("surowa", [*BRAKI, "17 x 9 cm"])
def test_wymiary_brak(surowa: str | None) -> None:
    assert czysc_wymiary(surowa) is None


@pytest.mark.parametrize(("surowa", "oczekiwana"), [("0 szt.", 0), ("158 szt.", 158)])
def test_stan_magazynowy(surowa: str, oczekiwana: int) -> None:
    assert czysc_stan_magazynowy(surowa) == oczekiwana


@pytest.mark.parametrize(("surowa", "oczekiwana"), [("8 dni roboczych", 8), ("1 dni roboczych", 1)])
def test_czas_dostawy_w_dniach(surowa: str, oczekiwana: int) -> None:
    assert czysc_czas_dostawy(surowa) == oczekiwana


@pytest.mark.parametrize(
    ("surowa", "oczekiwana"), [("30 dni na zwrot", 30), ("100 dni na zwrot", 100)]
)
def test_zwrot_w_dniach(surowa: str, oczekiwana: int) -> None:
    assert czysc_zwrot(surowa) == oczekiwana


def test_koszt_dostawy_liczbowy_i_gratis() -> None:
    assert czysc_koszt_dostawy(f"14,99{NBSP}zł") == (14.99, "PLN")
    assert czysc_koszt_dostawy("gratis") == (0.0, None)
    assert czysc_koszt_dostawy("—") == (None, None)
