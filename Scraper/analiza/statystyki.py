"""Statystyki opisowe, histogramy, box-ploty i korelacje cech liczbowych katalogu.

Uruchomienie: `python analiza/statystyki.py`. Wyniki: `analiza/wyniki/statystyki.md` oraz
wykresy PNG (dpi 150) w `analiza/wykresy/`. Waluty NIE są przeliczane: ceny analizujemy
osobno dla PLN (próba główna), a EUR i USD opisujemy osobno (mała próba).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wspolne as w

# Kolory z domyślnej palety (jedna barwa serii, reszta to atrament i tło).
SERIA = "#2a78d6"
SERIA_JASNA = "#cfe0f6"
TEKST = "#0b0b0b"
TEKST_DRUGI = "#52514e"
SIATKA = "#e3e2de"
TLO = "#fcfcfb"
DPI = 150

CECHY_OPISOWE = [
    ("ocena", "ocena (0-5)"),
    ("liczba_opinii", "liczba opinii"),
    ("gwarancja_mies", "gwarancja (mies.)"),
    ("waga_kg", "waga (kg)"),
    ("szerokosc_cm", "szerokość (cm)"),
    ("wysokosc_cm", "wysokość (cm)"),
    ("glebokosc_cm", "głębokość (cm)"),
    ("stan_magazynowy_szt", "stan magazynowy (szt.)"),
    ("czas_dostawy_dni", "czas dostawy (dni)"),
    ("koszt_dostawy", "koszt dostawy"),
    ("zwrot_dni", "zwrot (dni)"),
]


def _styl() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": TLO,
            "axes.facecolor": TLO,
            "savefig.facecolor": TLO,
            "axes.edgecolor": SIATKA,
            "axes.labelcolor": TEKST_DRUGI,
            "axes.titlecolor": TEKST,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.titlelocation": "left",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": SIATKA,
            "grid.linewidth": 0.8,
            "axes.axisbelow": True,
            "xtick.color": TEKST_DRUGI,
            "ytick.color": TEKST_DRUGI,
            "text.color": TEKST,
            "font.family": "DejaVu Sans",
            "font.size": 10,
        }
    )


def _spacje(wartosc: float, _pozycja: int | None = None) -> str:
    return f"{wartosc:,.0f}".replace(",", " ")


def opis(seria: pd.Series) -> dict[str, Any]:
    """Statystyki opisowe jednej cechy (moda: wszystkie wartości o max. częstości, do 3)."""
    s = seria.dropna()
    mody = s.mode().tolist()
    moda = ", ".join(f"{m:g}" for m in mody[:3]) + (" …" if len(mody) > 3 else "")
    if len(mody) == len(s.unique()) and len(s) > 1:
        moda += " (wszystkie wartości różne)"
    return {
        "n": len(s),
        "średnia": s.mean(),
        "mediana": s.median(),
        "moda": moda,
        "Q1": s.quantile(0.25),
        "Q3": s.quantile(0.75),
        "min": s.min(),
        "max": s.max(),
        "odch. std.": s.std(),
    }


def tabela_opisowa(pozycje: list[tuple[str, pd.Series]]) -> pd.DataFrame:
    wiersze = [{"cecha": nazwa, **opis(seria)} for nazwa, seria in pozycje]
    return pd.DataFrame(wiersze)


def wykres_histogram_ceny(pln: pd.Series, sciezka: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    biny = np.geomspace(pln.min(), pln.max(), 26)
    ax.hist(pln, bins=biny, color=SERIA, edgecolor=TLO, linewidth=1.2)
    ax.set_xscale("log")
    mediana = pln.median()
    ax.axvline(mediana, color=TEKST_DRUGI, linestyle="--", linewidth=1.2)
    ax.annotate(
        f"mediana {_spacje(mediana)} zł",
        xy=(mediana, ax.get_ylim()[1]),
        xytext=(6, -14),
        textcoords="offset points",
        color=TEKST_DRUGI,
        fontsize=10,
    )
    ax.xaxis.set_major_formatter(FuncFormatter(_spacje))
    ax.set_xticks([10, 30, 100, 300, 1000, 3000, 10000])
    ax.set_title(f"Rozkład cen produktów w PLN (n = {len(pln)})")
    ax.set_xlabel("Cena [zł], skala logarytmiczna")
    ax.set_ylabel("Liczba produktów")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(sciezka, dpi=DPI)
    plt.close(fig)


def wykres_histogram_oceny(ocena: pd.Series, sciezka: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))
    biny = np.arange(2.5, 5.01, 0.25)
    ax.hist(ocena.dropna(), bins=biny, color=SERIA, edgecolor=TLO, linewidth=1.2)
    mediana = ocena.median()
    ax.axvline(mediana, color=TEKST_DRUGI, linestyle="--", linewidth=1.2)
    ax.annotate(
        f"mediana {mediana:.1f}".replace(".", ","),
        xy=(mediana, ax.get_ylim()[1]),
        xytext=(6, -14),
        textcoords="offset points",
        color=TEKST_DRUGI,
    )
    ax.set_title(f"Rozkład ocen produktów (n = {int(ocena.notna().sum())}, bez braków)")
    ax.set_xlabel("Ocena (skala 0-5)")
    ax.set_ylabel("Liczba produktów")
    ax.grid(axis="x", visible=False)
    fig.tight_layout()
    fig.savefig(sciezka, dpi=DPI)
    plt.close(fig)


def wykres_box_kategorie(pln: pd.DataFrame, sciezka: Path) -> pd.DataFrame:
    kolejnosc = pln.groupby("kategoria")["cena"].median().sort_values().index.tolist()
    dane = [pln.loc[pln["kategoria"] == k, "cena"] for k in kolejnosc]
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.boxplot(
        dane,
        orientation="horizontal",
        tick_labels=kolejnosc,
        patch_artist=True,
        boxprops={"facecolor": SERIA_JASNA, "edgecolor": SERIA, "linewidth": 1.4},
        medianprops={"color": TEKST, "linewidth": 2},
        whiskerprops={"color": SERIA, "linewidth": 1.2},
        capprops={"color": SERIA, "linewidth": 1.2},
        flierprops={
            "marker": "o",
            "markerfacecolor": SERIA,
            "markeredgecolor": TLO,
            "markersize": 5,
            "alpha": 0.8,
        },
    )
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(FuncFormatter(_spacje))
    ax.set_xticks([10, 30, 100, 300, 1000, 3000, 10000, 30000])
    ax.set_title(f"Ceny produktów w PLN według kategorii (n = {len(pln)})")
    ax.set_xlabel("Cena [zł], skala logarytmiczna (linia = mediana, punkty = odstające wg IQR)")
    ax.set_ylabel("Kategoria")
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    fig.savefig(sciezka, dpi=DPI)
    plt.close(fig)
    return pln.groupby("kategoria")["cena"].agg(["count", "median", "min", "max"]).loc[kolejnosc]


def korelacja(x: pd.Series, y: pd.Series) -> dict[str, Any]:
    ramka = pd.concat([x, y], axis=1).dropna()
    a, b = ramka.iloc[:, 0], ramka.iloc[:, 1]
    return {
        "n": len(ramka),
        "Pearson": a.corr(b, method="pearson"),
        # Spearman = Pearson rang (rangi uśrednione przy remisach); bez zależności od scipy
        "Spearman": a.rank().corr(b.rank()),
        # przybliżony próg |r| istotnego na poziomie 5% (test dwustronny, duże n)
        "próg 5%": 1.96 / np.sqrt(len(ramka) - 1),
    }


def _rangi_w_kategorii(ramka: pd.DataFrame, kx: str, ky: str) -> tuple[pd.Series, pd.Series]:
    """Rangi percentylowe cech liczone osobno w każdej kategorii (usuwa wpływ kategorii)."""
    d = ramka[[kx, ky, "kategoria"]].dropna()
    grupy = d.groupby("kategoria")
    return grupy[kx].rank(pct=True), grupy[ky].rank(pct=True)


def eta_kwadrat(ramka: pd.DataFrame) -> float:
    """Udział wariancji log10(ceny) wyjaśniany przez kategorię (eta^2, ANOVA jednoczynnikowa)."""
    y = np.log10(ramka["cena"])
    srednia = y.mean()
    grupy = ramka.assign(y=y).groupby("kategoria")["y"].agg(["count", "mean"])
    miedzy = (grupy["count"] * (grupy["mean"] - srednia) ** 2).sum()
    return float(miedzy / ((y - srednia) ** 2).sum())


def sila(r: float) -> str:
    a = abs(r)
    if a < 0.1:
        return "pomijalna"
    if a < 0.3:
        return "słaba"
    if a < 0.5:
        return "umiarkowana"
    return "silna"


def wykres_korelacje(pary: list[tuple[pd.DataFrame, str, str, str, str]], sciezka: Path) -> None:
    fig, osie = plt.subplots(1, len(pary), figsize=(5.2 * len(pary), 4.8))
    for ax, (ramka, kx, ky, ex, ey) in zip(osie, pary, strict=True):
        d = ramka[[kx, ky]].dropna()
        ax.scatter(d[kx], d[ky], s=34, color=SERIA, alpha=0.6, edgecolor=TLO, linewidth=0.8)
        k = korelacja(d[kx], d[ky])
        ax.set_title(
            f"{ey} a {ex.lower()}\nPearson {k['Pearson']:.2f}, Spearman {k['Spearman']:.2f} "
            f"(n = {k['n']})".replace(".", ","),
            fontsize=11,
        )
        ax.set_xlabel(ex)
        ax.set_ylabel(ey)
        if kx == "cena":
            ax.set_xscale("log")
            ax.xaxis.set_major_formatter(FuncFormatter(_spacje))
        elif kx == "liczba_opinii":
            # zera i jeden rekord rzędu 10^4: skala symlog (liniowa do 10, potem logarytmiczna)
            ax.set_xscale("symlog", linthresh=10)
            ax.set_xticks([0, 10, 100, 1000, 10000])
            ax.xaxis.set_major_formatter(FuncFormatter(_spacje))
    fig.tight_layout()
    fig.savefig(sciezka, dpi=DPI)
    plt.close(fig)


def main() -> None:
    w.ustaw_utf8()
    _styl()
    w.WYKRESY.mkdir(parents=True, exist_ok=True)
    df = w.wczytaj_csv()
    pln = df[df["waluta"] == "PLN"]
    eur = df[df["waluta"] == "EUR"]
    usd = df[df["waluta"] == "USD"]

    # --- tabele opisowe -------------------------------------------------------------------
    ceny = tabela_opisowa(
        [
            (f"cena PLN [zł], n={len(pln)}", pln["cena"]),
            (f"cena EUR [€], n={len(eur)}", eur["cena"]),
            (f"cena USD [$], n={len(usd)}", usd["cena"]),
        ]
    )
    cechy = tabela_opisowa([(etykieta, df[k]) for k, etykieta in CECHY_OPISOWE])
    waluta_dostawy = df["waluta_dostawy"].value_counts().to_dict()

    # --- wykresy -------------------------------------------------------------------------
    wykres_histogram_ceny(pln["cena"], w.WYKRESY / "hist_cena_pln.png")
    wykres_histogram_oceny(df["ocena"], w.WYKRESY / "hist_ocena.png")
    kat = wykres_box_kategorie(pln, w.WYKRESY / "box_cena_pln_kategoria.png")

    # --- korelacje -----------------------------------------------------------------------
    plnx = pln.copy()
    pary_def = [
        ("cena PLN – ocena", plnx["cena"], plnx["ocena"], "dodatnia"),
        ("cena PLN – waga_kg", plnx["cena"], plnx["waga_kg"], "dodatnia"),
        ("liczba_opinii – ocena (wszystkie)", df["liczba_opinii"], df["ocena"], "dodatnia"),
        (
            "liczba_opinii – ocena (bez max. liczby opinii)",
            df.loc[df["liczba_opinii"] < df["liczba_opinii"].max(), "liczba_opinii"],
            df.loc[df["liczba_opinii"] < df["liczba_opinii"].max(), "ocena"],
            "dodatnia",
        ),
        (
            "cena PLN – waga_kg (rangi w obrębie kategorii)",
            *_rangi_w_kategorii(plnx, "cena", "waga_kg"),
            "dodatnia",
        ),
        ("cena PLN – stan_magazynowy_szt", plnx["cena"], plnx["stan_magazynowy_szt"], "ujemna"),
        ("cena PLN – liczba_opinii", plnx["cena"], plnx["liczba_opinii"], "ujemna"),
    ]
    wiersze_kor = []
    for nazwa, x, y, oczekiwana in pary_def:
        k = korelacja(x, y)
        wiersze_kor.append(
            {
                "para": nazwa,
                "n": k["n"],
                "Pearson": k["Pearson"],
                "Spearman": k["Spearman"],
                "siła (wg Spearmana)": sila(k["Spearman"]),
                "próg istotności 5% (≈)": k["próg 5%"],
                "oczekiwany znak": oczekiwana,
                "istotna": "tak" if abs(k["Spearman"]) > k["próg 5%"] else "nie",
            }
        )
    kor = pd.DataFrame(wiersze_kor)
    wykres_korelacje(
        [
            (plnx, "cena", "ocena", "Cena [zł]", "Ocena"),
            (plnx, "cena", "waga_kg", "Cena [zł]", "Waga [kg]"),
            (df, "liczba_opinii", "ocena", "Liczba opinii", "Ocena"),
        ],
        w.WYKRESY / "korelacje.png",
    )

    # --- opis słowny korelacji (zależny od wyniku) ------------------------------------
    komentarze = []
    for _, r in kor.iterrows():
        znak = "dodatnia" if r["Spearman"] > 0 else "ujemna"
        zgodny = (
            "zgodny z intuicją"
            if znak == r["oczekiwany znak"] and r["istotna"] == "tak"
            else "niezgodny lub niewykazany"
        )
        komentarze.append(
            f"- **{r['para']}**: Spearman {r['Spearman']:.3f} ({r['siła (wg Spearmana)']}, "
            f"{znak}, {'istotna' if r['istotna'] == 'tak' else 'nieistotna'} przy n={r['n']}), "
            f"Pearson {r['Pearson']:.3f}. Wynik {zgodny} (hipoteza: zależność "
            f"{r['oczekiwany znak']})."
        )
    komentarze_md = "\n".join(komentarze)
    eta2 = eta_kwadrat(pln)
    wiersz_waga = kor[kor["para"] == "cena PLN – waga_kg"].iloc[0]
    wiersz_waga_kat = kor[kor["para"].str.contains("w obrębie kategorii")].iloc[0]
    wiersz_op = kor[kor["para"] == "liczba_opinii – ocena (wszystkie)"].iloc[0]
    wiersz_op_bez = kor[kor["para"].str.contains("bez max")].iloc[0]
    wiersz_ocena = kor[kor["para"] == "cena PLN – ocena"].iloc[0]
    pomijalne = kor[kor["siła (wg Spearmana)"] == "pomijalna"]["para"].tolist()
    mediany = kat["median"]

    # --- fragmenty opisowe danych --------------------------------------------------------
    najdrozsza = kat.index[-1]
    najtansza = kat.index[0]
    cena_pln = opis(pln["cena"])
    skosnosc = float(pln["cena"].skew())
    iqr_ocena = opis(df["ocena"])

    tresc = f"""# Statystyki opisowe i wykresy

