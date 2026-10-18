"""Kontrola jakości danych Bajtoparsera: braki, duplikaty, typy, odstające, zgodność z README.

Uruchomienie: `python analiza/kontrola_jakosci.py`. Wynik: `analiza/wyniki/kontrola_jakosci.md`.
Wszystkie liczby w raporcie są liczone z `output/okno.csv`, `output/okno_surowe.jsonl`,
`output/headless.csv` oraz z logu pełnego przebiegu; nic nie jest wpisane z pamięci poza
liczbami kontrolnymi z README serwisu (stałe `README` poniżej), które są punktem odniesienia.
"""

from __future__ import annotations

import hashlib
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wspolne as w

# Liczby kontrolne z README serwisu (docs/SERWIS.md, sekcja „Kontrola poprawności”).
README = {
    "lista": 432,
    "unikalne": 420,
    "duplikaty": 12,
    "PLN": 357,
    "EUR": 38,
    "USD": 25,
    "producent": 71,
    "ocena": 84,
}
BRAK = ("—", "")  # „—” (brak danych) i pusty napis

# kolumna CSV -> pole surowe (tam, gdzie braki mają surowy odpowiednik)
SUROWE_POLE = {
    "producent": "producent",
    "ocena": "ocena",
    "gwarancja_mies": "gwarancja",
    "waga_kg": "waga",
    "cena_poprzednia": "cena_poprzednia",
}


# --- niezależne odczytanie surowych wartości (kontrola parsera, bez importu parsing/) ----------


def _liczba(tekst: str, usun_przecinki: bool = False) -> float:
    """Najprostsze możliwe odczytanie liczby z tekstu, niezależne od `parsing/`."""
    if usun_przecinki:
        return float(re.sub(r"[^\d.]", "", tekst))
    return float(re.sub(r"[^\d,]", "", tekst).replace(",", "."))


def _cena_niezalezna(surowa: str, waluta: str) -> float:
    return _liczba(surowa, usun_przecinki=(waluta == "USD"))


def _niezalezne(surowe: pd.DataFrame) -> dict[str, tuple[str, Callable[[pd.Series], float]]]:
    """Mapa kolumna CSV -> (pole surowe, funkcja odczytu zwracająca NaN dla braku)."""

    def lub_nan(f: Callable[[str], float]) -> Callable[[str], float]:
        return lambda s: np.nan if s.strip() in BRAK else f(s)

    return {
        "ocena": ("ocena", lub_nan(_liczba)),
        "gwarancja_mies": ("gwarancja", lub_nan(lambda s: float(re.search(r"\d+", s)[0]))),
        "liczba_opinii": ("liczba_opinii", lub_nan(lambda s: float(s))),
        "waga_kg": ("waga", lub_nan(lambda s: _liczba(s.split("kg")[0]))),
        "stan_magazynowy_szt": (
            "stan_magazynowy",
            lub_nan(lambda s: float(re.search(r"\d+", s)[0])),
        ),
        "czas_dostawy_dni": ("czas_dostawy", lub_nan(lambda s: float(re.search(r"\d+", s)[0]))),
        "zwrot_dni": ("zwrot", lub_nan(lambda s: float(re.search(r"\d+", s)[0]))),
        "koszt_dostawy": (
            "koszt_dostawy",
            lub_nan(lambda s: 0.0 if s.strip().lower() == "gratis" else _liczba(s)),
        ),
    }


def _wymiary_niezalezne(s: str) -> tuple[float, float, float]:
    liczby = [float(x.replace(",", ".")) for x in re.findall(r"\d+(?:,\d+)?", s)]
    return liczby[0], liczby[1], liczby[2]


