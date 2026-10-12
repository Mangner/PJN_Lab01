"""Interfejs wiersza poleceń: argparse i składanie obiektów (bez selenium).

Kody wyjścia: 0 sukces, 1 błędy częściowe (lub przerwanie), 2 błąd krytyczny.
"""

import argparse
import dataclasses
import logging
import urllib.error
import urllib.request
from collections.abc import Sequence
from pathlib import Path

from bajtoparser.pages.catalog_page import CatalogPage
from bajtoparser.pages.product_page import ProductPage
from bajtoparser.pipeline import Pipeline
from bajtoparser.porownanie import (
    DaneDom,
    linia_porownania,
    porownaj,
    wniosek,
    zapisz_json,
)
from bajtoparser.utils.driver import otworz_driver
from bajtoparser.utils.konfiguracja import (
    KONFIGURACJA,
    MIN_PAUZA_GRZECZNOSCIOWA_S,
    Konfiguracja,
)
from bajtoparser.utils.logowanie import PodsumowaniePrzebiegu, skonfiguruj_logowanie

log = logging.getLogger("bajtoparser.cli")

KOD_SUKCES = 0
KOD_BLEDY_CZESCIOWE = 1
KOD_BLAD_KRYTYCZNY = 2

TIMEOUT_SPRAWDZENIA_S = 3.0
"""Limit czasu jednego żądania sprawdzającego, czy serwis odpowiada."""


def _liczba_dodatnia(tekst: str) -> int:
    """Typ argparse: liczba całkowita >= 1."""
    try:
        wartosc = int(tekst)
    except ValueError:
        raise argparse.ArgumentTypeError(f"to nie jest liczba całkowita: {tekst!r}") from None
    if wartosc < 1:
        raise argparse.ArgumentTypeError(f"wartość musi być >= 1, podano {wartosc}")
    return wartosc


def _sekundy_dodatnie(tekst: str) -> float:
    """Typ argparse: liczba sekund > 0."""
    try:
        wartosc = float(tekst.replace(",", "."))
    except ValueError:
        raise argparse.ArgumentTypeError(f"to nie jest liczba: {tekst!r}") from None
    if wartosc <= 0:
        raise argparse.ArgumentTypeError(f"wartość musi być > 0, podano {wartosc}")
    return wartosc


def zbuduj_parser() -> argparse.ArgumentParser:
    """Tworzy parser argumentów Bajtoparsera."""
    parser = argparse.ArgumentParser(
        prog="bajtoparser",
        description="Scraper katalogu Bajtomarket (Selenium + Chrome), eksport do CSV i JSON.",
    )
    parser.add_argument(
        "--adres",
        default=KONFIGURACJA.adres_serwisu,
        help="adres serwisu (domyślnie %(default)s)",
    )
    parser.add_argument(
        "--strony",
        type=_liczba_dodatnia,
        default=None,
        help="liczba podstron listy do przetworzenia (domyślnie wszystkie)",
    )
    parser.add_argument(
        "--limit",
        type=_liczba_dodatnia,
        default=None,
        help="liczba unikalnych produktów do przetworzenia (domyślnie wszystkie)",
    )
    parser.add_argument("--headless", action="store_true", help="Chrome bez okna")
    parser.add_argument(
        "--porownanie",
        action="store_true",
        help="po przebiegu porównaj liczbę rekordów w surowym HTML (urllib) z DOM",
    )
    parser.add_argument(
        "--wyjscie",
        default=KONFIGURACJA.nazwa_wyjscia,
        help="nazwa bazowa plików wyjściowych (domyślnie %(default)s)",
    )
    parser.add_argument(
        "--katalog-wyjscia",
        type=Path,
        default=KONFIGURACJA.katalog_wyjscia,
        help="katalog plików wyjściowych (domyślnie %(default)s)",
    )
    parser.add_argument(
        "--pauza",
        type=_sekundy_dodatnie,
        default=KONFIGURACJA.pauza_s,
        help=(
            "pauza grzecznościowa między żądaniami w s; wartość poniżej "
            f"{MIN_PAUZA_GRZECZNOSCIOWA_S} jest podnoszona (domyślnie %(default)s)"
        ),
    )
    parser.add_argument(
        "--timeout",
        type=_sekundy_dodatnie,
        default=KONFIGURACJA.timeout_s,
        help="limit czasu oczekiwania na stan strony w s (domyślnie %(default)s)",
    )
    return parser


