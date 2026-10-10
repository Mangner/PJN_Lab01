#!/usr/bin/env python3
"""Generator serwisu Bajtomarket (Lab 1 PJN – rola AUTOR, poziom 5.0).

Uruchamiany RAZ. Tworzy kompletny serwis statyczny, który wystarczy podać dowolnym
serwerem plików (`python -m http.server`):

  index.html, strona-2.html … strona-6.html   – powłoki podstron katalogu (bez rekordów)
  produkt/<id>.html                           – własna strona każdego z 420 rekordów
  dane/katalog.json                           – metadane: podstrony, porcje, kategorie
  dane/strona-<n>-porcja-<k>.json             – porcje listy po 12 rekordów (36 plików)
  dane/produkt/<id>.json                      – pełny rekord ze szczegółami (420 plików)
  klucz/produkty_wzorcowe.csv                 – „klucz odpowiedzi” do sprawdzenia parsera
  klucz/duplikaty.csv                         – wykaz celowo zduplikowanych rekordów

Pliki pisane ręcznie (szablony HTML, CSS, JavaScript) leżą w `szablony/` i `statyczne/`
i nie są przez ten skrypt nadpisywane.

Uruchomienie:  python generuj_serwis.py [--ziarno 2026]
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import math
import random
import shutil
from pathlib import Path
from typing import NamedTuple

KATALOG_GLOWNY = Path(__file__).resolve().parent
DANE = KATALOG_GLOWNY / "dane"
KLUCZ = KATALOG_GLOWNY / "klucz"
SZABLONY = KATALOG_GLOWNY / "szablony"
STRONY_PRODUKTOW = KATALOG_GLOWNY / "produkt"

NBSP = " "
DATA_STANU = dt.date(2026, 10, 6)
NAJSTARSZA_DATA = dt.date(2025, 10, 1)
LICZBA_PRODUKTOW = 420
LICZBA_STRON = 6
LICZBA_DUPLIKATOW = 12
ROZMIAR_PORCJI = 12
KURSY_WALUT = {"PLN": 1.0, "EUR": 4.28, "USD": 3.92}

# Utrudnienie nr 2: braki wartości w dwóch polach u ponad 15% rekordów.
BRAKI = {"producent": 0.17, "ocena": 0.20, "waga_kg": 0.06, "gwarancja_mies": 0.05}
# Utrudnienie nr 1: część cen w innej walucie niż złoty.
UDZIAL_WALUT = {"EUR": 0.09, "USD": 0.06}
UDZIAL_PROMOCJI = 0.22


class Typ(NamedTuple):
    nazwa: str
    cena: tuple[float, float]
    waga: tuple[float, float]
    wymiary: tuple[int, int, int]
    materialy: list[str]
    warianty: list[str] = []


KATEGORIE = {
    "AGD": {
        "producenci": ["Zefir", "Domovit", "Bryza", "Kowalski i Syn", "Arktis"],
        "cechy": ["niezawodność", "prostą obsługę", "energooszczędność", "cichą pracę", "nowoczesny wygląd"],
        "zastosowanie": "codziennej pracy w kuchni i w domu",
        "gwarancje": [12, 24, 24, 24, 36],
        "typy": [
            Typ("Czajnik elektryczny", (79, 399), (0.9, 1.8), (22, 25, 16), ["stal nierdzewna", "szkło borokrzemowe", "tworzywo sztuczne"], ["1,7 l", "1,5 l", "1,2 l"]),
            Typ("Ekspres do kawy", (349, 3999), (4.0, 11.0), (24, 36, 42), ["tworzywo sztuczne", "stal nierdzewna"]),
            Typ("Odkurzacz pionowy", (399, 2499), (2.2, 3.5), (25, 112, 22), ["tworzywo sztuczne", "aluminium"]),
            Typ("Blender kielichowy", (129, 899), (2.0, 4.5), (18, 42, 20), ["szkło", "tworzywo Tritan", "stal nierdzewna"], ["1000 W", "1200 W", "1500 W"]),
            Typ("Toster", (69, 449), (1.0, 2.2), (28, 19, 17), ["stal nierdzewna", "tworzywo sztuczne"], ["2 kromki", "4 kromki"]),
            Typ("Frytkownica beztłuszczowa", (199, 899), (3.5, 7.0), (30, 32, 36), ["tworzywo sztuczne", "stal nierdzewna"], ["3,5 l", "5,5 l", "8 l"]),
        ],
    },
    "RTV i audio": {
        "producenci": ["Sonora", "Volta Audio", "Pixelium", "Echo-Lab", "Nordis"],
        "cechy": ["czysty dźwięk", "głęboki bas", "intuicyjne sterowanie", "długi czas pracy", "elegancki wygląd"],
        "zastosowanie": "słuchaniu muzyki i oglądaniu filmów",
        "gwarancje": [12, 24, 24, 36],
        "typy": [
            Typ("Słuchawki bezprzewodowe", (99, 1499), (0.15, 0.4), (17, 19, 8), ["tworzywo sztuczne", "aluminium", "skóra ekologiczna"], ["ANC", "nauszne", "douszne"]),
            Typ("Głośnik Bluetooth", (79, 1299), (0.3, 2.5), (18, 8, 8), ["tkanina akustyczna", "aluminium", "silikon"], ["10 W", "20 W", "40 W"]),
            Typ("Soundbar", (399, 3999), (2.0, 7.0), (90, 7, 10), ["aluminium", "tworzywo sztuczne"], ["2.1", "3.1", "5.1"]),
            Typ("Telewizor LED", (1299, 8999), (6.0, 25.0), (97, 57, 8), ["tworzywo sztuczne", "aluminium"], ["43 cale", "50 cali", "55 cali", "65 cali"]),
            Typ("Projektor", (499, 5999), (1.5, 4.5), (30, 11, 23), ["tworzywo sztuczne"], ["Full HD", "4K"]),
        ],
    },
    "Komputery": {
        "producenci": ["TechNova", "Kwant", "Pixelium", "Bajtex", "Orion Systems"],
        "cechy": ["wysoką wydajność", "lekką konstrukcję", "długi czas pracy na baterii", "solidne wykonanie", "ciche chłodzenie"],
        "zastosowanie": "pracy biurowej, nauce i rozrywce",
        "gwarancje": [12, 24, 24, 36],
        "typy": [
            Typ("Laptop", (1999, 9999), (1.1, 2.6), (36, 2, 24), ["aluminium", "tworzywo sztuczne", "stop magnezu"], ["14 cali", "15,6 cala", "16 cali"]),
            Typ("Monitor", (499, 3999), (3.0, 8.0), (61, 45, 20), ["tworzywo sztuczne", "aluminium"], ["24 cale", "27 cali", "32 cale"]),
            Typ("Klawiatura mechaniczna", (149, 899), (0.6, 1.3), (44, 4, 14), ["aluminium", "tworzywo ABS", "tworzywo PBT"], ["TKL", "75%", "pełnowymiarowa"]),
            Typ("Mysz bezprzewodowa", (39, 499), (0.06, 0.14), (7, 4, 12), ["tworzywo sztuczne"]),
            Typ("Dysk SSD", (129, 1299), (0.01, 0.06), (8, 1, 2), ["aluminium", "laminat"], ["500 GB", "1 TB", "2 TB", "4 TB"]),
            Typ("Router Wi-Fi", (119, 1499), (0.3, 1.2), (24, 5, 15), ["tworzywo sztuczne"], ["Wi-Fi 6", "Wi-Fi 6E", "Wi-Fi 7"]),
        ],
    },
    "Telefony i akcesoria": {
        "producenci": ["Kometa", "Volta", "Iskra Mobile", "TechNova", "Lumen"],
        "cechy": ["wydajny procesor", "jasny ekran", "pojemną baterię", "szybkie ładowanie", "smukłą obudowę"],
        "zastosowanie": "codziennej komunikacji i podróżach",
        "gwarancje": [12, 24, 24],
        "typy": [
            Typ("Smartfon", (499, 6999), (0.15, 0.24), (7, 16, 1), ["aluminium", "szkło", "tworzywo sztuczne"], ["128 GB", "256 GB", "512 GB"]),
            Typ("Smartwatch", (199, 2499), (0.03, 0.07), (4, 4, 1), ["aluminium", "stal nierdzewna", "silikon"]),
            Typ("Powerbank", (59, 399), (0.18, 0.5), (7, 15, 2), ["aluminium", "tworzywo sztuczne"], ["10000 mAh", "20000 mAh", "26800 mAh"]),
            Typ("Ładowarka sieciowa", (39, 249), (0.05, 0.25), (5, 6, 3), ["tworzywo sztuczne"], ["20 W", "45 W", "65 W", "100 W"]),
            Typ("Etui ochronne", (19, 149), (0.02, 0.08), (8, 16, 1), ["silikon", "skóra naturalna", "poliwęglan"]),
        ],
    },
    "Dom i ogród": {
        "producenci": ["Ogrodex", "Lumena", "Żuraw", "Granit", "Kowalski i Syn"],
        "cechy": ["trwałość", "odporność na warunki atmosferyczne", "łatwy montaż", "funkcjonalność", "klasyczny wygląd"],
        "zastosowanie": "pracach w domu i w ogrodzie",
        "gwarancje": [12, 24, 24, 36],
        "typy": [
            Typ("Lampa stojąca", (149, 1199), (3.0, 8.0), (40, 160, 40), ["metal", "drewno", "len"]),
            Typ("Grill węglowy", (199, 1999), (8.0, 35.0), (60, 100, 55), ["stal emaliowana", "żeliwo"], ["średnica 47 cm", "średnica 57 cm"]),
            Typ("Kosiarka elektryczna", (399, 2499), (10.0, 28.0), (40, 40, 140), ["stal", "tworzywo sztuczne"], ["1400 W", "1800 W"]),
            Typ("Sekator", (39, 249), (0.2, 0.5), (6, 22, 2), ["stal hartowana", "aluminium"]),
            Typ("Krzesło ogrodowe", (99, 699), (3.0, 9.0), (55, 90, 60), ["drewno akacjowe", "technorattan", "aluminium"]),
        ],
    },
    "Sport i turystyka": {
        "producenci": ["Wisła Sport", "Łoś Outdoor", "Tatra", "Sprint", "Hartex"],
        "cechy": ["wygodę", "wytrzymałość", "niską wagę", "ergonomię", "bezpieczeństwo"],
        "zastosowanie": "treningu i aktywnym wypoczynku",
        "gwarancje": [12, 24, 24, 36],
        "typy": [
            Typ("Rower trekkingowy", (1499, 6999), (13.0, 18.0), (65, 105, 175), ["aluminium", "stal chromowo-molibdenowa"], ["rama S", "rama M", "rama L"]),
            Typ("Hantle regulowane", (149, 1499), (5.0, 24.0), (40, 20, 20), ["stal", "żeliwo"], ["2 x 10 kg", "2 x 20 kg"]),
            Typ("Mata do jogi", (49, 349), (0.8, 2.5), (61, 1, 183), ["TPE", "kauczuk naturalny", "korek"], ["4 mm", "6 mm"]),
            Typ("Plecak turystyczny", (129, 899), (0.9, 2.2), (32, 60, 22), ["poliester", "nylon ripstop"], ["30 l", "45 l", "65 l"]),
            Typ("Namiot dwuosobowy", (249, 1999), (1.6, 4.5), (45, 15, 15), ["poliester", "nylon"]),
            Typ("Kask rowerowy", (89, 699), (0.2, 0.4), (20, 15, 27), ["EPS", "poliwęglan"], ["S", "M", "L"]),
        ],
    },
    "Zabawki": {
        "producenci": ["Bajkowo", "Klocuś", "Planszomania", "Turbo Toys", "Misiaczek"],
        "cechy": ["bezpieczne materiały", "rozwój kreatywności", "solidne wykonanie", "długą zabawę", "kolorowy design"],
        "zastosowanie": "wspólnej zabawie dzieci i dorosłych",
        "gwarancje": [12, 24],
        "typy": [
            Typ("Klocki konstrukcyjne", (49, 899), (0.3, 3.0), (38, 26, 7), ["tworzywo ABS"], ["250 el.", "500 el.", "1200 el."]),
            Typ("Puzzle", (29, 129), (0.4, 1.2), (34, 25, 5), ["tektura"], ["500 el.", "1000 el.", "2000 el."]),
            Typ("Gra planszowa", (59, 349), (0.6, 2.2), (30, 30, 8), ["tektura", "drewno"]),
            Typ("Samochód zdalnie sterowany", (99, 799), (0.5, 2.5), (35, 15, 20), ["tworzywo sztuczne", "metal"], ["skala 1:16", "skala 1:10"]),
            Typ("Pluszowy miś", (39, 299), (0.2, 1.0), (25, 40, 20), ["plusz", "poliester"], ["30 cm", "50 cm", "80 cm"]),
        ],
    },
    "Narzędzia": {
        "producenci": ["Tytan", "Hartex", "Orzeł Tools", "Granit", "Volta"],
        "cechy": ["dużą moc", "precyzję", "ergonomiczny uchwyt", "odporność na zużycie", "bezpieczeństwo pracy"],
        "zastosowanie": "domowych remontach i pracach warsztatowych",
        "gwarancje": [24, 24, 36, 60],
        "typy": [
            Typ("Wiertarka udarowa", (149, 1299), (1.5, 3.0), (28, 24, 8), ["tworzywo sztuczne", "metal"], ["750 W", "1100 W"]),
            Typ("Wkrętarka akumulatorowa", (199, 1499), (1.0, 2.0), (20, 22, 7), ["tworzywo sztuczne"], ["12 V", "18 V"]),
            Typ("Szlifierka kątowa", (129, 999), (1.8, 3.2), (30, 10, 12), ["tworzywo sztuczne", "aluminium"], ["125 mm", "230 mm"]),
            Typ("Zestaw kluczy", (79, 799), (1.5, 9.0), (40, 8, 25), ["stal chromowo-wanadowa"], ["94 el.", "108 el.", "216 el."]),
            Typ("Poziomica laserowa", (129, 1499), (0.4, 1.2), (12, 12, 7), ["tworzywo sztuczne", "aluminium"]),
        ],
    },
    "Kuchnia": {
        "producenci": ["Smakosz", "Granit", "Kuchcik", "Stalwar", "Kowalski i Syn"],
        "cechy": ["równomierne nagrzewanie", "łatwe czyszczenie", "trwałą powłokę", "wygodny uchwyt", "elegancki wygląd"],
        "zastosowanie": "przygotowywaniu codziennych posiłków",
        "gwarancje": [12, 24, 24, 60],
        "typy": [
            Typ("Patelnia", (59, 599), (0.8, 2.2), (28, 6, 48), ["aluminium", "stal nierdzewna", "żeliwo"], ["średnica 24 cm", "średnica 28 cm"]),
            Typ("Zestaw garnków", (199, 2499), (4.0, 12.0), (50, 30, 40), ["stal nierdzewna", "emalia"], ["5 el.", "8 el.", "12 el."]),
            Typ("Nóż szefa kuchni", (49, 899), (0.15, 0.35), (5, 3, 33), ["stal damasceńska", "stal nierdzewna", "ceramika"], ["20 cm"]),
            Typ("Deska do krojenia", (29, 249), (0.5, 2.5), (40, 2, 28), ["drewno bukowe", "bambus", "tworzywo sztuczne"]),
            Typ("Waga kuchenna", (39, 199), (0.4, 1.0), (20, 2, 16), ["szkło hartowane", "stal nierdzewna"]),
        ],
    },
    "Zdrowie i uroda": {
        "producenci": ["Bella", "Lumen", "Zefir", "Sensi", "Medica"],
        "cechy": ["delikatność", "skuteczność", "wygodę użytkowania", "nowoczesną technologię", "kompaktowe wymiary"],
        "zastosowanie": "codziennej pielęgnacji",
        "gwarancje": [12, 24, 24],
        "typy": [
            Typ("Suszarka do włosów", (79, 1999), (0.4, 0.9), (25, 24, 9), ["tworzywo sztuczne"], ["2000 W", "2400 W"]),
            Typ("Szczoteczka soniczna", (99, 899), (0.1, 0.3), (3, 25, 3), ["tworzywo sztuczne"]),
            Typ("Waga łazienkowa", (49, 399), (1.0, 2.5), (30, 3, 30), ["szkło hartowane", "tworzywo sztuczne"]),
            Typ("Prostownica", (79, 899), (0.3, 0.6), (4, 30, 4), ["ceramika", "tytan"]),
            Typ("Golarka elektryczna", (129, 1499), (0.15, 0.4), (6, 16, 5), ["tworzywo sztuczne", "aluminium"]),
        ],
    },
}

LINIE = ["Aurora", "Bryza", "Nimbus", "Orion", "Wega", "Atlas", "Zenit", "Fala", "Iskra", "Mistral",
         "Pulsar", "Lira", "Sokół", "Żagiel", "Świt", "Łuna", "Halny", "Perła", "Topaz", "Rubin",
         "Jantar", "Granat", "Sirius", "Kosmo", "Tęcza", "Wir", "Szafir", "Echo"]
SUFIKSY = ["", "", "", " Pro", " Max", " Mini", " Lite", " Plus", " Eco", " 2.0", " X", " Ultra"]
LITERY_KODU = "ABCDEFGHKLMNPRSTVXZ"
KOLORY = ["czarny", "biały", "grafitowy", "srebrny", "czerwony", "granatowy", "zielony", "beżowy",
          "szary", "niebieski", "miętowy", "różowy", "złoty", "inox"]
KRAJE = [("Polska", 30), ("Chiny", 25), ("Niemcy", 10), ("Czechy", 7), ("Wietnam", 7), ("Tajwan", 6),
         ("Włochy", 5), ("Turcja", 4), ("Słowacja", 3), ("Korea Południowa", 3)]
SPRZEDAWCY = [("Bajtomarket", 50), ("Hurtownia Wisła", 12), ("MegaDom", 12), ("Elektro-Świat", 10),
              ("Outlet Mazury", 8), ("Sklep firmowy Kowalski", 8)]
DOSTEPNOSC = [("dostępny", 62), ("ostatnie sztuki", 12), ("na zamówienie", 14), ("niedostępny", 12)]
CZAS_DOSTAWY = {"dostępny": (1, 3), "ostatnie sztuki": (1, 5), "na zamówienie": (7, 21), "niedostępny": (14, 30)}
ZWROTY = [14, 30, 30, 30, 100]
POLSKIE_NA_ASCII = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")

ZDANIA_OTWIERAJACE = [
    "{typ} {linia} to propozycja dla osób, które cenią {c1} i {c2}.",
    "W modelu {linia} postawiliśmy na {c1} i {c2}.",
    "{typ} z serii {linia} zaprojektowano z myślą o {zast}.",
    "Klienci doceniają model {linia} przede wszystkim za {c1} i {c2}.",
]
ZDANIA_ZAMYKAJACE = [
    "Tak ten produkt oceniają nasi klienci: najlepszy zakup w tej cenie.",
    "W zestawie instrukcja w języku polskim.",
    "Kolory na zdjęciach mogą nieznacznie różnić się od rzeczywistych.",
    "Produkt dostępny także w innych wariantach - zapytaj sprzedawcę.",
]


# ───────────────────────────── generowanie rekordów ─────────────────────────────

def wybierz_wazone(los: random.Random, pary):
    return los.choices([wartosc for wartosc, _ in pary], weights=[waga for _, waga in pary])[0]


def zaokraglij_pln(los: random.Random, kwota: float) -> float:
    baza = max(9, round(kwota / 10) * 10 - 1)
    return round(baza + los.choice([0.0, 0.0, 0.99]), 2)


def zaokraglij_obca(kwota: float) -> float:
    return round(max(1, round(kwota)) - 0.01, 2)


def ean13(los: random.Random) -> str:
    cyfry = [5, 9, 0] + [los.randint(0, 9) for _ in range(9)]
    suma = sum(c * (3 if i % 2 else 1) for i, c in enumerate(cyfry))
    return "".join(map(str, cyfry)) + str((10 - suma % 10) % 10)


def liczba_pl(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def generuj_produkt(los: random.Random, numer: int, nazwa_kat: str, kat: dict, typ: Typ, nazwy: set) -> dict:
    producent = los.choice(kat["producenci"])
    while True:
        linia = los.choice(LINIE)
        kod = f"{los.choice(LITERY_KODU)}{los.randint(1, 99) * 10}"
        nazwa = f"{typ.nazwa} {linia}{los.choice(SUFIKSY)} {kod}"
        if typ.warianty and los.random() < 0.7:
            nazwa += f", {los.choice(typ.warianty)}"
        if nazwa not in nazwy:
            break
    nazwy.add(nazwa)

    # t – położenie ceny w przedziale typu; wpływa też na wagę i liczbę opinii,
    # dzięki czemu w danych są sensowne korelacje do części statystycznej.
    t = los.random()
    cena_min, cena_max = typ.cena
    cena = zaokraglij_pln(los, math.exp(math.log(cena_min) + t * (math.log(cena_max) - math.log(cena_min))))
    cena_poprzednia = zaokraglij_pln(los, cena * los.uniform(1.1, 1.4)) if los.random() < UDZIAL_PROMOCJI else None

    dostepnosc = wybierz_wazone(los, DOSTEPNOSC)
    stan = {"dostępny": los.randint(5, 250), "ostatnie sztuki": los.randint(1, 4)}.get(dostepnosc, 0)
    waga = round(typ.waga[0] + (typ.waga[1] - typ.waga[0]) * (0.35 * t + 0.65 * los.random()), 2)
    wymiary = [max(1, round(bok * los.uniform(0.85, 1.2))) for bok in typ.wymiary]

    data = NAJSTARSZA_DATA + dt.timedelta(days=los.randint(0, (DATA_STANU - NAJSTARSZA_DATA).days))

    if waga > 10:
        koszt_dostawy = los.choice([49.0, 79.0])
    elif cena >= 300 and los.random() < 0.8:
        koszt_dostawy = 0.0
    else:
        koszt_dostawy = los.choice([9.99, 12.99, 14.99])

    return {
        "id": f"P{numer}",
        "nazwa": nazwa,
        "kategoria": nazwa_kat,
        "producent": producent,
        "cena": cena,
        "waluta": "PLN",
        "cena_poprzednia": cena_poprzednia,
        "dostepnosc": dostepnosc,
        "stan_magazynowy": stan,
        "ocena": round(min(5.0, max(1.0, los.gauss(4.2, 0.55))), 1),
        "liczba_opinii": max(1, int(los.lognormvariate(3.6 - 1.2 * t, 1.1))),
        "data_dodania": data.isoformat(),
        "gwarancja_mies": los.choice(kat["gwarancje"]),
        "ean": ean13(los),
        "kod_producenta": f"{producent.translate(POLSKIE_NA_ASCII)[:3].upper()}-{kod}-{los.randint(1000, 9999)}",
        "kolor": los.choice(KOLORY),
        "material": los.choice(typ.materialy),
        "waga_kg": waga,
        "wymiary_cm": {"szerokosc": wymiary[0], "wysokosc": wymiary[1], "glebokosc": wymiary[2]},
        "kraj_pochodzenia": wybierz_wazone(los, KRAJE),
        "sprzedawca": wybierz_wazone(los, SPRZEDAWCY),
        "czas_dostawy_dni": los.randint(*CZAS_DOSTAWY[dostepnosc]),
        "koszt_dostawy": koszt_dostawy,
        "zwrot_dni": los.choice(ZWROTY),
        "_typ": typ,
        "_kat": kat,
        "_linia": linia,
    }


def wprowadz_braki(los: random.Random, produkty: list[dict]) -> None:
    for pole, udzial in BRAKI.items():
        for produkt in los.sample(produkty, round(len(produkty) * udzial)):
            produkt[pole] = None
            if pole == "ocena":
                produkt["liczba_opinii"] = 0


def wprowadz_waluty(los: random.Random, produkty: list[dict]) -> None:
    kolejnosc = list(produkty)
    los.shuffle(kolejnosc)
    poczatek = 0
    for waluta, udzial in UDZIAL_WALUT.items():
        liczba = round(len(produkty) * udzial)
        kurs = KURSY_WALUT[waluta]
        for produkt in kolejnosc[poczatek:poczatek + liczba]:
            produkt["waluta"] = waluta
            produkt["cena"] = zaokraglij_obca(produkt["cena"] / kurs)
            if produkt["cena_poprzednia"] is not None:
                poprzednia = zaokraglij_obca(produkt["cena_poprzednia"] / kurs)
                produkt["cena_poprzednia"] = poprzednia if poprzednia > produkt["cena"] else None
        poczatek += liczba


def wprowadz_odstajace(los: random.Random, produkty: list[dict]) -> None:
    """Dwie prawdziwe anomalie – do odróżnienia w analizie od błędu parsera."""
    ekspresy = [p for p in produkty if p["_typ"].nazwa == "Ekspres do kawy" and p["waluta"] == "PLN"]
    if ekspresy:
        produkt = los.choice(ekspresy)
        produkt.update(cena=24999.0, cena_poprzednia=None, waga_kg=38.5, koszt_dostawy=149.0)
        produkt["nazwa"] += " - wersja profesjonalna"
    powerbanki = [p for p in produkty if p["_typ"].nazwa == "Powerbank" and p["ocena"] is not None]
    if powerbanki:
        los.choice(powerbanki).update(ocena=4.8, liczba_opinii=12480)


def generuj_opis(los: random.Random, produkt: dict) -> str:
    typ, kat, linia = produkt["_typ"], produkt["_kat"], produkt["_linia"]
    c1, c2 = los.sample(kat["cechy"], 2)
    wymiary = produkt["wymiary_cm"]
    otwarcie = los.choice(ZDANIA_OTWIERAJACE).format(
        typ=typ.nazwa, linia=linia, c1=c1, c2=c2, zast=kat["zastosowanie"])
    srodek = [
        f"Materiał: {produkt['material']}, wymiary {wymiary['szerokosc']} x {wymiary['wysokosc']}"
        f" x {wymiary['glebokosc']} cm.",
        f"Wariant kolorystyczny: {produkt['kolor']}.",
        f"Sprawdzi się przy {kat['zastosowanie']}.",
    ]
    if produkt["waga_kg"] is not None:
        srodek.append(f"Waga produktu to około {liczba_pl(produkt['waga_kg'])} kg.")
    zamkniecia = list(ZDANIA_ZAMYKAJACE)
    if produkt["gwarancja_mies"] is not None:
        zamkniecia.append(f"Gwarancja producenta: {produkt['gwarancja_mies']} mies.")
    return " ".join([otwarcie, *los.sample(srodek, 2), los.choice(zamkniecia)])


def generuj_produkty(los: random.Random) -> list[dict]:
    kategorie = list(KATEGORIE.items())
    plan = [kategorie[i % len(kategorie)] for i in range(LICZBA_PRODUKTOW)]
    los.shuffle(plan)
    numery = los.sample(range(10000, 100000), LICZBA_PRODUKTOW)
    nazwy: set[str] = set()
    produkty = [generuj_produkt(los, numer, nazwa_kat, kat, los.choice(kat["typy"]), nazwy)
                for numer, (nazwa_kat, kat) in zip(numery, plan)]
    wprowadz_braki(los, produkty)
    wprowadz_waluty(los, produkty)
    wprowadz_odstajace(los, produkty)
    for produkt in produkty:
        produkt["_opis"] = generuj_opis(los, produkt)
    return produkty


def podziel_na_strony(los: random.Random, produkty: list[dict]):
    """Rozdziela rekordy na podstrony i rozrzuca po nich 12 duplikatów (utrudnienie nr 3)."""
    identyfikatory = [p["id"] for p in produkty]
    los.shuffle(identyfikatory)
    na_strone = len(identyfikatory) // LICZBA_STRON
    strony = [identyfikatory[i * na_strone:(i + 1) * na_strone] for i in range(LICZBA_STRON)]
    strony[-1].extend(identyfikatory[LICZBA_STRON * na_strone:])

    wybrane = [(strony[indeks // na_strone][indeks % na_strone], indeks // na_strone)
               for indeks in los.sample(range(LICZBA_STRON * na_strone), LICZBA_DUPLIKATOW)]
    otrzymane = [0] * LICZBA_STRON
    duplikaty = []
    for identyfikator, zrodlo in wybrane:
        cele = [strona for strona in range(LICZBA_STRON) if strona != zrodlo]
        najmniej = min(otrzymane[strona] for strona in cele)
        cel = los.choice([strona for strona in cele if otrzymane[strona] == najmniej])
        otrzymane[cel] += 1
        strony[cel].insert(los.randint(1, len(strony[cel])), identyfikator)
        duplikaty.append((identyfikator, zrodlo + 1, cel + 1))
    return strony, duplikaty


# ───────────────────────────── formy prezentacyjne ─────────────────────────────

def formatuj_cene(kwota: float, waluta: str) -> str:
    """Utrudnienie nr 1: trzy konwencje zapisu - „1 299,00 zł”, „303,99 €”, „$1,299.99”."""
    if waluta == "USD":
        return f"${kwota:,.2f}"
    tekst = f"{kwota:,.2f}".replace(",", NBSP).replace(".", ",")
    return f"{tekst}{NBSP}{'zł' if waluta == 'PLN' else '€'}"


def formatuj_date(data_iso: str) -> str:
    data = dt.date.fromisoformat(data_iso)
    return f"{data.day:02d}.{data.month:02d}.{data.year}"


def widok_listy(produkt: dict) -> dict:
    """13 atrybutów widocznych na liście katalogu."""
    ocena = produkt["ocena"]
    return {
        "id": produkt["id"],
        "url": f"produkt/{produkt['id']}.html",
        "nazwa": produkt["nazwa"],
        "kategoria": produkt["kategoria"],
        "producent": produkt["producent"],
        "cena_tekst": formatuj_cene(produkt["cena"], produkt["waluta"]),
        "cena_poprzednia_tekst": (formatuj_cene(produkt["cena_poprzednia"], produkt["waluta"])
                                  if produkt["cena_poprzednia"] is not None else None),
        "waluta": produkt["waluta"],
        "dostepnosc": produkt["dostepnosc"],
        "ocena_tekst": f"{ocena:.1f}".replace(".", ",") if ocena is not None else None,
        "liczba_opinii": produkt["liczba_opinii"],
        "data_tekst": formatuj_date(produkt["data_dodania"]),
        "gwarancja_tekst": f"{produkt['gwarancja_mies']} mies." if produkt["gwarancja_mies"] is not None else None,
    }


def widok_szczegolow(produkt: dict) -> dict:
    """Powyższe 13 atrybutów plus 13 dostępnych wyłącznie na stronie produktu."""
    wymiary = produkt["wymiary_cm"]
    waga = produkt["waga_kg"]
    return widok_listy(produkt) | {
        "ean": produkt["ean"],
        "stan_magazynowy": produkt["stan_magazynowy"],
        "sprzedawca": produkt["sprzedawca"],
        "opis": produkt["_opis"],
        "kod_producenta": produkt["kod_producenta"],
        "kolor": produkt["kolor"],
        "material": produkt["material"],
        "waga_tekst": f"{liczba_pl(waga)}{NBSP}kg" if waga is not None else None,
        "wymiary_tekst": f"{wymiary['szerokosc']} x {wymiary['wysokosc']} x {wymiary['glebokosc']}{NBSP}cm",
        "kraj_pochodzenia": produkt["kraj_pochodzenia"],
        "czas_dostawy_tekst": f"{produkt['czas_dostawy_dni']} dni roboczych",
        "koszt_dostawy_tekst": ("gratis" if produkt["koszt_dostawy"] == 0
                                else formatuj_cene(produkt["koszt_dostawy"], "PLN")),
        "zwrot_tekst": f"{produkt['zwrot_dni']} dni na zwrot",
    }


# ───────────────────────────── zapis serwisu ─────────────────────────────

def adres_strony(numer: int) -> str:
    return "index.html" if numer == 1 else f"strona-{numer}.html"


def zapisz_json(sciezka: Path, dane) -> None:
    sciezka.parent.mkdir(parents=True, exist_ok=True)
    sciezka.write_text(json.dumps(dane, ensure_ascii=False, indent=1), encoding="utf-8")


def zapisz_dane(produkty: dict[str, dict], strony: list[list[str]]) -> int:
    """Porcje listy (po 12 rekordów) oraz pełne rekordy pojedynczych produktów."""
    if DANE.exists():
        shutil.rmtree(DANE)
    porcji_lacznie = []
    for numer, identyfikatory in enumerate(strony, start=1):
        porcje = [identyfikatory[i:i + ROZMIAR_PORCJI] for i in range(0, len(identyfikatory), ROZMIAR_PORCJI)]
        porcji_lacznie.append(len(porcje))
        for kolejna, porcja in enumerate(porcje, start=1):
            zapisz_json(DANE / f"strona-{numer}-porcja-{kolejna}.json", {
                "strona": numer,
                "porcja": kolejna,
                "porcji_lacznie": len(porcje),
                "od": (kolejna - 1) * ROZMIAR_PORCJI,
                "ile": len(porcja),
                "razem": len(identyfikatory),
                "produkty": [widok_listy(produkty[i]) for i in porcja],
            })
    for produkt in produkty.values():
        zapisz_json(DANE / "produkt" / f"{produkt['id']}.json", widok_szczegolow(produkt))

    zapisz_json(DANE / "katalog.json", {
        "serwis": "Bajtomarket",
        "opis": "Fikcyjne dane wygenerowane na potrzeby Laboratorium nr 1 (PJN).",
        "data_stanu": DATA_STANU.isoformat(),
        "liczba_produktow": len(produkty),
        "rozmiar_porcji": ROZMIAR_PORCJI,
        "kategorie": sorted({p["kategoria"] for p in produkty.values()}),
        "strony": [{"numer": numer, "adres": adres_strony(numer),
                    "pozycji": len(identyfikatory), "porcji": porcji_lacznie[numer - 1]}
                   for numer, identyfikatory in enumerate(strony, start=1)],
    })
    return sum(porcji_lacznie)


def zapisz_strony(produkty: dict[str, dict], strony: list[list[str]]) -> None:
    """Powłoki HTML - ani jedna nie zawiera rekordu, mają tylko numer strony albo identyfikator."""
    szablon_katalogu = (SZABLONY / "katalog.html").read_text(encoding="utf-8")
    szablon_produktu = (SZABLONY / "produkt.html").read_text(encoding="utf-8")

    for numer in range(1, len(strony) + 1):
        tresc = (szablon_katalogu
                 .replace("{{PODSTRONA}}", str(numer))
                 .replace("{{STRON_LACZNIE}}", str(len(strony))))
        (KATALOG_GLOWNY / adres_strony(numer)).write_text(tresc, encoding="utf-8")

    if STRONY_PRODUKTOW.exists():
        shutil.rmtree(STRONY_PRODUKTOW)
    STRONY_PRODUKTOW.mkdir()
    for identyfikator in produkty:
        tresc = szablon_produktu.replace("{{IDENTYFIKATOR}}", identyfikator)
        (STRONY_PRODUKTOW / f"{identyfikator}.html").write_text(tresc, encoding="utf-8")


def zapisz_klucz(produkty: dict[str, dict], strony: list[list[str]], duplikaty) -> None:
    KLUCZ.mkdir(exist_ok=True)
    wystapienia: dict[str, list[str]] = {}
    for numer, identyfikatory in enumerate(strony, start=1):
        for identyfikator in identyfikatory:
            wystapienia.setdefault(identyfikator, []).append(str(numer))

    kolumny = ["id", "nazwa", "url", "kategoria", "producent", "cena", "waluta", "cena_pln",
               "cena_poprzednia", "dostepnosc", "stan_magazynowy", "ocena", "liczba_opinii",
               "data_dodania", "gwarancja_mies", "ean", "opis", "kod_producenta", "kolor", "material",
               "waga_kg", "wymiary_cm", "kraj_pochodzenia", "sprzedawca", "czas_dostawy_dni",
               "koszt_dostawy_pln", "zwrot_dni", "strony"]
    with open(KLUCZ / "produkty_wzorcowe.csv", "w", newline="", encoding="utf-8-sig") as plik:
        zapis = csv.DictWriter(plik, fieldnames=kolumny)
        zapis.writeheader()
        for produkt in produkty.values():
            wymiary = produkt["wymiary_cm"]
            zapis.writerow({
                **{k: produkt[k] for k in kolumny if k in produkt},
                "url": f"produkt/{produkt['id']}.html",
                "cena_pln": round(produkt["cena"] * KURSY_WALUT[produkt["waluta"]], 2),
                "opis": produkt["_opis"],
                "wymiary_cm": f"{wymiary['szerokosc']}x{wymiary['wysokosc']}x{wymiary['glebokosc']}",
                "koszt_dostawy_pln": produkt["koszt_dostawy"],
                "strony": ";".join(wystapienia[produkt["id"]]),
            })

    with open(KLUCZ / "duplikaty.csv", "w", newline="", encoding="utf-8-sig") as plik:
        zapis = csv.writer(plik)
        zapis.writerow(["id", "nazwa", "strona_pierwotna", "strona_duplikatu"])
        for identyfikator, zrodlo, cel in duplikaty:
            zapis.writerow([identyfikator, produkty[identyfikator]["nazwa"], zrodlo, cel])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generator serwisu Bajtomarket.")
    parser.add_argument("--ziarno", type=int, default=2026, help="ziarno generatora (domyślnie 2026)")
    args = parser.parse_args()

    los = random.Random(args.ziarno)
    lista = generuj_produkty(los)
    strony, duplikaty = podziel_na_strony(los, lista)
    produkty = {p["id"]: p for p in lista}

    porcji = zapisz_dane(produkty, strony)
    zapisz_strony(produkty, strony)
    zapisz_klucz(produkty, strony, duplikaty)

    pozycje = sum(len(s) for s in strony)
    print(f"Rekordy:    {len(produkty)} unikalnych, {len(widok_szczegolow(lista[0]))} atrybutów")
    print(f"Podstrony:  {len(strony)} ({', '.join(adres_strony(n) for n in range(1, len(strony) + 1))})")
    print(f"Pozycje:    {pozycje} (w tym {len(duplikaty)} duplikatów rozrzuconych po innych podstronach)")
    print(f"Pliki JSON: {porcji} porcji listy + {len(produkty)} rekordów szczegółowych + katalog.json")
    print(f"Pliki HTML: {len(strony)} podstron katalogu + {len(produkty)} stron produktów")
    for pole in ("producent", "ocena"):
        braki = sum(produkty[i][pole] is None for i in produkty)
        print(f"  braki w polu {pole:<12} {braki:>4} ({braki / len(produkty):.1%})")
    print("  waluty: " + ", ".join(
        f"{waluta} {sum(p['waluta'] == waluta for p in produkty.values())}" for waluta in KURSY_WALUT))
    print("\nUruchom serwis:  python -m http.server 8000")


if __name__ == "__main__":
    main()
