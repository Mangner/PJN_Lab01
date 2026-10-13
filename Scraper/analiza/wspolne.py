"""Wspólne narzędzia skryptów analizy: ścieżki, wczytywanie danych, tabele Markdown."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

KORZEN = Path(__file__).resolve().parent.parent
WYJSCIE = KORZEN / "output"
LOGI = KORZEN / "logs"
WYNIKI = Path(__file__).resolve().parent / "wyniki"
WYKRESY = Path(__file__).resolve().parent / "wykresy"

CSV_OKNO = WYJSCIE / "okno.csv"
CSV_HEADLESS = WYJSCIE / "headless.csv"
JSONL_OKNO = WYJSCIE / "okno_surowe.jsonl"

KOLUMNY_LICZBOWE = [
    "cena",
    "cena_poprzednia",
    "gwarancja_mies",
    "ocena",
    "liczba_opinii",
    "waga_kg",
    "dlugosc_cm",
    "szerokosc_cm",
    "wysokosc_cm",
    "stan_magazynowy_szt",
    "czas_dostawy_dni",
    "koszt_dostawy",
    "zwrot_dni",
]


def ustaw_utf8() -> None:
    """Konsola Windows bywa w cp1250: wymuszamy UTF-8 dla wypisywanych komunikatów."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def wczytaj_csv(sciezka: Path = CSV_OKNO) -> pd.DataFrame:
    """Wczytuje eksport CSV; `ean` jako tekst (inaczej tracone byłyby zera i precyzja)."""
    return pd.read_csv(sciezka, dtype={"ean": str})


def wczytaj_surowe(sciezka: Path = JSONL_OKNO) -> pd.DataFrame:
    """Wczytuje surowe wartości sprzed czyszczenia (jedna linia JSON = jeden rekord).

    Karty nie mają elementu `cena_poprzednia` bez promocji (klucz nieobecny), tabela ma pusty
    napis; oba oznaczają brak promocji, więc nieobecne klucze uzupełniamy pustym napisem.
    """
    with sciezka.open(encoding="utf-8") as plik:
        return pd.DataFrame([json.loads(linia) for linia in plik if linia.strip()]).fillna("")


def podsumowanie_z_logu(tryb: str = "okno") -> dict[str, Any]:
    """Zwraca liczby z linii `PODSUMOWANIE:` najnowszego pełnego przebiegu danego trybu.

    Pełny przebieg to taki, w którym `lista` > 0 i rekordów jest co najmniej 400 (testowe
    przebiegi `--strony 1 --limit 5` są pomijane).
    """
    wzorzec = re.compile(
        r"PODSUMOWANIE: tryb=(?P<tryb>\w+), stron=(?P<strony>\d+), rekordów=(?P<rekordy>\d+), "
        r"błędów=(?P<bledy>\d+), retry=(?P<retry>\d+), czas=(?P<czas>[\d.]+) s; "
        r"lista=(?P<lista>\d+), po deduplikacji=(?P<po_dedup>\d+), "
        r"duplikatów=(?P<duplikaty>\d+) \(różnych od oryginału: (?P<rozne>\d+)\)"
    )
    znalezione: list[tuple[str, dict[str, Any]]] = []
    for sciezka in sorted(LOGI.glob("bajtoparser_*.log")):
        for linia in sciezka.read_text(encoding="utf-8").splitlines():
            trafienie = wzorzec.search(linia)
            if trafienie and trafienie["tryb"] == tryb and int(trafienie["rekordy"]) >= 400:
                dane: dict[str, Any] = {
                    k: (float(v) if k == "czas" else int(v))
                    for k, v in trafienie.groupdict().items()
                    if k != "tryb"
                }
                dane["plik_logu"] = sciezka.name
                znalezione.append((sciezka.name, dane))
    if not znalezione:
        raise SystemExit(f"Brak pełnego przebiegu w logach (tryb={tryb}) w {LOGI}")
    return znalezione[-1][1]


def _komorka(wartosc: Any) -> str:
    if isinstance(wartosc, float):
        if pd.isna(wartosc):
            return ""
        return (
            f"{wartosc:.2f}".rstrip("0").rstrip(".")
            if wartosc != int(wartosc)
            else str(int(wartosc))
        )
    return str(wartosc).replace("|", "\\|").replace("\n", " ")


def tabela_md(ramka: pd.DataFrame, indeks: bool = False) -> str:
    """Zamienia ramkę na tabelę Markdown (bez zależności od `tabulate`)."""
    if indeks:
        ramka = ramka.reset_index()
    naglowek = "| " + " | ".join(str(k) for k in ramka.columns) + " |"
    separator = "|" + "|".join("---" for _ in ramka.columns) + "|"
    wiersze = [
        "| " + " | ".join(_komorka(v) for v in wiersz) + " |"
        for wiersz in ramka.itertuples(index=False, name=None)
    ]
    return "\n".join([naglowek, separator, *wiersze])


def zapisz(nazwa: str, tresc: str) -> Path:
    """Zapisuje plik wyników (UTF-8) w `analiza/wyniki/`."""
    WYNIKI.mkdir(parents=True, exist_ok=True)
    sciezka = WYNIKI / nazwa
    sciezka.write_text(tresc, encoding="utf-8")
    return sciezka
