#!/usr/bin/env python3
"""Weryfikacja serwisu Bajtomarket pod kątem wymagań Laboratorium nr 1 (rola AUTOR, 5.0).

Serwis jest statyczny, więc kontrola działa bezpośrednio na plikach — nie trzeba niczego
uruchamiać. Najważniejszy pomiar to liczba rekordów widocznych w surowym HTML (zero):
to ta liczba wchodzi do sprawozdania jako jedna strona porównania HTML ↔ DOM.

Uruchomienie:  python sprawdz_serwis.py
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

KATALOG_GLOWNY = Path(__file__).resolve().parent
DANE = KATALOG_GLOWNY / "dane"
STRONY_PRODUKTOW = KATALOG_GLOWNY / "produkt"
STATYCZNE = KATALOG_GLOWNY / "statyczne"

POLA_LISTY = ["id", "url", "nazwa", "kategoria", "producent", "cena_tekst", "cena_poprzednia_tekst",
              "waluta", "dostepnosc", "ocena_tekst", "liczba_opinii", "data_tekst", "gwarancja_tekst"]
POLA_SZCZEGOLOW = ["ean", "stan_magazynowy", "sprzedawca", "opis", "kod_producenta", "kolor",
                   "material", "waga_tekst", "wymiary_tekst", "kraj_pochodzenia",
                   "czas_dostawy_tekst", "koszt_dostawy_tekst", "zwrot_tekst"]

wyniki: list[tuple[bool, str]] = []


def sprawdz(warunek: bool, opis: str) -> None:
    wyniki.append((bool(warunek), opis))
    print(f"  [{'OK ' if warunek else 'BLAD'}] {opis}")


def naglowek(tytul: str) -> None:
    print(f"\n{tytul}\n{'─' * len(tytul)}")


def wczytaj(sciezka: Path):
    return json.loads(sciezka.read_text(encoding="utf-8"))


# ───────────────────────────── kontrole ─────────────────────────────

def struktura(katalog: dict) -> None:
    naglowek("1. Paginacja i rozmiar katalogu")
    sprawdz(len(katalog["strony"]) >= 5, f"liczba podstron: {len(katalog['strony'])} (wymagane ≥ 5)")
    sprawdz(katalog["liczba_produktow"] >= 400,
            f"liczba unikalnych rekordów: {katalog['liczba_produktow']} (wymagane ≥ 400)")
    for strona in katalog["strony"]:
        plik = KATALOG_GLOWNY / strona["adres"]
        if not plik.is_file():
            sprawdz(False, f"brakuje pliku podstrony {strona['adres']}")
            return
    sprawdz(True, "każda podstrona ma własny plik HTML: "
                  + ", ".join(s["adres"] for s in katalog["strony"]))


def zbierz_pozycje(katalog: dict) -> list[dict]:
    naglowek("2. Porcje listy")
    pozycje: list[dict] = []
    for strona in katalog["strony"]:
        wczytane = 0
        for numer in range(1, strona["porcji"] + 1):
            porcja = wczytaj(DANE / f"strona-{strona['numer']}-porcja-{numer}.json")
            pozycje.extend(porcja["produkty"])
            wczytane += porcja["ile"]
        print(f"       podstrona {strona['numer']}: {strona['porcji']} porcji, {wczytane} pozycji")
    sprawdz(len(pozycje) >= 200, f"łączna liczba pozycji na listach: {len(pozycje)} (wymagane ≥ 200)")
    rozmiary = {len(wczytaj(p)["produkty"]) for p in DANE.glob("strona-*-porcja-*.json")}
    sprawdz(max(rozmiary) <= katalog["rozmiar_porcji"],
            f"porcje liczą po {katalog['rozmiar_porcji']} rekordów (największa: {max(rozmiary)})")
    return pozycje


def brak_rekordow_w_html(katalog: dict, pozycje: list[dict]) -> None:
    naglowek("3. Treść wstrzykiwana JavaScriptem (źródło HTML a dane)")
    probka = pozycje[:60]
    trafienia_nazw = trafienia_id = 0
    for strona in katalog["strony"]:
        zrodlo = (KATALOG_GLOWNY / strona["adres"]).read_text(encoding="utf-8")
        trafienia_nazw += sum(rekord["nazwa"] in zrodlo for rekord in probka)
        trafienia_id += sum(f'data-id="{rekord["id"]}"' in zrodlo for rekord in probka)
    sprawdz(trafienia_nazw == 0, f"w źródle podstron nie ma żadnej nazwy produktu ({trafienia_nazw})")
    sprawdz(trafienia_id == 0, f"w źródle podstron nie ma żadnego identyfikatora rekordu ({trafienia_id})")

    przyklad = probka[0]
    zrodlo = (STRONY_PRODUKTOW / f"{przyklad['id']}.html").read_text(encoding="utf-8")
    sprawdz(przyklad["nazwa"] not in zrodlo and przyklad["cena_tekst"] not in zrodlo,
            f"strona produktu {przyklad['id']}.html nie zawiera ani nazwy, ani ceny")
    print("       rekordów w surowym HTML: 0 — do zestawienia z drzewem DOM w sprawozdaniu")


def strony_szczegolow(katalog: dict, pozycje: list[dict]) -> None:
    naglowek("4. Podstrony szczegółów i liczba atrybutów")
    identyfikatory = {rekord["id"] for rekord in pozycje}
    brakujace_html = [i for i in identyfikatory if not (STRONY_PRODUKTOW / f"{i}.html").is_file()]
    brakujace_json = [i for i in identyfikatory if not (DANE / "produkt" / f"{i}.json").is_file()]
    sprawdz(not brakujace_html, f"każdy rekord ma własną stronę HTML ({len(identyfikatory)} plików)")
    sprawdz(not brakujace_json, f"każdy rekord ma własny plik danych ({len(identyfikatory)} plików)")

    przyklad = wczytaj(DANE / "produkt" / f"{pozycje[0]['id']}.json")
    dodatkowe = [pole for pole in POLA_SZCZEGOLOW if pole in przyklad]
    sprawdz(len(dodatkowe) >= 8, f"atrybutów wyłącznie na stronie produktu: {len(dodatkowe)} (wymagane ≥ 8)")
    sprawdz(len(przyklad) >= 22, f"łączna liczba atrybutów rekordu: {len(przyklad)} (wymagane ≥ 22)")
    sprawdz(all(pole in pozycje[0] for pole in POLA_LISTY),
            f"atrybutów na liście katalogu: {len(pozycje[0])} (wymagane ≥ 10)")


def utrudnienia_danych(pozycje: list[dict]) -> None:
    naglowek("5. Utrudnienia z poziomu 4.0 (wymagane 3)")
    unikalne = {rekord["id"]: rekord for rekord in pozycje}

    waluty = Counter(rekord["waluta"] for rekord in unikalne.values())
    przyklady = {w: next(r["cena_tekst"] for r in unikalne.values() if r["waluta"] == w) for w in waluty}
    sprawdz(len(waluty) >= 2, f"(1) ceny w różnych walutach: {dict(waluty)}")
    sprawdz(any(" " in r["cena_tekst"] for r in unikalne.values()),
            f"(1) twarde spacje w zapisie ceny — {przyklady}")

    for pole in ("producent", "ocena_tekst"):
        braki = sum(1 for r in unikalne.values() if r[pole] is None)
        sprawdz(braki / len(unikalne) >= 0.15,
                f"(2) braki w polu {pole}: {braki} ({braki / len(unikalne):.1%}, wymagane ≥ 15%)")

    powtorzone = {i: ile for i, ile in Counter(r["id"] for r in pozycje).items() if ile > 1}
    sprawdz(len(powtorzone) >= 8, f"(3) zduplikowanych rekordów: {len(powtorzone)} (wymagane ≥ 8)")


def utrudnienia_interakcji() -> None:
    naglowek("6. Utrudnienia z poziomu 5.0 (wymagane 2)")
    szablon = (KATALOG_GLOWNY / "szablony" / "produkt.html").read_text(encoding="utf-8")
    puste_panele = re.findall(r'<div class="panel-zakladki" id="panel-(specyfikacja|dostawa)"[^>]*>\s*</div>',
                              szablon)
    sprawdz(len(puste_panele) == 2,
            "(1) zakładki Specyfikacja i Dostawa są w szablonie puste — treść powstaje po kliknięciu")
    produkt_js = (STATYCZNE / "produkt.js").read_text(encoding="utf-8")
    sprawdz("wypelnijPanel" in produkt_js and "wypelnione[nazwa]" in produkt_js,
            "(1) panel wypełnia się tylko przy pierwszym otwarciu")

    katalog_js = (STATYCZNE / "katalog.js").read_text(encoding="utf-8")
    sprawdz("zmienFiltry" in katalog_js and "rysuj()" in katalog_js,
            "(2) filtrowanie i sortowanie przerysowują listę bez przeładowania strony")


def wymogi_poziomu(katalog: dict) -> None:
    naglowek("7. Pozostałe wymagania obowiązkowe poziomu 5.0")
    wspolne_js = (STATYCZNE / "wspolne.js").read_text(encoding="utf-8")
    zakres = re.search(r"OPOZNIENIE_PORCJI\s*=\s*\[(\d+),\s*(\d+)\]", wspolne_js)
    if zakres:
        od, do = int(zakres.group(1)), int(zakres.group(2))
        sprawdz(od >= 300 and do <= 2000, f"sztuczne opóźnienie porcji: {od}–{do} ms (wymagane 300–2000)")
    else:
        sprawdz(False, "nie znaleziono deklaracji opóźnienia porcji")

    katalog_js = (STATYCZNE / "katalog.js").read_text(encoding="utf-8")
    sprawdz("tabela-ofert" in katalog_js and 'utworz("article", { klasa: "produkt"' in katalog_js,
            "rekordy trafiają do dwóch struktur: tabeli i kart article.produkt")
    sprawdz("wczytaj-wiecej" in katalog_js, "doładowywanie porcjami przyciskiem „Wczytaj więcej”")
    sprawdz("fetch(" in wspolne_js, "dane pobierane przez fetch z plików JSON")

    robots = (KATALOG_GLOWNY / "robots.txt").read_text(encoding="utf-8")
    sprawdz("Crawl-delay" in robots, "serwis udostępnia robots.txt z Crawl-delay")
    print(f"       stan katalogu: {katalog['data_stanu']}, rozmiar porcji: {katalog['rozmiar_porcji']}")


def main() -> int:
    if not (DANE / "katalog.json").is_file():
        print("Brak pliku dane/katalog.json — uruchom najpierw: python generuj_serwis.py")
        return 2

    katalog = wczytaj(DANE / "katalog.json")
    print(f"Weryfikacja serwisu: {katalog['serwis']} ({KATALOG_GLOWNY})")

    struktura(katalog)
    pozycje = zbierz_pozycje(katalog)
    brak_rekordow_w_html(katalog, pozycje)
    strony_szczegolow(katalog, pozycje)
    utrudnienia_danych(pozycje)
    utrudnienia_interakcji()
    wymogi_poziomu(katalog)

    bledy = [opis for ok, opis in wyniki if not ok]
    naglowek("Podsumowanie")
    print(f"  kontroli wykonanych: {len(wyniki)}, zakończonych powodzeniem: {len(wyniki) - len(bledy)}")
    for opis in bledy:
        print(f"  — nie spełniono: {opis}")
    return 1 if bledy else 0


if __name__ == "__main__":
    sys.exit(main())
