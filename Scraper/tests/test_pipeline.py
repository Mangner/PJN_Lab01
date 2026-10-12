"""Testy pipeline'u na atrapach stron (bez przeglądarki)."""

import dataclasses
import json
import logging

import pandas as pd
import pytest
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException

from bajtoparser.parsing.rekord import KOLUMNY
from bajtoparser.pipeline import Pipeline
from bajtoparser.utils.konfiguracja import KONFIGURACJA

SZCZEGOLY = {
    "opis": "Zażółć gęślą jaźń",
    "ean": "0590123456789",
    "kod_producenta": "GX-12",
    "kolor": "czarny",
    "material": "tworzywo",
    "waga": "1,47 kg",
    "wymiary": "17 x 9 x 8 cm",
    "kraj_pochodzenia": "Polska",
    "sprzedawca": "Bajtomarket",
    "stan_magazynowy": "158 szt.",
    "czas_dostawy": "8 dni roboczych",
    "koszt_dostawy": "gratis",
    "zwrot": "30 dni na zwrot",
}


def pozycja(id_, cena="100,00 zł", zrodlo="tabela", **zmiany):
    """Surowy rekord listy, jak z `CatalogPage.pobierz_rekordy`."""
    rekord = {
        "id": id_,
        "nazwa": f"Produkt {id_} Łódź",
        "url": f"/produkt/{id_}.html",
        "cena": cena,
        "waluta": "PLN",
        "cena_poprzednia": "" if zrodlo == "tabela" else None,
        "kategoria": "Audio",
        "producent": "—",
        "dostepnosc": "dostępny",
        "gwarancja": "24 mies.",
        "ocena": "4,5",
        "liczba_opinii": "12",
        "data_dodania": "01.02.2026",
        "zrodlo": zrodlo,
    }
    rekord.update(zmiany)
    return rekord


class AtrapaKatalogu:
    """Atrapa `CatalogPage`: podstrony z gotowymi rekordami, opcjonalne błędy."""

    def __init__(self, podstrony, blad_wczytania=(), blad_otwarcia=()):
        self.podstrony = podstrony
        self.blad_wczytania = set(blad_wczytania)
        self.blad_otwarcia = set(blad_otwarcia)
        self.otwarte = []
        self.biezaca = None

    def otworz_podstrone(self, nr):
        self.otwarte.append(nr)
        if nr in self.blad_otwarcia:
            raise TimeoutException("atrapa: podstrona się nie otworzyła")
        self.biezaca = nr

    def liczba_podstron(self):
        return len(self.podstrony)

    def wczytaj_wszystko(self):
        if self.biezaca in self.blad_wczytania:
            raise StaleElementReferenceException("atrapa: błąd doładowywania")
        return len(self.podstrony[self.biezaca])

    def pobierz_rekordy(self):
        return [dict(r) for r in self.podstrony[self.biezaca]]


class AtrapaProduktu:
    """Atrapa `ProductPage`: zapamiętuje odwiedzone url, rzuca wyjątki dla wskazanych."""

    def __init__(self, bledy=(), przerwij_na=None, szczegoly=None):
        self.bledy = set(bledy)
        self.przerwij_na = przerwij_na
        self.szczegoly = szczegoly or {}
        self.odwiedzone = []

    def pobierz_szczegoly(self, url):
        self.odwiedzone.append(url)
        if url == self.przerwij_na:
            raise KeyboardInterrupt
        if url in self.bledy:
            raise TimeoutException("atrapa: produkt się nie wczytał")
        return {**SZCZEGOLY, **self.szczegoly.get(url, {})}


@pytest.fixture
def konfiguracja(tmp_path):
    return dataclasses.replace(
        KONFIGURACJA, katalog_wyjscia=tmp_path, nazwa_wyjscia="test", headless=True
    )


def uruchom(katalog, produkt, konfiguracja, **zmiany):
    konf = dataclasses.replace(konfiguracja, **zmiany)
    return Pipeline(katalog, produkt, konf).uruchom()


def wczytaj_csv(konfiguracja):
    return pd.read_csv(konfiguracja.katalog_wyjscia / "test.csv", encoding="utf-8")


def wczytaj_jsonl(konfiguracja):
    plik = konfiguracja.katalog_wyjscia / "test_surowe.jsonl"
    return [json.loads(linia) for linia in plik.read_text(encoding="utf-8").splitlines()]


