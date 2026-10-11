"""Fabryka sterownika Chrome (Selenium Manager sam pobiera chromedriver)."""

from collections.abc import Iterator
from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from bajtoparser.utils.konfiguracja import KONFIGURACJA, Konfiguracja

LOCALE = "pl-PL"


def zbuduj_opcje(headless: bool, konfiguracja: Konfiguracja = KONFIGURACJA) -> Options:
    """Buduje opcje Chrome: headless, polskie locale, rozmiar okna."""
    opcje = Options()
    if headless:
        opcje.add_argument("--headless=new")
    opcje.add_argument(f"--lang={LOCALE}")
    opcje.add_argument(f"--window-size={konfiguracja.szerokosc_okna},{konfiguracja.wysokosc_okna}")
    opcje.add_experimental_option("prefs", {"intl.accept_languages": LOCALE})
    opcje.add_experimental_option("excludeSwitches", ["enable-logging"])
    return opcje


def utworz_driver(headless: bool, konfiguracja: Konfiguracja = KONFIGURACJA) -> webdriver.Chrome:
    """Tworzy sterownik Chrome. Zamknięciem (`quit()`) zajmuje się kod wywołujący."""
    return webdriver.Chrome(options=zbuduj_opcje(headless, konfiguracja))


@contextmanager
def otworz_driver(
    headless: bool, konfiguracja: Konfiguracja = KONFIGURACJA
) -> Iterator[webdriver.Chrome]:
    """Menedżer kontekstu: tworzy sterownik i zawsze go zamyka."""
    driver = utworz_driver(headless, konfiguracja)
    try:
        yield driver
    finally:
        driver.quit()