Źródło: `output/okno.csv` ({len(df)} rekordów). Raport generuje `python analiza/statystyki.py`.

## 1. Wybór próby: dlaczego ceny osobno według walut

Ceny występują w trzech walutach: PLN ({len(pln)}), EUR ({len(eur)}) i USD ({len(usd)}). Nie
przeliczamy ich kursem, bo serwis jest fikcyjny i nie ma kursu źródłowego: każdy przyjęty kurs
byłby arbitralnym założeniem, które zmieniłoby wszystkie statystyki. Cenę analizujemy więc
**osobno dla PLN** ({len(pln)} rekordów, {100 * len(pln) / len(df):.1f}% katalogu), a EUR i USD
opisujemy tylko tabelą statystyk opisowych: próby {len(eur)} i {len(usd)} są za małe na
wykresy według kategorii (10 kategorii, średnio kilka rekordów na kategorię) i na wiarygodne
korelacje. Cechy niezwiązane z walutą (ocena, waga, wymiary, stany, czasy) liczymy na
wszystkich {len(df)} rekordach. Koszt dostawy: waluty dostawy w danych to
{", ".join(f"{k} ({v})" for k, v in waluta_dostawy.items())}.

## 2. Statystyki opisowe cen (osobno według walut)

{w.tabela_md(ceny)}

