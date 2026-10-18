"""Buduje sprawozdanie PDF z docs/SPRAWOZDANIE.md i docs/OPIS_SERWISU.md.

Uruchomienie z katalogu głównego projektu: `python sprawozdanie/buduj_pdf.py`.
Wynik: sprawozdanie/LAB1_sprawozdanie.pdf (druk przez Chrome, headless).
"""

import base64
import html
import re
import sys
from pathlib import Path

import markdown
from selenium.webdriver.common.print_page_options import PrintOptions

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from bajtoparser.utils.driver import otworz_driver

DOCS = ROOT / "docs"
WYKRESY = ROOT / "analiza" / "wykresy"
WYNIK = Path(__file__).resolve().parent / "LAB1_sprawozdanie.pdf"

AUTOR_PARSERA = "Michał Langner"
AUTOR_SERWISU = "Jakub Nawrocki"

# Wykresy wstawiane przed akapitem o korelacjach (sekcja 5).
ZNACZNIK_WYKRESOW = "**Korelacje** (n po"
WYKRESY_PODPISY = [
    ("hist_cena_pln.png", "Histogram ceny PLN (skala logarytmiczna)"),
    ("hist_ocena.png", "Histogram oceny"),
    ("box_cena_pln_kategoria.png", "Box-plot ceny PLN według kategorii"),
    ("korelacje.png", "Wykresy rozrzutu korelowanych cech"),
]

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Segoe UI", "DejaVu Sans", Arial, sans-serif; font-size: 10pt;
       line-height: 1.4; color: #111; }
