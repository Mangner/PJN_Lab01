"""Testy BasePage z atrapą drivera (bez przeglądarki)."""

import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By

from bajtoparser.pages.base_page import BasePage
from bajtoparser.utils import retry

LOKATOR = (By.CSS_SELECTOR, ".cos")


class Element:
    def __init__(self, tekst="", atrybuty=None):
        self.text = tekst
        self._atrybuty = atrybuty or {}

    def get_attribute(self, nazwa):
        return self._atrybuty.get(nazwa)


class AtrapaDrivera:
    page_source = "<html></html>"

    def __init__(self, element=None, blad=None):
        self.element = element
        self.blad = blad
        self.otwarte = []

    def find_element(self, *lokator):
        if self.blad is not None:
            raise self.blad
        return self.element

    def get(self, url):
        self.otwarte.append(url)

    def save_screenshot(self, sciezka):
        return True


def strona(driver):
    return BasePage(driver, timeout_s=0.05, poll_s=0.01)


def test_tekst_zwraca_tekst_elementu():
    assert strona(AtrapaDrivera(Element("Cena"))).tekst(LOKATOR) == "Cena"


def test_tekst_brak_elementu_zwraca_domyslny():
    s = strona(AtrapaDrivera(blad=NoSuchElementException("brak")))
    assert s.tekst(LOKATOR) is None
    assert s.tekst(LOKATOR, domyslny="—") == "—"


def test_tekst_nie_maskuje_timeoutu_jako_braku_danych():
    s = strona(AtrapaDrivera(blad=TimeoutException("ładowanie")))
    with pytest.raises(TimeoutException):
        s.tekst(LOKATOR)


def test_otworz_przekazuje_url():
    driver = AtrapaDrivera()
    strona(driver).otworz("http://localhost:8000/")
    assert driver.otwarte == ["http://localhost:8000/"]


def test_otworz_pauza_grzecznosciowa_poza_pierwszym_zadaniem(opoznienia):
    driver = AtrapaDrivera()
    strona(driver).otworz("http://localhost:8000/")
    assert opoznienia == []
    strona(driver).otworz("http://localhost:8000/strona-2.html")
    strona(driver).otworz("http://localhost:8000/strona-3.html")
    assert opoznienia == [0.5, 0.5]
    assert len(driver.otwarte) == 3


def test_otworz_pierwsze_zadanie_na_nowym_driverze_bez_pauzy(opoznienia):
    strona(AtrapaDrivera()).otworz("http://localhost:8000/")
    strona(AtrapaDrivera()).otworz("http://localhost:8000/")
    assert opoznienia == []


def test_czekaj_na_atrybut_zwraca_wartosc():
    s = strona(AtrapaDrivera(Element(atrybuty={"data-wczytano": "12"})))
    assert s.czekaj_na_atrybut(LOKATOR, "data-wczytano") == "12"
    assert s.czekaj_na_atrybut(LOKATOR, "data-wczytano", "12") == "12"


def test_czekaj_na_wzrost_atrybutu():
    s = strona(AtrapaDrivera(Element(atrybuty={"data-wczytano": "24"})))
    assert s.czekaj_na_wzrost_atrybutu(LOKATOR, "data-wczytano", 12) == 24


def test_czekaj_na_wzrost_atrybutu_timeout_gdy_brak_wzrostu():
    s = strona(AtrapaDrivera(Element(atrybuty={"data-wczytano": "12"})))
    with pytest.raises(TimeoutException):
        s.czekaj_na_wzrost_atrybutu(LOKATOR, "data-wczytano", 12)


def test_kliknij_nieistniejacy_element_retry_i_jedna_diagnostyka(opoznienia, monkeypatch):
    wywolania = []
    monkeypatch.setattr(retry, "zapisz_diagnostyke", lambda d, op: wywolania.append(op))
    s = strona(AtrapaDrivera(blad=NoSuchElementException("brak")))
    with pytest.raises(TimeoutException):
        s.kliknij(LOKATOR)
    assert opoznienia == [1.0, 2.0, 4.0]
    assert len(wywolania) == 1