Cena PLN: średnia {cena_pln["średnia"]:.2f} zł wobec mediany {cena_pln["mediana"]:.2f} zł,
skośność {skosnosc:.2f}. Rozkład jest silnie prawoskośny (średnia ciągnięta w górę przez kilka
drogich produktów), dlatego do opisu „typowej” ceny używamy mediany i kwartyli, a wykresy
rysujemy w skali logarytmicznej.

## 3. Statystyki opisowe pozostałych cech liczbowych (wszystkie rekordy)

{w.tabela_md(cechy)}

Uwagi: `n` mniejsze niż {len(df)} oznacza braki (ocena, gwarancja, waga). Moda cech ciągłych
(waga, wymiary) bywa przypadkowa (przy remisach pokazano do trzech wartości), więc do opisu
tych cech służą mediana i kwartyle.
Kolumny wymiarów (szerokość, wysokość, głębokość) odpowiadają kolejności liczb w tekście
serwisu; nazwy ustalono po analizie rozkładów, patrz `kontrola_jakosci.md`, sekcja 7.

## 4. Wykresy

### Histogram ceny PLN
![Histogram cen PLN](../wykresy/hist_cena_pln.png)

W skali logarytmicznej rozkład jest szeroki (min {_spacje(float(cena_pln["min"]))} zł,
max {_spacje(float(cena_pln["max"]))} zł, mediana {_spacje(float(cena_pln["mediana"]))} zł) z
długim prawym ogonem i bez jednego wyraźnego szczytu (kilka sąsiednich przedziałów o
podobnej liczności), co wiąże się z mieszaniem kategorii o różnych poziomach cen (box-plot
niżej).