def test_deduplikacja_przed_szczegolami(konfiguracja):
    katalog = AtrapaKatalogu(
        {
            1: [pozycja("A"), pozycja("B"), pozycja("C")],
            2: [pozycja("D"), pozycja("A", zrodlo="karta")],
        }
    )
    produkt = AtrapaProduktu()
    p = uruchom(katalog, produkt, konfiguracja)

    assert produkt.odwiedzone == [f"/produkt/{x}.html" for x in "ABCD"]
    assert (p.rekordy_lista, p.rekordy_po_dedup, p.duplikaty) == (5, 4, 1)
    assert p.duplikaty_rozne == 0  # "" w tabeli i brak w karcie to ta sama „brak promocji”
    assert (p.strony, p.rekordy, p.bledy, p.ze_szczegolami, p.nierozpoznane) == (2, 4, 0, 4, 0)
    assert p.tryb == "headless" and not p.przerwano

    ramka = wczytaj_csv(konfiguracja)
    assert list(ramka.columns) == KOLUMNY
    assert list(ramka["id"]) == list("ABCD")
    assert (ramka["koszt_dostawy"] == 0.0).all()


def test_duplikat_rozny_od_oryginalu_jest_logowany(konfiguracja, caplog):
    katalog = AtrapaKatalogu({1: [pozycja("A")], 2: [pozycja("A", cena="90,00 zł")]})
    with caplog.at_level(logging.WARNING, logger="bajtoparser"):
        p = uruchom(katalog, AtrapaProduktu(), konfiguracja)
    assert (p.duplikaty, p.duplikaty_rozne, p.rekordy) == (1, 1, 1)
    assert any("Duplikaty różne" in r.message and "A" in r.message for r in caplog.records)
    assert wczytaj_csv(konfiguracja).loc[0, "cena"] == 100.0  # zostaje pierwsze wystąpienie


def test_limit_produktow(konfiguracja):
    katalog = AtrapaKatalogu({1: [pozycja(x) for x in "ABCDE"]})
    produkt = AtrapaProduktu()
    p = uruchom(katalog, produkt, konfiguracja, limit=2)
    assert len(produkt.odwiedzone) == 2
    assert p.rekordy == 2 and p.rekordy_po_dedup == 5
    assert len(wczytaj_csv(konfiguracja)) == 2


def test_limit_podstron(konfiguracja):
    katalog = AtrapaKatalogu({1: [pozycja("A")], 2: [pozycja("B")], 3: [pozycja("C")]})
    p = uruchom(katalog, AtrapaProduktu(), konfiguracja, strony=2)
    assert katalog.otwarte == [1, 2]
    assert (p.strony, p.rekordy) == (2, 2)


def test_limit_podstron_wiekszy_niz_serwis(konfiguracja):
    katalog = AtrapaKatalogu({1: [pozycja("A")]})
    p = uruchom(katalog, AtrapaProduktu(), konfiguracja, strony=6)
    assert katalog.otwarte == [1] and p.strony == 1


def test_blad_produktu_nie_przerywa_petli(konfiguracja, caplog):
    katalog = AtrapaKatalogu({1: [pozycja(x) for x in "ABC"]})
    produkt = AtrapaProduktu(bledy={"/produkt/B.html"})
    with caplog.at_level(logging.WARNING, logger="bajtoparser"):
        p = uruchom(katalog, produkt, konfiguracja)

    assert len(produkt.odwiedzone) == 3
    assert (p.rekordy, p.bledy, p.ze_szczegolami, p.nierozpoznane) == (3, 1, 2, 0)
    assert any("B" in r.message and "TimeoutException" in r.message for r in caplog.records)

    ramka = wczytaj_csv(konfiguracja).set_index("id")
    assert ramka.loc["B", "cena"] == 100.0  # dane z listy zostają
    assert pd.isna(ramka.loc["B", "opis"]) and pd.isna(ramka.loc["B", "waga_kg"])
    assert ramka.loc["A", "waga_kg"] == 1.47


def test_rekord_bez_url_to_blad_bez_wizyty(konfiguracja):
    katalog = AtrapaKatalogu({1: [pozycja("A", url=None), pozycja("B")]})
    produkt = AtrapaProduktu()
    p = uruchom(katalog, produkt, konfiguracja)
    assert produkt.odwiedzone == ["/produkt/B.html"]
    assert (p.rekordy, p.bledy) == (2, 1)


def test_blad_doladowywania_pomija_cala_podstrone(konfiguracja, caplog):
    katalog = AtrapaKatalogu(
        {1: [pozycja("A")], 2: [pozycja("B"), pozycja("C")], 3: [pozycja("D")]},
        blad_wczytania={2},
    )
    with caplog.at_level(logging.WARNING, logger="bajtoparser"):
        p = uruchom(katalog, AtrapaProduktu(), konfiguracja)
    assert p.pominiete_strony == [2]
    assert (p.strony, p.bledy, p.rekordy_lista) == (2, 1, 2)
    assert list(wczytaj_csv(konfiguracja)["id"]) == ["A", "D"]
    assert any("Podstrona 2 pominięta" in r.message for r in caplog.records)