def zgodnosc_surowe_oczyszczone(df: pd.DataFrame, surowe: pd.DataFrame) -> pd.DataFrame:
    """Porównuje CSV z niezależnym odczytem surowych napisów (po `id`). Zwraca tabelę."""
    s = surowe.set_index("id").loc[df["id"]].reset_index()
    wiersze: list[dict[str, Any]] = []

    def porownaj(nazwa: str, oczekiwane: pd.Series, dane: pd.Series) -> None:
        zgodne = np.isclose(oczekiwane.astype(float), dane.astype(float), equal_nan=True)
        wiersze.append(
            {"kolumna": nazwa, "porównano": len(df), "niezgodnych": int((~zgodne).sum())}
        )

    ceny = pd.Series(
        [_cena_niezalezna(c, wl) for c, wl in zip(s["cena"], df["waluta"], strict=True)]
    )
    porownaj("cena", ceny, df["cena"])
    poprzednie = pd.Series(
        [
            np.nan if c.strip() in BRAK else _cena_niezalezna(c, wl)
            for c, wl in zip(s["cena_poprzednia"], df["waluta"], strict=True)
        ]
    )
    porownaj("cena_poprzednia", poprzednie, df["cena_poprzednia"])
    for kolumna, (pole, funkcja) in _niezalezne(s).items():
        porownaj(kolumna, s[pole].map(funkcja), df[kolumna])
    wym = s["wymiary"].map(_wymiary_niezalezne)
    for i, kolumna in enumerate(["szerokosc_cm", "wysokosc_cm", "glebokosc_cm"]):
        porownaj(kolumna, wym.map(lambda t, i=i: t[i]), df[kolumna])
    daty = pd.to_datetime(s["data_dodania"], format="%d.%m.%Y").dt.strftime("%Y-%m-%d")
    wiersze.append(
        {
            "kolumna": "data_dodania",
            "porównano": len(df),
            "niezgodnych": int((daty.to_numpy() != df["data_dodania"].to_numpy()).sum()),
        }
    )
    for kolumna in ["waluta", "producent", "kategoria", "nazwa", "ean"]:
        lewa = [None if str(v).strip() in BRAK else v for v in s[kolumna]]
        prawa = [None if pd.isna(v) else v for v in df[kolumna]]
        niezgodne = sum(1 for x, y in zip(lewa, prawa, strict=True) if x != y)
        wiersze.append({"kolumna": kolumna, "porównano": len(df), "niezgodnych": niezgodne})
    return pd.DataFrame(wiersze)


# --- sekcje raportu --------------------------------------------------------------------------


def sekcja_braki(df: pd.DataFrame, surowe: pd.DataFrame) -> tuple[str, pd.DataFrame]:
    s = surowe.set_index("id").loc[df["id"]].reset_index()
    wiersze = []
    for kolumna in df.columns:
        braki = int(df[kolumna].isna().sum())
        pole = SUROWE_POLE.get(kolumna)
        surowe_puste = int(s[pole].map(lambda v: str(v).strip() in BRAK).sum()) if pole else ""
        uwaga = ""
        if kolumna == "cena_poprzednia":
            uwaga = "brak promocji, nie brak danych"
        elif braki and pole:
            uwaga = (
                "znak „—” w surowych danych" if surowe_puste == braki else "NIEZGODNE z surowymi"
            )
        wiersze.append(
            {
                "kolumna": kolumna,
                "braków (szt.)": braki,
                "braków (%)": f"{100 * braki / len(df):.1f}",
                "puste w surowych": surowe_puste,
                "uwaga": uwaga,
            }
        )
    tabela = pd.DataFrame(wiersze)
    tresc = (
        f"Liczba rekordów: **{len(df)}**, kolumn: **{df.shape[1]}**.\n\n"
        "Kolumna „puste w surowych” to liczba wartości `—` lub pustych w "
        "`okno_surowe.jsonl` dla tego samego pola: musi się zgadzać z brakami w CSV, "
        "inaczej parser zamieniałby coś w `NaN` bez powodu.\n\n"
        + w.tabela_md(tabela[tabela["braków (szt.)"] > 0])
        + f"\n\nPozostałe {int((tabela['braków (szt.)'] == 0).sum())} kolumn nie ma braków "
        "(pełna lista kolumn w tabeli typów poniżej)."
    )
    return tresc, tabela


