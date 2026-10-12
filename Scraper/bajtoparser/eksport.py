"""Eksport oczyszczonych rekordów jednocześnie do CSV (UTF-8) i JSON (bez selenium)."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pandas as pd

from bajtoparser.parsing.rekord import KOLUMNY, KOLUMNY_CALKOWITE, KOLUMNY_ZMIENNOPRZECINKOWE


def ramka_danych(rekordy: Iterable[dict[str, Any]]) -> pd.DataFrame:
    """Buduje DataFrame w kolejności `KOLUMNY` z typami liczbowymi (braki jako NaN/<NA>).

    Kolumny zmiennoprzecinkowe mają typ `float64`, całkowite nullable `Int64` (bez
    zamiany 25 na 25.0 tylko dlatego, że w kolumnie są braki), reszta `object`.
    """
    ramka = pd.DataFrame(list(rekordy), columns=KOLUMNY)
    for kolumna in KOLUMNY_ZMIENNOPRZECINKOWE:
        ramka[kolumna] = pd.to_numeric(ramka[kolumna], errors="raise").astype("float64")
    for kolumna in KOLUMNY_CALKOWITE:
        ramka[kolumna] = pd.to_numeric(ramka[kolumna], errors="raise").astype("Int64")
    return ramka


def eksportuj(rekordy: Iterable[dict[str, Any]], katalog: Path, nazwa: str) -> tuple[Path, Path]:
    """Zapisuje `<katalog>/<nazwa>.csv` i `<katalog>/<nazwa>.json`; zwraca obie ścieżki.

    CSV: UTF-8 bez BOM, separator przecinek, bez indeksu. JSON: lista obiektów
    (`orient="records"`), polskie znaki bez escapowania, wcięcie 2, braki jako `null`.
    """
    katalog = Path(katalog)
    katalog.mkdir(parents=True, exist_ok=True)
    ramka = ramka_danych(rekordy)
    csv = katalog / f"{nazwa}.csv"
    json = katalog / f"{nazwa}.json"
    ramka.to_csv(csv, index=False, encoding="utf-8")
    ramka.to_json(json, orient="records", force_ascii=False, indent=2)
    return csv, json
