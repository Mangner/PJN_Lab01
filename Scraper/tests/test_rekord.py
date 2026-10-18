"""Testy czyszczenia całego rekordu i porównania duplikatów (bez przeglądarki)."""

import pytest

from bajtoparser.parsing.duplikaty import rozne_duplikaty
from bajtoparser.parsing.rekord import (
    KOLUMNY,
    KOLUMNY_CALKOWITE,
    KOLUMNY_ZMIENNOPRZECINKOWE,
    POLA_SZCZEGOLOW,
    czysc_rekord,
    nierozpoznane_pola,
    pola_listy,
)

NBSP = " "


def surowy_rekord(**zmiany):
    """Scalony surowy rekord (lista + szczegóły) w formacie zwracanym przez strony."""
    rekord = {
        "id": "P49235",
        "nazwa": "Słuchawki Żółw Bezprzewodowe",
        "url": "/produkt/P49235.html",
        "cena": f"1{NBSP}299,00{NBSP}zł",
        "waluta": "PLN",
        "cena_poprzednia": f"1{NBSP}499,00{NBSP}zł",
        "kategoria": "Audio",
        "producent": "Gęślarz",
        "dostepnosc": "dostępny",
        "gwarancja": "24 mies.",
        "ocena": "4,1",
        "liczba_opinii": "25",
        "data_dodania": "05.03.2026",
        "zrodlo": "tabela",
        "opis": "Opis z polskimi znakami: zażółć gęślą jaźń.",
        "ean": "0590123456789",
        "kod_producenta": "GX-12",
        "kolor": "czarny",
        "material": "tworzywo",
        "waga": f"1,47{NBSP}kg",
        "wymiary": f"17 x 9 x 8{NBSP}cm",
        "kraj_pochodzenia": "Polska",
        "sprzedawca": "Bajtomarket",
        "stan_magazynowy": "158 szt.",
        "czas_dostawy": "8 dni roboczych",
        "koszt_dostawy": "14,99 zł",
        "zwrot": "30 dni na zwrot",
    }
    rekord.update(zmiany)
    return rekord


def test_pelny_rekord():
    wynik = czysc_rekord(surowy_rekord())
    assert wynik["cena"] == 1299.0
    assert wynik["waluta"] == "PLN"
    assert wynik["cena_poprzednia"] == 1499.0
    assert wynik["gwarancja_mies"] == 24
    assert wynik["ocena"] == 4.1
    assert wynik["liczba_opinii"] == 25
    assert wynik["data_dodania"] == "2026-03-05"
    assert wynik["waga_kg"] == 1.47
    assert wynik["stan_magazynowy_szt"] == 158
    assert wynik["czas_dostawy_dni"] == 8
    assert wynik["koszt_dostawy"] == 14.99
    assert wynik["waluta_dostawy"] == "PLN"
    assert wynik["zwrot_dni"] == 30
    assert wynik["ean"] == "0590123456789"
    assert wynik["producent"] == "Gęślarz"
    assert wynik["zrodlo"] == "tabela"
    assert nierozpoznane_pola(surowy_rekord()) == []


def test_kolejnosc_kolumn_stala():
    assert list(czysc_rekord(surowy_rekord())) == KOLUMNY
    assert list(czysc_rekord({})) == KOLUMNY
    assert len(KOLUMNY) == len(set(KOLUMNY)) == 30
    assert (KOLUMNY_CALKOWITE | KOLUMNY_ZMIENNOPRZECINKOWE) <= set(KOLUMNY)


def test_wymiary_na_trzy_kolumny():
    wynik = czysc_rekord(surowy_rekord(wymiary="120 x 60,5 x 75 cm"))
    assert (wynik["szerokosc_cm"], wynik["wysokosc_cm"], wynik["glebokosc_cm"]) == (
        120.0,
        60.5,
        75.0,
    )
    assert "wymiary" not in wynik