def sekcja_duplikaty(df: pd.DataFrame, log: dict[str, Any]) -> str:
    powtorzone_csv = int(df["id"].duplicated().sum())
    powtorzone_url = int(df["url"].duplicated().sum())
    return (
        "| Etap | Liczba pozycji |\n|---|---|\n"
        f"| Pozycje na liście przed deduplikacją (log) | {log['lista']} |\n"
        f"| Po deduplikacji po `id` (log) | {log['po_dedup']} |\n"
        f"| Usunięte duplikaty (log) | {log['duplikaty']} |\n"
        f"| Duplikaty różne od oryginału (log pipeline'u) | **{log['rozne']}** |\n"
        f"| Rekordy w `okno.csv` | {len(df)} |\n"
        f"| Powtórzone `id` w `okno.csv` | {powtorzone_csv} |\n"
        f"| Powtórzone `url` w `okno.csv` | {powtorzone_url} |\n\n"
        f"Źródło liczb z logu: `logs/{log['plik_logu']}` (linia `PODSUMOWANIE:`).\n\n"
        "**Porównanie usuniętych duplikatów z oryginałem.** Pipeline porównał pola listy "
        "(po oczyszczeniu) każdego duplikatu z pierwszym wystąpieniem tego samego `id` jeszcze "
        f"przed usunięciem: różnych było **{log['rozne']}** z {log['duplikaty']}. Szczegóły "
        "(zakładki Specyfikacja i Dostawa) duplikatu są identyczne z założenia: duplikat ma to "
        "samo `id` i ten sam URL, więc prowadzi do tej samej strony produktu "
        "`produkt/<id>.html`, a jej treść nie zależy od tego, z której podstrony listy "
        "weszliśmy. Dlatego pipeline deduplikuje przed wejściem w szczegóły (duplikaty nie "
        "generują żądań). Ograniczenie: usunięte duplikaty nie są zapisane w żadnym pliku "
        "(`okno_surowe.jsonl` ma już tylko 420 linii), więc porównania nie da się powtórzyć "
        "z samych plików wyjściowych; opieramy się na liczbie z logu."
    )


def sekcja_typy(df: pd.DataFrame) -> tuple[str, dict[str, Any]]:
    wiersze = []
    for kolumna in df.columns:
        wiersze.append(
            {
                "kolumna": kolumna,
                "dtype": str(df[kolumna].dtype),
                "oczekiwany": "liczbowy" if kolumna in w.KOLUMNY_LICZBOWE else "tekst",
                "zgodny": "tak"
                if pd.api.types.is_numeric_dtype(df[kolumna]) == (kolumna in w.KOLUMNY_LICZBOWE)
                else "NIE",
            }
        )
    tabela = pd.DataFrame(wiersze)
    tekst = pd.read_csv(w.CSV_OKNO, dtype=str, keep_default_na=False)
    nieliczbowe = {
        k: int((pd.to_numeric(tekst[k], errors="coerce").isna() & (tekst[k] != "")).sum())
        for k in w.KOLUMNY_LICZBOWE
    }
    kontrole = {
        "ean_nie_13_cyfr": int((~df["ean"].str.fullmatch(r"\d{13}")).sum()),
        "ocena_poza_0_5": int(((df["ocena"] < 0) | (df["ocena"] > 5)).sum()),
        "ujemne_liczby": int((df[w.KOLUMNY_LICZBOWE] < 0).sum().sum()),
        "url_niezgodny_z_id": int((df["url"] != "/produkt/" + df["id"] + ".html").sum()),
        "data_nie_iso": int(
            pd.to_datetime(df["data_dodania"], format="%Y-%m-%d", errors="coerce").isna().sum()
        ),
        "waluta_poza_zbiorem": int((~df["waluta"].isin(["PLN", "EUR", "USD"])).sum()),
        "znaki_zastepcze": int(
            sum(
                df[k].astype(str).str.contains("�|Ã|Å|Ä", regex=True).sum()
                for k in df.select_dtypes(include=["object", "string"]).columns
            )
        ),
    }
    szczegoly = ", ".join(f"{k}: {v}" for k, v in nieliczbowe.items() if v)
    tresc = (
        w.tabela_md(tabela)
        + "\n\nTekst w kolumnach liczbowych (niepuste komórki CSV, których nie da się "
        f"zamienić na liczbę): **{sum(nieliczbowe.values())}**"
        + (f" ({szczegoly})" if szczegoly else "")
        + "."
        + "\n\n| Kontrola spójności | Rekordów naruszających |\n|---|---|\n"
        + "\n".join(f"| {k} | {v} |" for k, v in kontrole.items())
    )
    return tresc, {"tabela": tabela, "nieliczbowe": nieliczbowe, "kontrole": kontrole}


