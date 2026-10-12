"""Testy eksportu do CSV i JSON (pandas, bez przeglądarki)."""

import json

import pandas as pd
import pytest

from bajtoparser.eksport import eksportuj, ramka_danych
from bajtoparser.parsing.rekord import KOLUMNY, KOLUMNY_CALKOWITE, KOLUMNY_ZMIENNOPRZECINKOWE


def rekord(**pola):
    wynik = dict.fromkeys(KOLUMNY)
    wynik.update(pola)
    return wynik


@pytest.fixture
def rekordy():
    return [
        rekord(
            id="P1",
            nazwa="Zażółć gęślą jaźń",
            cena=1299.0,
            waluta="PLN",
            liczba_opinii=25,
            gwarancja_mies=24,
            koszt_dostawy=0.0,
            waluta_dostawy="PLN",
            data_dodania="2026-03-05",
            zrodlo="tabela",
        ),
        rekord(id="P2", nazwa="Łódź €", cena=246.99, waluta="EUR", zrodlo="karta"),
    ]


def test_typy_kolumn(rekordy):
    ramka = ramka_danych(rekordy)
    assert list(ramka.columns) == KOLUMNY
    for kolumna in KOLUMNY_ZMIENNOPRZECINKOWE:
        assert ramka[kolumna].dtype == "float64", kolumna
    for kolumna in KOLUMNY_CALKOWITE:
        assert str(ramka[kolumna].dtype) == "Int64", kolumna


def test_round_trip_csv(tmp_path, rekordy):
    csv, _ = eksportuj(rekordy, tmp_path, "wynik")
    surowe = csv.read_bytes()
    assert not surowe.startswith(b"\xef\xbb\xbf")  # bez BOM
    assert "Zażółć gęślą jaźń" in surowe.decode("utf-8")

    wczytane = pd.read_csv(csv, encoding="utf-8")
    assert list(wczytane.columns) == KOLUMNY
    assert len(wczytane) == 2
    for kolumna in KOLUMNY_CALKOWITE | KOLUMNY_ZMIENNOPRZECINKOWE:
        assert pd.api.types.is_numeric_dtype(wczytane[kolumna]), kolumna
    assert wczytane.loc[0, "cena"] == 1299.0
    assert wczytane.loc[0, "liczba_opinii"] == 25
    assert pd.isna(wczytane.loc[1, "liczba_opinii"])
    assert wczytane.loc[0, "koszt_dostawy"] == 0.0


def test_round_trip_json(tmp_path, rekordy):
    _, plik = eksportuj(rekordy, tmp_path, "wynik")
    tekst = plik.read_text(encoding="utf-8")
    assert "Zażółć gęślą jaźń" in tekst and "\\u" not in tekst  # force_ascii=False
    dane = json.loads(tekst)
    assert [list(r) for r in dane] == [KOLUMNY, KOLUMNY]
    assert dane[0]["cena"] == 1299.0
    assert dane[0]["liczba_opinii"] == 25 and isinstance(dane[0]["liczba_opinii"], int)
    assert dane[1]["liczba_opinii"] is None
    assert dane[1]["ocena"] is None
    assert dane[1]["nazwa"] == "Łódź €"


def test_tworzy_katalog(tmp_path, rekordy):
    csv, plik = eksportuj(rekordy, tmp_path / "nowy" / "katalog", "x")
    assert csv.exists() and plik.exists()
    assert (csv.name, plik.name) == ("x.csv", "x.json")