@pytest.mark.parametrize("brak", ["—", "", None])
def test_brak_wymiarow_to_none_bez_nierozpoznanych(brak):
    surowy = surowy_rekord(wymiary=brak)
    wynik = czysc_rekord(surowy)
    assert wynik["szerokosc_cm"] is wynik["wysokosc_cm"] is wynik["glebokosc_cm"] is None
    assert nierozpoznane_pola(surowy) == []


def test_koszt_dostawy_gratis_to_zero_pln():
    wynik = czysc_rekord(surowy_rekord(koszt_dostawy="Gratis"))
    assert wynik["koszt_dostawy"] == 0.0
    assert wynik["waluta_dostawy"] == "PLN"


@pytest.mark.parametrize("brak", ["—", "", None])
def test_brak_promocji_nie_jest_nierozpoznany(brak):
    surowy = surowy_rekord(cena_poprzednia=brak)
    assert czysc_rekord(surowy)["cena_poprzednia"] is None
    assert nierozpoznane_pola(surowy) == []


def test_braki_myslnikiem_to_none():
    surowy = surowy_rekord(producent="—", ocena="—", gwarancja="—")
    wynik = czysc_rekord(surowy)
    assert wynik["producent"] is wynik["ocena"] is wynik["gwarancja_mies"] is None
    assert nierozpoznane_pola(surowy) == []


def test_rekord_bez_szczegolow():
    surowy = surowy_rekord(**dict.fromkeys(POLA_SZCZEGOLOW))
    wynik = czysc_rekord(surowy)
    assert wynik["cena"] == 1299.0
    assert all(
        wynik[k] is None
        for k in ("opis", "ean", "waga_kg", "szerokosc_cm", "koszt_dostawy", "waluta_dostawy")
    )
    assert nierozpoznane_pola(surowy) == []


def test_ceny_eur_i_usd():
    eur = czysc_rekord(surowy_rekord(cena="246,99 €", waluta="EUR", cena_poprzednia=""))
    usd = czysc_rekord(surowy_rekord(cena="$1,134.99", waluta="USD", cena_poprzednia="$1,299.00"))
    assert (eur["cena"], eur["waluta"]) == (246.99, "EUR")
    assert (usd["cena"], usd["waluta"], usd["cena_poprzednia"]) == (1134.99, "USD", 1299.0)


@pytest.mark.parametrize(
    ("pole", "wartosc"),
    [
        ("waga", "12 lb"),
        ("cena", "abc zł"),
        ("wymiary", "17 x 9 cm"),
        ("data_dodania", "2026-03-05"),
        ("stan_magazynowy", "dużo"),
        ("koszt_dostawy", "za darmo"),
    ],
)
def test_nierozpoznana_wartosc_jest_zgloszona(pole, wartosc):
    surowy = surowy_rekord(**{pole: wartosc})
    assert nierozpoznane_pola(surowy) == [pole]


def test_cena_poprzednia_w_innej_walucie_jest_nierozpoznana():
    surowy = surowy_rekord(cena_poprzednia="300,00 €")
    assert czysc_rekord(surowy)["cena_poprzednia"] is None
    assert nierozpoznane_pola(surowy) == ["cena_poprzednia"]


def test_pola_listy_bez_szczegolow_i_zrodla():
    pola = pola_listy(surowy_rekord())
    assert "zrodlo" not in pola and "opis" not in pola
    assert pola["id"] == "P49235"


def test_rozne_duplikaty_ignoruja_zapis_braku_promocji():
    tabela = surowy_rekord(cena_poprzednia="", zrodlo="tabela")
    karta = surowy_rekord(cena_poprzednia=None, zrodlo="karta")
    assert rozne_duplikaty([tabela, karta], porownywane=pola_listy) == []


def test_rozne_duplikaty_wykrywa_inna_cene():
    oryginal = surowy_rekord()
    inny = surowy_rekord(cena="999,00 zł")
    trzeci = surowy_rekord(cena="899,00 zł")
    inny_id = surowy_rekord(id="P1")
    wynik = rozne_duplikaty([oryginal, inny_id, inny, trzeci], porownywane=pola_listy)
    assert wynik == ["P49235"]