### Histogram oceny
![Histogram ocen](../wykresy/hist_ocena.png)

Oceny skupiają się wokół mediany {iqr_ocena["mediana"]:.1f} (Q1 {iqr_ocena["Q1"]:.1f},
Q3 {iqr_ocena["Q3"]:.1f}); {int(df["ocena"].isna().sum())} produktów nie ma oceny i
nie jest uwzględnionych.

### Box-plot ceny PLN według kategorii
![Box-plot cen PLN według kategorii](../wykresy/box_cena_pln_kategoria.png)

Mediany cen według kategorii (rosnąco):

{w.tabela_md(kat.reset_index().rename(columns={"kategoria": "kategoria", "count": "n", "median": "mediana", "min": "min", "max": "max"}))}

Najniższą medianę ma „{najtansza}” ({mediany.iloc[0]:g} zł), najwyższą „{najdrozsza}”
({mediany.iloc[-1]:g} zł), czyli {mediany.iloc[-1] / mediany.iloc[0]:.1f}× więcej. Kategoria
wyjaśnia {100 * eta2:.1f}% wariancji log10(ceny) (eta², ANOVA jednoczynnikowa); dla
porównania kwadrat Spearmana ceny z wagą to {wiersz_waga["Spearman"] ** 2:.3f}. Pudełka
kategorii nakładają się, więc sama kategoria nie wyznacza ceny.