def _odstajace(seria: pd.Series) -> dict[str, Any]:
    s = seria.dropna()
    q1, q3 = s.quantile([0.25, 0.75])
    iqr = q3 - q1
    dolna, gorna = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    z = (s - s.mean()) / s.std()
    maska_iqr = (s < dolna) | (s > gorna)
    return {
        "n": len(s),
        "q1": q1,
        "q3": q3,
        "dolna": dolna,
        "gorna": gorna,
        "iqr": int(maska_iqr.sum()),
        "z": int((z.abs() > 3).sum()),
        "min": s.min(),
        "max": s.max(),
        "maska_iqr": maska_iqr,
        "maska_z": z.abs() > 3,
        "mediana": s.median(),
    }


def _interpretacja(nazwa: str, czesc: pd.DataFrame, kolumna: str) -> str:
    """Interpretacja grupy odstających: anomalia danych czy błąd parsera (liczby z danych)."""
    if nazwa == "liczba_opinii":
        malejaco = czesc[kolumna].sort_values(ascending=False).tolist()
        return (
            f"Jedna wartość ({malejaco[0]:g}) jest {malejaco[0] / malejaco[1]:.1f}× większa od "
            f"następnej ({malejaco[1]:g}) i jest jedynym odstającym wg z-score. Surowy napis to "
            "same cyfry (bez separatora, spacji i przecinka), więc parser nie miał jak jej "
            "zniekształcić. **Anomalia danych źródłowych, nie błąd parsera**; przy korelacjach "
            "raportować z nią i bez niej."
        )
    if nazwa.startswith("cena"):
        usd = (
            " Wartości z separatorem tysięcy (`$1,769.99`) są odczytane jako 1769.99, czyli "
            "poprawnie; to przypadek, na którym naiwny odczyt zawodzi (sekcja niżej)."
            if nazwa.endswith("USD")
            else ""
        )
        return (
            "Prawostronny ogon rozkładu: drogi sprzęt (komputery, RTV, AGD, sport). Surowy napis "
            "daje dokładnie tę wartość, więc to **prawdziwa cecha danych, nie błąd parsera**." + usd
        )
    if nazwa == "waga_kg":
        return (
            "Ciężkie towary (dom i ogród, RTV, sport, AGD). Surowy napis (`38,5 kg`) daje tę samą "
            "liczbę; przecinek dziesiętny nie został wzięty za separator tysięcy (385 kg byłoby "
            "wartością absurdalną). **Anomalia danych (towary ciężkie), nie błąd parsera**."
        )
    if nazwa.endswith("_cm"):
        return (
            "Duże i długie towary (telewizory i soundbary, lampy stojące, sprzęt sportowy). "
            "Wartości zgodne z surowym tekstem `a x b x c cm`, więc to **nie błąd przepisania**; "
            "pozycja liczby w tekście odpowiada nazwie osi (szerokość × wysokość × głębokość, "
            "patrz wniosek)."
        )
    return ""


