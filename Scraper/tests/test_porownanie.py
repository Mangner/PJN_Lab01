"""Testy porównania surowego HTML z DOM: bez sieci i bez przeglądarki."""

import json
import logging
import urllib.error

import pytest

from bajtoparser import porownanie
from bajtoparser.porownanie import (
    DaneDom,
    StronaHtml,
    WynikPorownania,
    adres_podstrony,
    analizuj_html,
    linia_porownania,
    pobierz_html,
    porownaj,
    wniosek,
    zapisz_json,
)
from bajtoparser.utils import timing
from bajtoparser.utils.logowanie import PodsumowaniePrzebiegu

WIERSZ = '<tr class="wiersz-produktu" data-id="P1"><td>x</td></tr>'
KARTA = '<article class="produkt wyrozniony" data-id="P2"></article>'


@pytest.fixture(autouse=True)
def bez_czekania():
    """Pauzy nie czekają naprawdę; lista zapamiętuje żądane długości."""
    pauzy: list[float] = []
    poprzednia = timing.ustaw_funkcje_czekania(pauzy.append)
    yield pauzy
    timing.ustaw_funkcje_czekania(poprzednia)


def test_pusty_dokument_daje_zera():
    a = analizuj_html("")
    assert (a.wiersz_produktu, a.produkt, a.data_id, a.skrypty) == (0, 0, 0, 0)
    assert a.tekst == ""


def test_kilka_wystapien_jest_liczonych_osobno():
    html = f"<table>{WIERSZ * 3}</table>{KARTA * 2}"
    a = analizuj_html(html)
    assert (a.wiersz_produktu, a.produkt, a.data_id) == (3, 2, 5)


def test_klasa_wiersz_produktu_nie_jest_klasa_produkt():
    a = analizuj_html('<tr class="wiersz-produktu"></tr><div class="produktowy"></div>')
    assert (a.wiersz_produktu, a.produkt) == (1, 0)


def test_data_id_w_skrypcie_nie_jest_liczone():
    html = '<script>el.setAttribute("data-id", 1); // <tr class="wiersz-produktu"></script>'
    a = analizuj_html(html)
    assert (a.wiersz_produktu, a.data_id, a.skrypty) == (0, 0, 1)
    assert a.tekst == ""


def test_uszkodzony_html_nie_rzuca():
    a = analizuj_html('<div class="produkt" data-id=<<>> <tr class="wiersz-produktu')
    assert a.produkt >= 0


def test_adres_podstrony():
    assert adres_podstrony("http://x:8000", 1) == "http://x:8000/index.html"
    assert adres_podstrony("http://x:8000/", 4) == "http://x:8000/strona-4.html"
    with pytest.raises(ValueError):
        adres_podstrony("http://x/", 0)


def test_pobierz_html_blad_sieci_to_none_i_ostrzezenie(monkeypatch, caplog):
    def awaria(url, timeout):
        raise urllib.error.URLError("odmowa połączenia")

    monkeypatch.setattr(porownanie.urllib.request, "urlopen", awaria)
    with caplog.at_level(logging.WARNING, logger="bajtoparser"):
        assert pobierz_html("http://localhost:1/index.html", 0.5) is None
    assert any("nie powiodło się" in r.message for r in caplog.records)


def test_pobierz_html_timeout_to_none(monkeypatch):
    def awaria(url, timeout):
        raise TimeoutError("przekroczono czas")

    monkeypatch.setattr(porownanie.urllib.request, "urlopen", awaria)
    assert pobierz_html("http://localhost:1/", 0.1) is None


def atrapa(strony: dict[str, str | None]):
    """Pobieracz zwracający gotowy HTML dla adresu (brak klucza i None = błąd sieci)."""
    wywolania: list[str] = []

    def pobieracz(url, timeout_s):
        wywolania.append(url)
        return strony.get(url)

    pobieracz.wywolania = wywolania  # type: ignore[attr-defined]
    return pobieracz


def test_porownaj_jedna_strona_nie_pobrana_nie_przerywa(bez_czekania):
    baza = "http://s/"
    pobieracz = atrapa(
        {
            baza + "index.html": "<html><script></script></html>",
            baza + "strona-2.html": None,
            baza + "strona-3.html": f"{WIERSZ}{KARTA}",
        }
    )
    wynik = porownaj(baza, 3, [], pauza_s=0.5, pobieracz=pobieracz)

    assert [s.pobrano for s in wynik.podstrony] == [True, False, True]
    assert wynik.bledy_sieci == 1
    assert (wynik.suma_wiersz_produktu, wynik.suma_produkt, wynik.suma_data_id) == (1, 1, 2)
    assert wynik.podstrony[0].skrypty == 1