def test_blad_otwarcia_dalszej_podstrony_pomija_ja(konfiguracja):
    katalog = AtrapaKatalogu({1: [pozycja("A")], 2: [pozycja("B")]}, blad_otwarcia={2})
    p = uruchom(katalog, AtrapaProduktu(), konfiguracja)
    assert p.pominiete_strony == [2] and p.rekordy == 1


def test_blad_otwarcia_pierwszej_podstrony_jest_krytyczny(konfiguracja):
    katalog = AtrapaKatalogu({1: [pozycja("A")]}, blad_otwarcia={1})
    with pytest.raises(TimeoutException):
        uruchom(katalog, AtrapaProduktu(), konfiguracja)
    assert not (konfiguracja.katalog_wyjscia / "test.csv").exists()


def test_keyboard_interrupt_zapisuje_zebrane(konfiguracja):
    katalog = AtrapaKatalogu({1: [pozycja(x) for x in "ABCD"]})
    produkt = AtrapaProduktu(przerwij_na="/produkt/C.html")
    p = uruchom(katalog, produkt, konfiguracja)

    assert p.przerwano
    assert p.rekordy == 2 and p.czas_s >= 0
    assert list(wczytaj_csv(konfiguracja)["id"]) == ["A", "B"]
    assert (konfiguracja.katalog_wyjscia / "test.json").exists()
    assert [r["id"] for r in wczytaj_jsonl(konfiguracja)] == ["A", "B"]


def test_zapis_jsonl_w_locie(konfiguracja):
    katalog = AtrapaKatalogu({1: [pozycja("A"), pozycja("B")]})
    produkt = AtrapaProduktu(bledy={"/produkt/B.html"})
    uruchom(katalog, produkt, konfiguracja)

    tekst = (konfiguracja.katalog_wyjscia / "test_surowe.jsonl").read_text(encoding="utf-8")
    assert "Zażółć gęślą jaźń" in tekst and "Łódź" in tekst  # bez \uXXXX
    linie = wczytaj_jsonl(konfiguracja)
    assert len(linie) == 2
    assert linie[0]["producent"] == "—"  # surowe, bez czyszczenia
    assert linie[0]["waga"] == SZCZEGOLY["waga"]
    assert linie[1]["opis"] is None and "waga" in linie[1]  # błąd: 13 kluczy z None


def test_jsonl_nadpisywany_przy_nowym_przebiegu(konfiguracja):
    uruchom(AtrapaKatalogu({1: [pozycja("A"), pozycja("B")]}), AtrapaProduktu(), konfiguracja)
    uruchom(AtrapaKatalogu({1: [pozycja("C")]}), AtrapaProduktu(), konfiguracja)
    assert [r["id"] for r in wczytaj_jsonl(konfiguracja)] == ["C"]


def test_nierozpoznane_jeden_warning_na_rekord(konfiguracja, caplog):
    katalog = AtrapaKatalogu({1: [pozycja("A"), pozycja("B", ocena="pięć")]})
    produkt = AtrapaProduktu(szczegoly={"/produkt/B.html": {"waga": "12 lb"}})
    with caplog.at_level(logging.WARNING, logger="bajtoparser"):
        p = uruchom(katalog, produkt, konfiguracja)

    assert p.nierozpoznane == 2
    ostrzezenia = [r.message for r in caplog.records if "nierozpoznane" in r.message]
    assert len(ostrzezenia) == 1
    assert "B" in ostrzezenia[0] and "ocena" in ostrzezenia[0] and "waga" in ostrzezenia[0]


def test_podsumowanie_w_logu(konfiguracja, caplog):
    with caplog.at_level(logging.INFO, logger="bajtoparser"):
        uruchom(AtrapaKatalogu({1: [pozycja("A")]}), AtrapaProduktu(), konfiguracja)
    assert any(r.message.startswith("PODSUMOWANIE") for r in caplog.records)


def test_podsumowanie_ma_dane_dom_do_porownania(konfiguracja):
    katalog = AtrapaKatalogu(
        {
            1: [pozycja("A"), pozycja("B", zrodlo="karta")],
            2: [pozycja("A", zrodlo="karta"), pozycja("C")],
        }
    )
    p = uruchom(katalog, AtrapaProduktu(), konfiguracja, limit=2)
    assert p.podstrony_w_serwisie == 2
    assert p.pozycje_zrodlo == {"tabela": 2, "karta": 2}
    assert [r["id"] for r in p.probka_produktow] == ["A", "B"]  # po limit
    assert p.probka_produktow[0]["url"] == "/produkt/A.html"