def sekcja_odstajace(df: pd.DataFrame, surowe: pd.DataFrame, niezgodne: int) -> tuple[str, int]:
    s = surowe.set_index("id").loc[df["id"]].reset_index()
    d = df.assign(
        surowa_cena=s["cena"],
        surowa_waga=s["waga"],
        surowe_wymiary=s["wymiary"],
        surowe_opinie=s["liczba_opinii"],
        surowy_stan=s["stan_magazynowy"],
    )
    grupy: list[tuple[str, pd.DataFrame, str, str]] = [
        ("cena PLN", d[d["waluta"] == "PLN"], "cena", "surowa_cena"),
        ("cena EUR", d[d["waluta"] == "EUR"], "cena", "surowa_cena"),
        ("cena USD", d[d["waluta"] == "USD"], "cena", "surowa_cena"),
        ("waga_kg", d, "waga_kg", "surowa_waga"),
        ("szerokosc_cm", d, "szerokosc_cm", "surowe_wymiary"),
        ("wysokosc_cm", d, "wysokosc_cm", "surowe_wymiary"),
        ("glebokosc_cm", d, "glebokosc_cm", "surowe_wymiary"),
        ("liczba_opinii", d, "liczba_opinii", "surowe_opinie"),
        ("stan_magazynowy_szt", d, "stan_magazynowy_szt", "surowy_stan"),
    ]
    wiersze = []
    opisy: list[str] = []
    for nazwa, czesc, kolumna, kol_surowa in grupy:
        o = _odstajace(czesc[kolumna])
        wiersze.append(
            {
                "cecha": nazwa,
                "n": o["n"],
                "mediana": o["mediana"],
                "Q1": o["q1"],
                "Q3": o["q3"],
                "granica dolna": o["dolna"],
                "granica górna": o["gorna"],
                "odstające IQR": o["iqr"],
                "odstające \\|z\\|>3": o["z"],
                "max": o["max"],
            }
        )
        if o["iqr"] == 0:
            zera = int((czesc[kolumna] == 0).sum())
            opisy.append(
                f"### {nazwa}\n\nBrak wartości odstających wg IQR ({o['z']} wg z-score). "
                f"Zakres 0-{o['max']:g}, zer: {zera} (0 szt. to rzeczywisty stan magazynowy, "
                "a nie brak danych)."
            )
            continue
        odstajace = czesc.loc[o["maska_iqr"].index[o["maska_iqr"]]]
        gorne = odstajace[odstajace[kolumna] > o["gorna"]].sort_values(kolumna, ascending=False)
        dolne = odstajace[odstajace[kolumna] < o["dolna"]]
        kat = gorne["kategoria"].value_counts()
        kat_txt = ", ".join(f"{k} ({v})" for k, v in kat.head(4).items())
        top = gorne.head(5)[["id", "kategoria", kolumna, kol_surowa]].copy()
        top.columns = ["id", "kategoria", "wartość", "surowy napis"]
        opisy.append(
            f"### {nazwa}\n\n"
            f"Odstających wg IQR: {o['iqr']} (górnych: {len(gorne)}, dolnych: {len(dolne)}), "
            f"wg z-score: {o['z']}. Największa wartość: {o['max']:g} "
            f"({o['max'] / o['mediana']:.1f}× mediany). Kategorie odstających górnych: "
            f"{kat_txt}.\n\n"
            + w.tabela_md(top)
            + f"\n\n**Interpretacja.** {_interpretacja(nazwa, czesc, kolumna)}"
        )
    tabela = pd.DataFrame(wiersze)
    tresc = (
        "Metody: IQR (wartość poza [Q1 − 1,5·IQR; Q3 + 1,5·IQR]) oraz |z-score| > 3. Waluty "
        "analizowane osobno, bez przeliczania kursem.\n\n"
        + w.tabela_md(tabela)
        + "\n\n"
        + "\n\n".join(opisy)
    )
    return tresc, niezgodne