## 5. Korelacje

Współczynniki Pearsona (zależność liniowa, wrażliwy na odstające) i Spearmana (zależność
monotoniczna, oparty na rangach). „Próg istotności” to przybliżony próg |r| ≈ 1,96/√(n−1)
dla poziomu 5%; wartość poniżej progu jest nieodróżnialna od zera.

{w.tabela_md(kor)}

![Wykresy rozrzutu korelowanych cech](../wykresy/korelacje.png)

### Komentarz

{komentarze_md}

**Interpretacja.** Dane są fikcyjne i generowane losowo, więc brak korelacji tam, gdzie
rzeczywisty rynek miałby zależność, jest wynikiem do omówienia, a nie wadą parsera
(odczyt niezależny w `kontrola_jakosci.md`: 0 niezgodności).

- **Bez zależności** ({len(pomijalne)} z {len(kor)} par: {"; ".join(pomijalne)}): współczynniki
  są poniżej progu istotności. Cena nie niesie informacji o ocenie (Spearman
  {wiersz_ocena["Spearman"]:.2f}), a liczba opinii nie niesie informacji o ocenie
  ({wiersz_op["Spearman"]:.2f}). Na rynku spodziewalibyśmy się dodatniej zależności ceny od
  jakości i liczby opinii od popularności; jej brak wskazuje, że generator losował te cechy
  niezależnie.
- **Cena a waga**: Spearman {wiersz_waga["Spearman"]:.2f} (n={wiersz_waga["n"]}) jest istotny
  i dodatni, więc generator wiązał wagę z ceną lub z kategorią. Po usunięciu efektu kategorii
  (rangi w obrębie kategorii) zależność wynosi {wiersz_waga_kat["Spearman"]:.2f}
  (próg ≈ {wiersz_waga_kat["próg istotności 5% (≈)"]:.2f}), czyli
  {"pozostaje istotna" if wiersz_waga_kat["istotna"] == "tak" else "zanika"}. Merytorycznie
  ma to sens: cięższe towary (AGD, sprzęt sportowy, dom i ogród) są droższe, ale RTV i
  elektronika bywają lekkie i drogie, stąd tylko umiarkowana siła.
- **Rekord z największą liczbą opinii** zmienia Pearsona liczby opinii z oceną z
  {wiersz_op["Pearson"]:.3f} (z rekordem) na {wiersz_op_bez["Pearson"]:.3f} (bez), a Spearmana
  z {wiersz_op["Spearman"]:.3f} na {wiersz_op_bez["Spearman"]:.3f}: wniosek nie zależy od
  tego rekordu.
"""
    sciezka = w.zapisz("statystyki.md", tresc)
    print(f"Zapisano {sciezka}")
    for plik in sorted(w.WYKRESY.glob("*.png")):
        print(f"Wykres {plik.name}")


if __name__ == "__main__":
    main()
