"""Testy CatalogPage bez przeglądarki: czysta logika i atrapa drivera (maszyna stanów)."""

import pytest
from selenium.common.exceptions import TimeoutException

from bajtoparser.pages.catalog_page import (
    CatalogPage,
    url_podstrony,
    ustal_liczbe_podstron,
    wczytano_wszystko,
)
from bajtoparser.utils import retry


class ElementAtrapy:
    def __init__(self, atrybuty=None, widoczny=True, po_kliknieciu=None):
        self.atrybuty = atrybuty if atrybuty is not None else {}
        self.widoczny = widoczny
        self.po_kliknieciu = po_kliknieciu

    def get_attribute(self, nazwa):
        wartosc = self.atrybuty.get(nazwa)
        return wartosc() if callable(wartosc) else wartosc

    def is_displayed(self):
        return self.widoczny() if callable(self.widoczny) else self.widoczny

    def is_enabled(self):
        return True

    def click(self):
        if self.po_kliknieciu:
            self.po_kliknieciu()


class AtrapaKatalogu:
    """Symuluje body z licznikami i przycisk „Wczytaj więcej” (porcje po 12)."""

    page_source = "<html></html>"

    def __init__(self, porcji=6, zawieszony=False, start_porcja=1):
        self.porcji = porcji
        self.porcja = start_porcja
        self.wczytano = 12 * start_porcja
        self.zawieszony = zawieszony
        self.klikniecia = 0
        self.otwarte = []
        self.linki = []
        self.body = ElementAtrapy(
            {
                "data-wczytano": lambda: str(self.wczytano),
                "data-porcja": lambda: str(self.porcja),
                "data-porcji-lacznie": lambda: str(self.porcji),
            }
        )
        self.przycisk = ElementAtrapy(
            widoczny=lambda: self.porcja < self.porcji, po_kliknieciu=self._kliknieto
        )

    def _kliknieto(self):
        self.klikniecia += 1
        if not self.zawieszony:
            self.porcja += 1
            self.wczytano += 12

    def find_element(self, by, wartosc):
        return {"body": self.body, "#wczytaj-wiecej": self.przycisk}[wartosc]

    def find_elements(self, by, wartosc):
        return [ElementAtrapy({"href": href}) for href in self.linki]

    def get(self, url):
        self.otwarte.append(url)

    def save_screenshot(self, sciezka):
        return True


@pytest.fixture
def strona_katalogu():
    def fabryka(**kwargs):
        driver = AtrapaKatalogu(**kwargs)
        strona = CatalogPage(
            driver, adres_serwisu="http://localhost:8000", timeout_s=0.05, poll_s=0.01
        )
        return strona, driver

    return fabryka


@pytest.fixture
def diagnostyka(monkeypatch):
    wywolania = []
    monkeypatch.setattr(retry, "zapisz_diagnostyke", lambda d, op: wywolania.append(op))
    return wywolania


# --- czyste funkcje ---------------------------------------------------------


def test_url_podstrony():
    assert url_podstrony("http://localhost:8000/", 1) == "http://localhost:8000/index.html"
    assert url_podstrony("http://localhost:8000", 2) == "http://localhost:8000/strona-2.html"
    assert url_podstrony("http://localhost:8000/", 6) == "http://localhost:8000/strona-6.html"


def test_url_podstrony_odrzuca_numer_ponizej_1():
    with pytest.raises(ValueError):
        url_podstrony("http://localhost:8000/", 0)


def test_liczba_podstron_z_linkow_paginacji():
    hrefy = [f"http://localhost:8000/strona-{n}.html" for n in range(2, 7)]
    hrefy += ["http://localhost:8000/", "/robots.txt", "/dane/katalog.json", None]
    assert ustal_liczbe_podstron(hrefy) == 6


def test_liczba_podstron_nie_jest_wpisana_na_sztywno():
    assert ustal_liczbe_podstron(["/strona-2.html", "/strona-9.html"]) == 9


def test_liczba_podstron_bez_linkow_to_jedna():
    assert ustal_liczbe_podstron([]) == 1
    assert ustal_liczbe_podstron(["/", "/robots.txt"]) == 1


@pytest.mark.parametrize(
    ("porcja", "lacznie", "oczekiwane"),
    [
        ("6", "6", True),
        ("5", "6", False),
        ("1", "6", False),
        (None, "6", False),
        ("6", None, False),
        ("x", "6", False),
        ("", "", False),
    ],
)
def test_wczytano_wszystko(porcja, lacznie, oczekiwane):
    assert wczytano_wszystko(porcja, lacznie) is oczekiwane


# --- atrapa drivera ----------------------------------------------------------


def test_otworz_podstrone_uzywa_url_i_czeka_na_dane(strona_katalogu):
    strona, driver = strona_katalogu()
    strona.otworz_podstrone(2)
    assert driver.otwarte == ["http://localhost:8000/strona-2.html"]


def test_liczba_podstron_z_dom(strona_katalogu):
    strona, driver = strona_katalogu()
    driver.linki = ["/strona-2.html", "/strona-3.html", "/strona-6.html", "/"]
    assert strona.liczba_podstron() == 6


def test_wczytaj_wszystko_klika_do_wyczerpania_z_pauza(strona_katalogu, opoznienia):
    strona, driver = strona_katalogu()
    assert strona.wczytaj_wszystko() == 72
    assert driver.klikniecia == 5
    assert opoznienia == [0.5] * 5  # pauza grzecznościowa przed każdym kliknięciem


def test_wczytaj_wszystko_nie_klika_gdy_juz_wyczerpane(strona_katalogu, opoznienia):
    strona, driver = strona_katalogu(start_porcja=6)
    assert strona.wczytaj_wszystko() == 72
    assert driver.klikniecia == 0
    assert opoznienia == []


def test_wczytaj_wszystko_twardy_limit_iteracji(strona_katalogu, opoznienia, monkeypatch):
    monkeypatch.setattr(CatalogPage, "MAKS_PORCJI", 3)
    strona, driver = strona_katalogu(porcji=100)
    with pytest.raises(RuntimeError):
        strona.wczytaj_wszystko()
    assert driver.klikniecia == 3


def test_zawieszone_doladowywanie_konczy_sie_timeoutem_i_jedna_diagnostyka(
    strona_katalogu, opoznienia, diagnostyka
):
    strona, driver = strona_katalogu(zawieszony=True)
    with pytest.raises(TimeoutException):
        strona.wczytaj_wszystko()
    assert driver.klikniecia == 4  # 4 próby jednej porcji, bez zagnieżdżonych pętli
    assert len(diagnostyka) == 1


def test_pobierz_rekordy_przekazuje_selektory_do_statycznego_skryptu(strona_katalogu):
    strona, driver = strona_katalogu()
    wywolania = []

    def execute_script(skrypt, *argumenty):
        wywolania.append((skrypt, argumenty))
        return [{"id": "P1", "zrodlo": "tabela"}]

    driver.execute_script = execute_script
    assert strona.pobierz_rekordy() == [{"id": "P1", "zrodlo": "tabela"}]
    skrypt, (parametry,) = wywolania[0]
    assert parametry["wiersz"] == "tr.wiersz-produktu"
    assert parametry["karta"] == "article.produkt"
    assert set(parametry["pola"]) >= {"cena", "cena_poprzednia", "producent", "ocena"}
    # skrypt jest statyczny: żadnego selektora serwisu w treści JS
    for selektor in [parametry["wiersz"], parametry["karta"], *parametry["pola"].values()]:
        assert selektor not in skrypt