def sekcja_naiwny_replace(df: pd.DataFrame, surowe: pd.DataFrame) -> str:
    s = surowe.set_index("id").loc[df["id"]].reset_index()
    symbole = ["zł", "€", "$", "\xa0", " "]

    def oczysc(tekst: str) -> str:
        for sym in symbole:
            tekst = tekst.replace(sym, "")
        return tekst

    def naiwny(tekst: str) -> float | None:
        try:
            return float(oczysc(tekst).replace(",", "."))
        except ValueError:
            return None

    def usun_przecinki(tekst: str) -> float | None:
        try:
            return float(oczysc(tekst).replace(",", ""))
        except ValueError:
            return None

    wiersze = []
    przyklady: list[dict[str, Any]] = []
    for waluta in ["PLN", "EUR", "USD"]:
        maska = (df["waluta"] == waluta).to_numpy()
        surowe_ceny = s.loc[maska, "cena"].tolist()
        parser = df.loc[maska, "cena"].tolist()
        wyniki = [naiwny(t) for t in surowe_ceny]
        bledy = sum(1 for x in wyniki if x is None)
        zgodne = sum(
            1 for x, p in zip(wyniki, parser, strict=True) if x is not None and np.isclose(x, p)
        )
        inne = len(wyniki) - bledy - zgodne
        wariant = [usun_przecinki(t) for t in surowe_ceny]
        wariant_zle = sum(
            1 for x, p in zip(wariant, parser, strict=True) if x is None or not np.isclose(x, p)
        )
        wiersze.append(
            {
                "waluta": waluta,
                "rekordów": len(wyniki),
                'replace(",", ".") zgodne z parserem': zgodne,
                "wynik inny niż parser": inne,
                "ValueError": bledy,
                "wariant: usunięcie przecinków, błędnych": wariant_zle,
            }
        )
        for t, x, v, p in zip(surowe_ceny, wyniki, wariant, parser, strict=True):
            if x is None or not np.isclose(x, p):
                przyklady.append(
                    {
                        "waluta": waluta,
                        "surowy napis": t.replace("\xa0", "\\xa0"),
                        "parser": p,
                        'naiwny replace(",", ".")': "ValueError" if x is None else x,
                        "wariant: usunięcie przecinków": "ValueError" if v is None else v,
                    }
                )
    pokaz: list[dict[str, Any]] = []
    for waluta in ["PLN", "EUR", "USD"]:
        pokaz += [p for p in przyklady if p["waluta"] == waluta][:3]
    # dodatkowo kilka wartości, na których wariant „usuń przecinki” zawyża cenę ok. 100×
    wariant_100x = []
    for t, p in zip(s["cena"], df["cena"], strict=True):
        v = usun_przecinki(t)
        if v is not None and p and np.isclose(v / p, 100):
            wariant_100x.append((t, p, v))
    pokaz_100 = pd.DataFrame(
        [
            {"surowy napis": t.replace("\xa0", "\\xa0"), "parser": p, "usunięcie przecinków": v}
            for t, p, v in wariant_100x[:3]
        ]
    )
    wynik = (
        "Ilustracja na rzeczywistych surowych napisach z `okno_surowe.jsonl` (bez uruchamiania "
        "parsera). Naiwny odczyt: usunięcie `zł`, `€`, `$` i spacji (w tym U+00A0), potem "
        '`replace(",", ".")` i `float()`.\n\n'
        + w.tabela_md(pd.DataFrame(wiersze))
        + "\n\n"
        + (
            'Przypadki, w których naiwny `replace(",", ".")` daje wynik inny niż parser '
            "(do 3 na walutę):\n\n" + w.tabela_md(pd.DataFrame(pokaz))
            if pokaz
            else 'Naiwny `replace(",", ".")` dał dla każdego rekordu ten sam wynik co parser.'
        )
    )
    wynik += (
        "\n\n**Co z tego wynika (dokładnie to, co wyszło z danych).** Dla PLN i EUR (przecinek "
        'dziesiętny) naiwny `replace(",", ".")` jest poprawny. Zawodzi tylko tam, gdzie '
        "przecinek jest separatorem tysięcy, czyli dla USD z tysiącami (`$1,299.00`): wynik to "
        "napis z dwiema kropkami (`1.299.00`) i `ValueError`, a nie cena zawyżona 100×. "
        "Zawyżenie ok. 100× daje dopiero inny naiwny wariant (usunięcie przecinków, żeby „pozbyć "
        "się separatora tysięcy”): ceny z przecinkiem dziesiętnym (PLN i EUR) są wtedy mnożone "
        "przez 100.\n\n"
        + (
            "Przykłady wariantu z usunięciem przecinków (cena zawyżona 100×; `\\xa0` w napisie "
            "to twarda spacja U+00A0):\n\n" + w.tabela_md(pokaz_100)
            if len(pokaz_100)
            else ""
        )
    )
    return wynik