def test_porownaj_pauza_miedzy_zadaniami_nie_przed_pierwszym(bez_czekania):
    pobieracz = atrapa({})
    porownaj("http://s/", 3, [], pauza_s=0.1, pobieracz=pobieracz)
    assert len(pobieracz.wywolania) == 3
    assert bez_czekania == [0.5, 0.5]  # 2 pauzy, wartość podniesiona do minimum 0,5 s


def test_porownaj_probka_produktow_nazwa_i_id():
    baza = "http://s/"
    pobieracz = atrapa(
        {
            baza + "index.html": "",
            baza + "produkt/A.html": "<body><h1>Głośnik Łódź</h1><p>A</p></body>",
            baza + "produkt/B.html": "<body><h1></h1></body>",
        }
    )
    probka = [
        {"id": "A", "nazwa": "Głośnik  Łódź", "url": "/produkt/A.html"},
        {"id": "B", "nazwa": "Mysz", "url": "produkt/B.html"},
        {"id": "C", "nazwa": "Brak", "url": None},
    ]
    wynik = porownaj(baza, 1, probka, pobieracz=pobieracz)

    assert len(wynik.produkty) == 2  # produkt bez url jest pominięty
    assert (wynik.produkty[0].id_w_html, wynik.produkty[0].nazwa_w_html) == (True, True)
    assert (wynik.produkty[1].id_w_html, wynik.produkty[1].nazwa_w_html) == (False, False)
    assert (wynik.produkty_pobrane, wynik.produkty_z_nazwa_i_id) == (2, 1)


def dom(**zmiany):
    podsumowanie = PodsumowaniePrzebiegu(tryb="headless")
    podsumowanie.rekordy_lista = 72
    podsumowanie.rekordy_po_dedup = 72
    podsumowanie.rekordy = 3
    podsumowanie.pozycje_zrodlo = {"tabela": 30, "karta": 42}
    return DaneDom.z_podsumowania(podsumowanie)


def test_dane_dom_z_podsumowania():
    d = dom()
    assert (d.tryb, d.pozycje_lista, d.pozycje_tabela, d.pozycje_karta) == ("headless", 72, 30, 42)
    assert (d.po_deduplikacji, d.rekordy_csv) == (72, 3)


def test_wniosek_i_linia_gdy_html_bez_rekordow():
    wynik = WynikPorownania(podstrony=[StronaHtml(url="u", pobrano=True, bajty=3952, skrypty=2)])
    assert "JavaScript" in wniosek(wynik, dom())
    linia = linia_porownania(wynik, dom())
    assert "lista=72 (tabela 30 / karty 42)" in linia
    assert "wiersz-produktu=0, produkt=0, data-id=0" in linia


def test_wniosek_bez_pobranych_podstron():
    wynik = WynikPorownania(podstrony=[StronaHtml(url="u", pobrano=False)])
    assert "niemożliwe" in wniosek(wynik, dom())


def test_zapisz_json_zachowuje_polskie_znaki(tmp_path):
    wynik = WynikPorownania(
        podstrony=[StronaHtml(url="http://s/index.html", pobrano=True, bajty=10)],
        produkty=[StronaHtml(url="http://s/p.html", pobrano=True, id_w_html=True)],
    )
    sciezka = zapisz_json(wynik, dom(), tmp_path / "wyj", "test")

    assert sciezka.name == "test_porownanie.json"
    tekst = sciezka.read_text(encoding="utf-8")
    assert "zażółć" not in tekst and "\\u" not in tekst
    dane = json.loads(tekst)
    assert dane["raw_html"]["suma_data_id"] == 0
    assert dane["dom"]["pozycje_lista"] == 72
    assert "wniosek" in dane


def test_id_tylko_w_meta_i_noscript_nie_jest_trescia_rekordu():
    baza = "http://s/"
    html = (
        '<head><meta name="produkt" content="P1"></head>'
        "<body><noscript><p>Dane: <code>dane/produkt/P1.json</code></p></noscript>"
        '<h1 id="nazwa-produktu"></h1></body>'
    )
    pobieracz = atrapa({baza + "index.html": "", baza + "produkt/P1.html": html})
    probka = [{"id": "P1", "nazwa": "Kabel", "url": "produkt/P1.html"}]
    wynik = porownaj(baza, 1, probka, pobieracz=pobieracz)

    produkt = wynik.produkty[0]
    assert produkt.id_w_html is False  # to wskazówka na plik JSON, nie dane rekordu
    assert produkt.id_gdziekolwiek is True
    assert produkt.nazwa_w_html is False
    assert wynik.produkty_z_nazwa_i_id == 0
