"""Testy czyszczenia cen: czysc_cene -> (wartość float, waluta PLN/EUR/USD)."""

import pytest

from bajtoparser.parsing.ceny import czysc_cene

NBSP = chr(0xA0)  # twarda spacja U+00A0


@pytest.mark.parametrize(
    ("surowa", "oczekiwana"),
    [
        (f"1{NBSP}299,00{NBSP}zł", (1299.0, "PLN")),  # twarda spacja U+00A0
        ("1 299,00 zł", (1299.0, "PLN")),  # zwykła spacja
        (f"99 999,99{NBSP}zł", (99999.99, "PLN")),
        (f"139,00{NBSP}zł", (139.0, "PLN")),
        (f"246,99{NBSP}€", (246.99, "EUR")),
        ("246,99 €", (246.99, "EUR")),
        ("$134.99", (134.99, "USD")),
        ("$1,299.00", (1299.0, "USD")),  # przecinek jako separator tysięcy
        ("$9,999.99", (9999.99, "USD")),
        ("$42.99", (42.99, "USD")),
    ],
)
def test_ceny_z_symbolem(surowa: str, oczekiwana: tuple[float, str]) -> None:
    assert czysc_cene(surowa) == oczekiwana


def test_przecinek_dziesietny_a_tysiace_zalezy_od_waluty() -> None:
    """Ta sama składnia „1,299” znaczy co innego dla PLN (ułamek) i USD (tysiące)."""
    assert czysc_cene("1,299 zł") == (1.299, "PLN")
    assert czysc_cene("$1,299") == (1299.0, "USD")


def test_waluta_z_atrybutu_gdy_brak_symbolu() -> None:
    assert czysc_cene("139,00", waluta="PLN") == (139.0, "PLN")


def test_symbol_ma_pierwszenstwo_przed_atrybutem() -> None:
    assert czysc_cene("246,99 €", waluta="PLN") == (246.99, "EUR")


@pytest.mark.parametrize("surowa", ["—", "", "   ", NBSP, None, "zł", "brak ceny"])
def test_brak_ceny_to_none_bez_wyjatku(surowa: str | None) -> None:
    assert czysc_cene(surowa) == (None, None)


def test_pusta_cena_poprzednia_to_brak_promocji() -> None:
    """Pusta cena_poprzednia (tabela: pusta komórka) daje None, nie wyjątek."""
    assert czysc_cene("") == (None, None)


def test_wartosc_jest_float() -> None:
    wartosc, _ = czysc_cene("100,00 zł")
    assert isinstance(wartosc, float)