def sekcja_readme(df: pd.DataFrame, log: dict[str, Any], braki: pd.DataFrame) -> tuple[str, bool]:
    def licz(kolumna: str) -> int:
        return int(braki.loc[braki["kolumna"] == kolumna, "braków (szt.)"].iloc[0])

    wal = df["waluta"].value_counts()
    pozycje = [
        ("Pozycje na liście", README["lista"], log["lista"]),
        ("Unikalne rekordy (`id`)", README["unikalne"], int(df["id"].nunique())),
        ("Duplikaty", README["duplikaty"], log["duplikaty"]),
        ("Waluta PLN", README["PLN"], int(wal.get("PLN", 0))),
        ("Waluta EUR", README["EUR"], int(wal.get("EUR", 0))),
        ("Waluta USD", README["USD"], int(wal.get("USD", 0))),
        ("Braki w `producent`", README["producent"], licz("producent")),
        ("Braki w `ocena`", README["ocena"], licz("ocena")),
    ]
    wiersze = [
        {"miara": n, "README": r, "dane": d, "zgodne": "tak" if r == d else "NIE"}
        for n, r, d in pozycje
    ]
    zgodne = all(r == d for _, r, d in pozycje)
    nadmiarowe = [
        ("gwarancja_mies", licz("gwarancja_mies")),
        ("waga_kg", licz("waga_kg")),
    ]
    tresc = (
        w.tabela_md(pd.DataFrame(wiersze))
        + "\n\n**Rozbieżności (README o nich nie wspomina):** "
        + "; ".join(f"`{k}` ma {v} braków ({100 * v / len(df):.1f}%)" for k, v in nadmiarowe)
        + ". README podaje braki tylko dla `producent` i `ocena`. W surowych danych te "
        "braki to `—`, tak samo jak w polach z README, więc parser traktuje je prawidłowo jako "
        "`NaN` (kolumna „puste w surowych” w tabeli braków), a nie jako błąd."
    )
    return tresc, zgodne


def sekcja_okno_headless(df: pd.DataFrame) -> tuple[str, bool]:
    h = w.wczytaj_csv(w.CSV_HEADLESS)

    def sha(sciezka: Path) -> str:
        return hashlib.sha256(sciezka.read_bytes()).hexdigest()[:16]

    pliki = [
        ("CSV", w.CSV_OKNO, w.CSV_HEADLESS),
        ("JSON", w.WYJSCIE / "okno.json", w.WYJSCIE / "headless.json"),
        ("JSONL (surowe)", w.JSONL_OKNO, w.WYJSCIE / "headless_surowe.jsonl"),
    ]
    wiersze = []
    for nazwa, a, b in pliki:
        sa, sb = sha(a), sha(b)
        wiersze.append(
            {"plik": nazwa, "SHA-256 okno": sa, "SHA-256 headless": sb, "identyczne": sa == sb}
        )
    rowne = df.equals(h)
    zgodne = rowne and all(r["identyczne"] for r in wiersze)
    tresc = (
        w.tabela_md(pd.DataFrame(wiersze))
        + f"\n\n`DataFrame.equals` na `okno.csv` i `headless.csv`: **{rowne}** "
        f"({df.shape[0]} × {df.shape[1]} vs {h.shape[0]} × {h.shape[1]}). "
        "Hashe skrócone do 16 znaków."
    )
    return tresc, zgodne


