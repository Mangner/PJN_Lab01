"""Testy ProductPage bez przeglądarki: czysta logika i atrapa drivera."""

import typing

import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from bajtoparser.pages.product_page import ProductPage, SzczegolyProduktu, url_produktu
from bajtoparser.utils import retry

BAZA = "http://localhost:8000"


class ElementAtrapy:
    def __init__(self, atrybuty=None, po_kliknieciu=None):
        self.atrybuty = atrybuty if atrybuty is not None else {}
        self.po_kliknieciu = po_kliknieciu

    def get_attribute(self, nazwa):
        return self.atrybuty.get(nazwa)

    def is_displayed(self):
        return True

    def is_enabled(self):
        return True

    def click(self):
        if self.po_kliknieciu:
            self.po_kliknieciu()


class AtrapaProduktu:
    """Symuluje stronę produktu: body ze stanem renderu oraz zakładki z panelami."""

    page_source = "<html></html>"

    def __init__(self, renderuje=True, wypelnia=True):
        self.renderuje = renderuje
        self.wypelnia = wypelnia
        self.zdarzenia = []
        self.body = ElementAtrapy()
        self.panele = {
            "#panel-specyfikacja": ElementAtrapy(),
            "#panel-dostawa": ElementAtrapy(),
        }
        self.przyciski = {
            'button.zakladka[data-panel="specyfikacja"]': self._zakladka("#panel-specyfikacja"),
            'button.zakladka[data-panel="dostawa"]': self._zakladka("#panel-dostawa"),
        }

    def _zakladka(self, panel):
        def po_kliknieciu():
            self.zdarzenia.append(("klik", panel))
            if self.wypelnia:
                self.panele[panel].atrybuty["data-wypelnione"] = "tak"

        return ElementAtrapy(po_kliknieciu=po_kliknieciu)

    def get(self, url):
        self.zdarzenia.append(("get", url))
        if self.renderuje:
            self.body.atrybuty["data-stan-renderu"] = "gotowy"

    def find_element(self, by, wartosc):
        if wartosc == "body":
            return self.body
        for slownik in (self.przyciski, self.panele):
            if wartosc in slownik:
                return slownik[wartosc]
        raise NoSuchElementException(wartosc)

    def execute_script(self, skrypt, *argumenty):
        self.zdarzenia.append(("skrypt", argumenty))
        return {"ean": None}

    def save_screenshot(self, sciezka):
        return True


@pytest.fixture
def strona_produktu():
    def fabryka(**kwargs):
        driver = AtrapaProduktu(**kwargs)
        strona = ProductPage(driver, adres_serwisu=BAZA, timeout_s=0.05, poll_s=0.01)
        return strona, driver

    return fabryka


@pytest.fixture
def diagnostyka(monkeypatch):
    wywolania = []
    monkeypatch.setattr(retry, "zapisz_diagnostyke", lambda d, op: wywolania.append(op))
    return wywolania


# --- czyste funkcje i stałe --------------------------------------------------


@pytest.mark.parametrize(
    ("url", "oczekiwany"),
    [
        ("/produkt/P1.html", "http://localhost:8000/produkt/P1.html"),
        ("produkt/P1.html", "http://localhost:8000/produkt/P1.html"),
        ("http://localhost:8000/produkt/P1.html", "http://localhost:8000/produkt/P1.html"),
    ],
)
def test_url_produktu(url, oczekiwany):
    assert url_produktu(BAZA + "/", url) == oczekiwany
    assert url_produktu(BAZA, url) == oczekiwany


@pytest.mark.parametrize("url", [None, "", "   "])
def test_url_produktu_odrzuca_pusty_adres(url):
    with pytest.raises(ValueError):
        url_produktu(BAZA, url)


def test_stale_pol_odpowiadaja_kluczom_typeddict():
    klucze = set(typing.get_type_hints(SzczegolyProduktu))
    zebrane = {"opis", *ProductPage.POLA_SPECYFIKACJA, *ProductPage.POLA_DOSTAWA}
    assert klucze == zebrane
    assert len(klucze) == 13
    assert len(ProductPage.POLA_SPECYFIKACJA) == 7
    assert len(ProductPage.POLA_DOSTAWA) == 5


# --- atrapa drivera ----------------------------------------------------------


def test_pobierz_szczegoly_kolejnosc_krokow(strona_produktu, opoznienia):
    strona, driver = strona_produktu()
    wynik = strona.pobierz_szczegoly("/produkt/P1.html")
    assert wynik == {"ean": None}
    rodzaje = [z[0] for z in driver.zdarzenia]
    assert rodzaje == ["get", "klik", "klik", "skrypt"]
    assert driver.zdarzenia[0][1] == "http://localhost:8000/produkt/P1.html"
    assert [z[1] for z in driver.zdarzenia[1:3]] == ["#panel-specyfikacja", "#panel-dostawa"]


def test_pola_czytane_jednym_skryptem_z_selektorami_jako_argumentem(strona_produktu):
    strona, driver = strona_produktu()
    strona.pobierz_pola()
    skrypt = driver.zdarzenia[0]
    (parametry,) = skrypt[1]
    assert parametry["panel_opis"] == "#panel-opis"
    pola = {p for g in parametry["grupy"] for p in g["pola"]}
    assert len(pola) == 12
    assert len(driver.zdarzenia) == 1


def test_skrypty_sa_statyczne_bez_selektorow_serwisu():
    selektory = [
        ProductPage.SEL_PANEL_OPIS,
        *ProductPage.POLA_SPECYFIKACJA.values(),
        *ProductPage.POLA_DOSTAWA.values(),
    ]
    for skrypt in (ProductPage._JS_SZCZEGOLY, ProductPage._JS_STAN_PANELI):
        for selektor in selektory:
            assert selektor not in skrypt


def test_nieznana_zakladka_to_valueerror_bez_klikania(strona_produktu, opoznienia):
    strona, driver = strona_produktu()
    with pytest.raises(ValueError):
        strona.otworz_zakladke("opis")
    assert driver.zdarzenia == []
    assert opoznienia == []


def test_brak_renderu_propaguje_timeout_po_czterech_probach_i_jedna_diagnostyka(
    strona_produktu, opoznienia, diagnostyka
):
    strona, driver = strona_produktu(renderuje=False)
    with pytest.raises(TimeoutException):
        strona.pobierz_szczegoly("/produkt/P404.html")
    assert [z[0] for z in driver.zdarzenia] == ["get"] * 4  # bez zagnieżdżania: 4, nie 16
    assert len(diagnostyka) == 1
    assert [o for o in opoznienia if o != 0.5] == [1.0, 2.0, 4.0]  # backoff; 0,5 s to pauza


def test_zakladka_ktora_sie_nie_wypelnia_ponawia_osobno(strona_produktu, opoznienia, diagnostyka):
    strona, driver = strona_produktu(wypelnia=False)
    with pytest.raises(TimeoutException):
        strona.pobierz_szczegoly("/produkt/P1.html")
    rodzaje = [z[0] for z in driver.zdarzenia]
    assert rodzaje.count("get") == 1  # otwarcie produktu nie jest ponawiane razem z zakładką
    assert rodzaje.count("klik") == 4
    assert "skrypt" not in rodzaje
    assert len(diagnostyka) == 1
