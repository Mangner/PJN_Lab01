"""Testy dekoratora retry (bez przeglądarki, z podmienionym czekaniem)."""

import pytest
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)

from bajtoparser.utils import retry
from bajtoparser.utils.logowanie import LICZNIK_RETRY
from bajtoparser.utils.retry import ponawiaj


class Obiekt:
    """Atrapa strony: operacja rzuca zadane wyjątki, potem zwraca wynik."""

    def __init__(self, bledy, driver=None):
        self.bledy = list(bledy)
        self.wywolania = 0
        if driver is not None:
            self.driver = driver

    @ponawiaj()
    def operacja(self):
        self.wywolania += 1
        if self.bledy:
            raise self.bledy.pop(0)
        return "ok"


@pytest.fixture
def diagnostyka(monkeypatch):
    """Podmienia zapis diagnostyki; zwraca listę (driver, operacja) wywołań."""
    wywolania = []
    monkeypatch.setattr(retry, "zapisz_diagnostyke", lambda d, op: wywolania.append((d, op)))
    return wywolania


def test_sukces_w_pierwszej_probie(opoznienia, diagnostyka):
    obiekt = Obiekt([])
    assert obiekt.operacja() == "ok"
    assert obiekt.wywolania == 1
    assert opoznienia == []
    assert LICZNIK_RETRY.wartosc == 0


def test_sukces_w_trzeciej_probie_opoznienia_1_2(opoznienia, diagnostyka):
    obiekt = Obiekt([TimeoutException(), TimeoutException()], driver=object())
    assert obiekt.operacja() == "ok"
    assert obiekt.wywolania == 3
    assert opoznienia == [1.0, 2.0]
    assert LICZNIK_RETRY.wartosc == 2
    assert diagnostyka == []


def test_wyczerpanie_prob_opoznienia_1_2_4_i_wyjatek_dalej(opoznienia, diagnostyka):
    driver = object()
    obiekt = Obiekt([TimeoutException()] * 10, driver=driver)
    with pytest.raises(TimeoutException):
        obiekt.operacja()
    assert obiekt.wywolania == 4
    assert opoznienia == [1.0, 2.0, 4.0]
    assert LICZNIK_RETRY.wartosc == 3
    assert len(diagnostyka) == 1
    assert diagnostyka[0][0] is driver
    assert "operacja" in diagnostyka[0][1]


def test_bez_drivera_nie_zapisuje_diagnostyki(opoznienia, diagnostyka):
    obiekt = Obiekt([TimeoutException()] * 10)
    with pytest.raises(TimeoutException):
        obiekt.operacja()
    assert diagnostyka == []


@pytest.mark.parametrize(
    "wyjatek",
    [TimeoutException, StaleElementReferenceException, ElementClickInterceptedException],
)
def test_ponawia_trzy_wyjatki_selenium(wyjatek, opoznienia, diagnostyka):
    obiekt = Obiekt([wyjatek()])
    assert obiekt.operacja() == "ok"
    assert obiekt.wywolania == 2


@pytest.mark.parametrize("wyjatek", [ValueError, KeyError, RuntimeError, Exception])
def test_inne_wyjatki_nie_sa_lapane(wyjatek, opoznienia, diagnostyka):
    obiekt = Obiekt([wyjatek("x")], driver=object())
    with pytest.raises(wyjatek):
        obiekt.operacja()
    assert obiekt.wywolania == 1
    assert opoznienia == []
    assert diagnostyka == []


def test_wlasny_limit_prob(opoznienia, diagnostyka):
    class Strona:
        driver = object()
        wywolania = 0

        @ponawiaj(max_prob=2)
        def op(self):
            self.wywolania += 1
            raise TimeoutException()

    strona = Strona()
    with pytest.raises(TimeoutException):
        strona.op()
    assert strona.wywolania == 2
    assert opoznienia == [1.0]