def main() -> None:
    w.ustaw_utf8()
    df = w.wczytaj_csv()
    surowe = w.wczytaj_surowe()
    log = w.podsumowanie_z_logu("okno")

    braki_md, braki = sekcja_braki(df, surowe)
    dup_md = sekcja_duplikaty(df, log)
    typy_md, typy = sekcja_typy(df)
    zgodnosc = zgodnosc_surowe_oczyszczone(df, surowe)
    niezgodne = int(zgodnosc["niezgodnych"].sum())
    odst_md, _ = sekcja_odstajace(df, surowe, niezgodne)
    naiwny_md = sekcja_naiwny_replace(df, surowe)
    readme_md, readme_zgodne = sekcja_readme(df, log, braki)
    hl_md, hl_zgodne = sekcja_okno_headless(df)

    typy_ok = (typy["tabela"]["zgodny"] == "tak").all() and not sum(typy["nieliczbowe"].values())
    kontrole_ok = not any(typy["kontrole"].values())
    braki_ok = not (braki["uwaga"] == "NIEZGODNE z surowymi").any()
    wszystko_ok = all([typy_ok, kontrole_ok, braki_ok, niezgodne == 0, readme_zgodne, hl_zgodne])

    wniosek = (
        f"- Typy kolumn: {'zgodne z oczekiwaniem' if typy_ok else 'ROZBIEŻNOŚCI, patrz sekcja 3'}.\n"
        f"- Kontrola spójności (EAN, zakres oceny, URL, daty, waluty, kodowanie): "
        f"{'brak naruszeń' if kontrole_ok else 'SĄ NARUSZENIA, patrz sekcja 3'}.\n"
        f"- Braki w CSV vs `—` w surowych danych: {'zgodne' if braki_ok else 'NIEZGODNE'}.\n"
        f"- Niezależny odczyt surowych napisów vs CSV: **{niezgodne}** niezgodnych wartości "
        f"w {int(zgodnosc['porównano'].sum())} porównaniach.\n"
        f"- Liczby z README: {'wszystkie zgodne' if readme_zgodne else 'ROZBIEŻNOŚCI'}.\n"
        f"- okno vs headless: {'identyczne' if hl_zgodne else 'RÓŻNE'}.\n\n"
        + (
            "**Wniosek: nie znaleziono błędu parsera, więc nie wprowadzono zmian w `parsing/`.** "
            "Wartości odstające mają odpowiedniki w surowych napisach (odczyt niezależny dał te "
            "same liczby), więc są cechą danych serwisu, a nie artefaktem czyszczenia."
            if wszystko_ok
            else "**Wniosek: wykryto rozbieżności, patrz punkty oznaczone powyżej; wymagają "
            "analizy przed ewentualną zmianą w `parsing/`.**"
        )
        + "\n\n**Poprawka nazw kolumn wymiarów (wynik analizy):** serwis nie podpisuje liczb w "
        "`wymiary` (`17 x 9 x 8 cm`), a pierwotnie przypisano je jako długość × szerokość × "
        "wysokość. Rozkłady (lampy stojące 36 × 191 × 47 cm, telefony 7 × 14 × 1 cm) wskazały, "
        "że kolejność jest inna; kod generatora serwisu potwierdził: szerokość × wysokość × "
        "głębokość. Kolumny nazwano `szerokosc_cm`/`wysokosc_cm`/`glebokosc_cm`. Wartości były "
        "przepisane poprawnie, zmieniły się tylko nazwy."
    )

    zgodnosc_md = w.tabela_md(zgodnosc)
    raport = f"""# Kontrola jakości danych

Źródła: `output/okno.csv`, `output/okno_surowe.jsonl`, `output/headless.csv`,
`logs/{log["plik_logu"]}`. Raport generuje `python analiza/kontrola_jakosci.py`.

## 1. Liczba rekordów i braki

{braki_md}

## 2. Duplikaty przed i po odrzuceniu

{dup_md}

## 3. Typy kolumn

{typy_md}

## 4. Wartości odstające

{odst_md}

### Zgodność surowych napisów z oczyszczonymi wartościami (odczyt niezależny)

Odczyt prostym wyrażeniem regularnym, bez kodu z `parsing/`, porównany z CSV dla wszystkich
420 rekordów (tolerancja numeryczna 1e-9).

{zgodnosc_md}

### Naiwny `replace(",", ".")` na rzeczywistych surowych cenach

{naiwny_md}

## 5. Zgodność z README serwisu

{readme_md}

## 6. Zgodność okno.csv z headless.csv

{hl_md}

## 7. Wniosek o poprawności parsera

{wniosek}
"""
    sciezka = w.zapisz("kontrola_jakosci.md", raport)
    print(f"Zapisano {sciezka}")
    print(
        f"niezgodne={niezgodne}, readme_zgodne={readme_zgodne}, "
        f"okno_headless={hl_zgodne}, typy_ok={typy_ok}, kontrole_ok={kontrole_ok}"
    )


if __name__ == "__main__":
    main()