def zbuduj_konfiguracje(argumenty: argparse.Namespace) -> Konfiguracja:
    """Składa `Konfiguracja` z argumentów; pauzę poniżej minimum podnosi z ostrzeżeniem."""
    pauza = argumenty.pauza
    if pauza < MIN_PAUZA_GRZECZNOSCIOWA_S:
        log.warning(
            "Pauza %.2f s jest poniżej minimum, używam %.2f s", pauza, MIN_PAUZA_GRZECZNOSCIOWA_S
        )
        pauza = MIN_PAUZA_GRZECZNOSCIOWA_S
    return dataclasses.replace(
        KONFIGURACJA,
        adres_serwisu=argumenty.adres,
        strony=argumenty.strony,
        limit=argumenty.limit,
        headless=argumenty.headless,
        nazwa_wyjscia=argumenty.wyjscie,
        katalog_wyjscia=argumenty.katalog_wyjscia,
        pauza_s=pauza,
        timeout_s=argumenty.timeout,
    )


def serwis_odpowiada(adres: str, timeout_s: float = TIMEOUT_SPRAWDZENIA_S) -> bool:
    """Czy serwis odpowiada na jedno żądanie HTTP (bez przeglądarki)."""
    try:
        with urllib.request.urlopen(adres, timeout=timeout_s) as odpowiedz:
            return 200 <= odpowiedz.status < 400
    except (urllib.error.URLError, OSError, ValueError):
        return False


def main(argv: Sequence[str] | None = None) -> int:
    """Punkt wejścia programu; zwraca kod wyjścia (0, 1 albo 2)."""
    argumenty = zbuduj_parser().parse_args(argv)
    sciezka_logu = skonfiguruj_logowanie()
    konfiguracja = zbuduj_konfiguracje(argumenty)
    log.info("Log: %s; konfiguracja: %s", sciezka_logu, konfiguracja)

    if not serwis_odpowiada(konfiguracja.adres_serwisu):
        log.error(
            "Serwis nie odpowiada pod adresem %s. Uruchom go (python -m http.server 8000 "
            "w katalogu Web-App) i spróbuj ponownie.",
            konfiguracja.adres_serwisu,
        )
        return KOD_BLAD_KRYTYCZNY

    try:
        with otworz_driver(konfiguracja.headless, konfiguracja) as driver:
            parametry_stron = {
                "adres_serwisu": konfiguracja.adres_serwisu,
                "timeout_s": konfiguracja.timeout_s,
                "pauza_s": konfiguracja.pauza_s,
            }
            pipeline = Pipeline(
                CatalogPage(driver, **parametry_stron),
                ProductPage(driver, **parametry_stron),
                konfiguracja,
            )
            podsumowanie = pipeline.uruchom()
    except KeyboardInterrupt:
        log.warning("Przerwano przed rozpoczęciem przebiegu")
        return KOD_BLEDY_CZESCIOWE
    except Exception:
        # Jedyne miejsce łapiące dowolny wyjątek: zamiana na kod wyjścia 2 z pełnym śladem.
        log.exception("Błąd krytyczny, przebieg przerwany")
        return KOD_BLAD_KRYTYCZNY

    if argumenty.porownanie:
        _porownaj_html_z_dom(konfiguracja, podsumowanie)

    if podsumowanie.bledy or podsumowanie.przerwano:
        return KOD_BLEDY_CZESCIOWE
    return KOD_SUKCES


def _porownaj_html_z_dom(konfiguracja: Konfiguracja, podsumowanie: PodsumowaniePrzebiegu) -> None:
    """Zestawia surowy HTML (urllib) z liczbami DOM z przebiegu i zapisuje JSON.

    Dodatek do przebiegu: błąd sieci daje ostrzeżenie w logu i nie zmienia kodu wyjścia.
    Czas porównania nie wchodzi do czasu przebiegu (jest liczony po jego zakończeniu).
    """
    przetworzone = podsumowanie.strony + len(podsumowanie.pominiete_strony)
    wynik = porownaj(
        konfiguracja.adres_serwisu,
        max(przetworzone, 1),
        podsumowanie.probka_produktow,
        timeout_s=konfiguracja.timeout_s,
        pauza_s=konfiguracja.pauza_s,
    )
    dom = DaneDom.z_podsumowania(podsumowanie)
    linia = linia_porownania(wynik, dom)
    sciezka = zapisz_json(wynik, dom, konfiguracja.katalog_wyjscia, konfiguracja.nazwa_wyjscia)
    log.info(linia)
    log.info("WNIOSEK: %s", wniosek(wynik, dom))
    log.info("Porównanie zapisano do %s", sciezka)
    if wynik.bledy_sieci:
        log.warning("Porównanie niepełne: %d stron nie pobrano", wynik.bledy_sieci)