h1 { font-size: 17pt; } h2 { font-size: 14pt; margin-top: 1.3em;
     border-bottom: 1px solid #888; padding-bottom: 2px; }
h3 { font-size: 11.5pt; } h2, h3 { break-after: avoid; }
table { border-collapse: collapse; margin: 0.6em 0; width: 100%; font-size: 8.5pt; }
th, td { border: 1px solid #555; padding: 3px 5px; vertical-align: top;
         overflow-wrap: break-word; }
th { background: #e8e8e8; } tr { break-inside: avoid; }
code { font-family: Consolas, "DejaVu Sans Mono", monospace; font-size: 8.5pt;
       background: #f2f2f2; padding: 0 2px; overflow-wrap: break-word; }
figure { margin: 0.8em 0; text-align: center; break-inside: avoid; }
figure img { max-width: 100%; max-height: 105mm; }
figcaption { font-size: 8.5pt; color: #333; }
.tytul { height: 255mm; display: flex; flex-direction: column;
         justify-content: center; text-align: center; break-after: page; }
.tytul h1 { font-size: 26pt; border: none; }
.tytul p { font-size: 13pt; margin: 0.3em 0; }
"""


def usun_robocze(tekst: str) -> tuple[str, list[str]]:
    """Usuwa uwagę o szkicu, znaczniki robocze i listę zbiorczą. Zwraca też usunięte fragmenty."""
    usuniete: list[str] = []

    def wytnij(wzorzec: str, opis: str, flagi: int = 0) -> None:
        nonlocal tekst
        trafienie = re.search(wzorzec, tekst, flagi)
        if trafienie is None:
            raise ValueError(f"Nie znaleziono fragmentu do usunięcia: {opis}")
        usuniete.append(f"[{opis}]\n{trafienie.group(0).strip()}")
        tekst = tekst[: trafienie.start()] + tekst[trafienie.end() :]

    # Nagłówek dokumentu (zastępuje go strona tytułowa) i nagłówkowa uwaga o szkicu.
    wytnij(r"\A# [^\n]*\n+", "tytuł szkicu")
    wytnij(r"\A(?:>[^\n]*\n)+\n*", "uwaga nagłówkowa o szkicu")
    # Lista zbiorcza "do uzupełnienia" wraz z zastrzeżeniami do końca pliku i linią ---.
    wytnij(
        r"\n---\s*\n+### Lista \[DO UZUPEŁNIENIA\].*\Z", "lista zbiorcza do uzupełnienia", re.DOTALL
    )
    if re.search(r"DO UZUPEŁNIENIA|\(szkic\)", tekst):
        raise ValueError("W treści zostały znaczniki robocze")
    return tekst.rstrip() + "\n", usuniete


def md_do_html(tekst: str) -> str:
    """Renderuje Markdown do HTML (tabele, bloki kodu)."""
    # Python-Markdown wymaga pustej linii przed listą, a szkic jej nie zawsze ma.
    tekst = re.sub(r"^([^\s\-\d>|#][^\n]*)\n(- |\d+\. )", r"\1\n\n\2", tekst, flags=re.MULTILINE)
    return markdown.markdown(tekst, extensions=["tables", "fenced_code"])


def wstaw_wykresy(tekst: str) -> str:
    """Wstawia wykresy z analiza/wykresy/ przed akapitem o korelacjach."""
    if ZNACZNIK_WYKRESOW not in tekst:
        raise ValueError("Brak miejsca na wykresy w sekcji 5")
    figury = []
    for plik, podpis in WYKRESY_PODPISY:
        sciezka = WYKRESY / plik
        if not sciezka.exists():
            raise FileNotFoundError(sciezka)
        figury.append(
            f'<figure><img src="{sciezka.as_uri()}" alt="{html.escape(podpis)}">'
            f"<figcaption>{html.escape(podpis)}</figcaption></figure>"
        )
    return tekst.replace(
        ZNACZNIK_WYKRESOW, "\n" + "\n".join(figury) + "\n\n" + ZNACZNIK_WYKRESOW, 1
    )


def zloz_html(sprawozdanie: str, opis: str) -> str:
    """Składa stronę tytułową, opis serwisu i sprawozdanie w jeden dokument HTML."""
    tytulowa = (
        '<section class="tytul"><h1>Laboratorium 1: parser strony www</h1>'
        "<p>Rola: PARSER</p>"
        f"<p>Autor parsera: {html.escape(AUTOR_PARSERA)}</p>"
        f"<p>Autor serwisu: {html.escape(AUTOR_SERWISU)}</p></section>"
    )
    return (
        '<!doctype html><html lang="pl"><head><meta charset="utf-8">'
        "<title>LAB1 sprawozdanie</title>"
        f"<style>{CSS}</style></head><body>{tytulowa}"
        f'<div class="opis">{md_do_html(opis)}</div>{md_do_html(wstaw_wykresy(sprawozdanie))}'
        "</body></html>"
    )


def drukuj_pdf(plik_html: Path, plik_pdf: Path) -> None:
    """Drukuje stronę HTML do PDF przez Chrome (headless, A4)."""
    opcje = PrintOptions()
    opcje.page_width, opcje.page_height = 21.0, 29.7
    opcje.margin_top = opcje.margin_bottom = 1.8
    opcje.margin_left = opcje.margin_right = 1.6
    opcje.background = True
    with otworz_driver(headless=True) as driver:
        driver.get(plik_html.as_uri())
        plik_pdf.write_bytes(base64.b64decode(driver.print_page(opcje)))


def main() -> None:
    """Czyta Markdown, usuwa znaczniki robocze, renderuje i zapisuje PDF."""
    surowe = (DOCS / "SPRAWOZDANIE.md").read_text(encoding="utf-8")
    opis = (DOCS / "OPIS_SERWISU.md").read_text(encoding="utf-8")
    sprawozdanie, usuniete = usun_robocze(surowe)
    print("USUNIĘTO Z TREŚCI:")
    for fragment in usuniete:
        print(fragment, "\n---")
    plik_html = WYNIK.with_suffix(".tmp.html")
    plik_html.write_text(zloz_html(sprawozdanie, opis), encoding="utf-8")
    try:
        drukuj_pdf(plik_html, WYNIK)
    finally:
        plik_html.unlink(missing_ok=True)
    print(f"Zapisano {WYNIK}")


if __name__ == "__main__":
    main()
