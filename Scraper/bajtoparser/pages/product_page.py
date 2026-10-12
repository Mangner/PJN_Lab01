"""Strona produktu (Page Object): wejście po URL-u, otwarcie zakładek, odczyt 13 pól.

Zwraca surowe stringi i `None` (brak elementu); czyszczenie jest w `parsing/`. Strona
niczego nie połyka: gdy produkt nie istnieje albo zakładka się nie wypełni, po wyczerpaniu
prób `@ponawiaj` zapisuje diagnostykę i rzuca wyjątek dalej (zlicza go pipeline).
"""

from typing import Any, ClassVar, TypedDict
from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from bajtoparser.pages.base_page import BasePage, Lokator
from bajtoparser.utils.konfiguracja import KONFIGURACJA
from bajtoparser.utils.retry import ponawiaj


class SzczegolyProduktu(TypedDict):
    """Surowe szczegóły ze strony produktu (13 pól); brak elementu w DOM to `None`."""

    opis: str | None
    ean: str | None
    kod_producenta: str | None
    kolor: str | None
    material: str | None
    waga: str | None
    wymiary: str | None
    kraj_pochodzenia: str | None
    sprzedawca: str | None
    stan_magazynowy: str | None
    czas_dostawy: str | None
    koszt_dostawy: str | None
    zwrot: str | None


def url_produktu(adres_serwisu: str, url: str | None) -> str:
    """Zwraca pełny adres produktu z `href` rekordu listy (względnego albo pełnego).

    Pusty lub `None` adres to `ValueError`: rekord bez `url` nie ma strony do odwiedzenia.
    """
    if not url or not url.strip():
        raise ValueError("rekord nie ma adresu url produktu")
    baza = adres_serwisu.rstrip("/") + "/"
    return urljoin(baza, url.strip())


class ProductPage(BasePage):
    """Strona `produkt/<id>.html`: opis od razu, pola specyfikacji i dostawy po kliknięciu.

    `@ponawiaj` stoi osobno na `otworz_produkt` i `otworz_zakladke` (każda woła tylko
    wersje bez retry: `_otworz`, `_kliknij`). Metoda zbiorcza `pobierz_szczegoly` nie ma
    dekoratora, więc próby się nie mnożą.
    """

    # Znaczniki stanu [DOM] w docs/SELEKTORY.md
    BODY: Lokator = (By.TAG_NAME, "body")
    ATR_STAN_RENDERU = "data-stan-renderu"
    STAN_GOTOWY = "gotowy"
    ATR_WYPELNIONE = "data-wypelnione"
    WARTOSC_WYPELNIONE = "tak"

    # Panele i zakładki: nazwa -> (przycisk zakładki, panel)
    SEL_PANEL_OPIS = "#panel-opis"
    ZAKLADKI: ClassVar[dict[str, tuple[str, str]]] = {
        "specyfikacja": ('button.zakladka[data-panel="specyfikacja"]', "#panel-specyfikacja"),
        "dostawa": ('button.zakladka[data-panel="dostawa"]', "#panel-dostawa"),
    }
    SEL_POLE_PANELU = "dd"

    # Pola w panelach: nazwa pola -> selektor `dd.<klasa>`
    POLA_SPECYFIKACJA: ClassVar[dict[str, str]] = {
        "ean": ".ean",
        "kod_producenta": ".kod-producenta",
        "kolor": ".kolor",
        "material": ".material",
        "waga": ".waga",
        "wymiary": ".wymiary",
        "kraj_pochodzenia": ".kraj-pochodzenia",
    }
    POLA_DOSTAWA: ClassVar[dict[str, str]] = {
        "sprzedawca": ".sprzedawca",
        "stan_magazynowy": ".stan-magazynowy",
        "czas_dostawy": ".czas-dostawy",
        "koszt_dostawy": ".koszt-dostawy",
        "zwrot": ".zwrot",
    }

    # Skrypty statyczne: selektory dostają z Pythona (`arguments[0]`).
    # `textContent`, bo `.text` zwraca '' dla elementów w ukrytym panelu.
    _JS_SZCZEGOLY = """
        const k = arguments[0];
        const tekst = (el) => (el ? el.textContent.trim() : null);
        const wynik = {opis: tekst(document.querySelector(k.panel_opis))};
        for (const grupa of k.grupy) {
            const panel = document.querySelector(grupa.panel);
            for (const [klucz, selektor] of Object.entries(grupa.pola)) {
                wynik[klucz] = panel ? tekst(panel.querySelector(selektor)) : null;
            }
        }
        return wynik;
    """

    _JS_STAN_PANELI = """
        const k = arguments[0];
        const wynik = {};
        for (const [nazwa, selektor] of Object.entries(k.panele)) {
            const panel = document.querySelector(selektor);
            wynik[nazwa] = panel
                ? Array.from(panel.querySelectorAll(k.pole)).filter(
                      (e) => e.textContent.trim() !== ''
                  ).length
                : 0;
        }
        return wynik;
    """

    def __init__(
        self,
        driver: WebDriver,
        adres_serwisu: str | None = None,
        timeout_s: float | None = None,
        poll_s: float | None = None,
        pauza_s: float | None = None,
    ) -> None:
        super().__init__(driver, timeout_s=timeout_s, poll_s=poll_s, pauza_s=pauza_s)
        self.adres_serwisu = adres_serwisu or KONFIGURACJA.adres_serwisu

    @ponawiaj()
    def otworz_produkt(self, url: str) -> None:
        """Otwiera stronę produktu (`url` z rekordu listy) i czeka na `data-stan-renderu="gotowy"`.

        Brak strony (404) kończy się `TimeoutException` po wyczerpaniu prób; wyjątek idzie dalej.
        """
        self._otworz(url_produktu(self.adres_serwisu, url))
        self.czekaj_na_atrybut(self.BODY, self.ATR_STAN_RENDERU, self.STAN_GOTOWY)

    @ponawiaj()
    def otworz_zakladke(self, nazwa: str) -> None:
        """Klika zakładkę (`specyfikacja` | `dostawa`) i czeka na `data-wypelnione="tak"` panelu.

        Nieznana nazwa to `ValueError` (przed jakimkolwiek klikaniem, bez retry).
        """
        if nazwa not in self.ZAKLADKI:
            raise ValueError(f"nieznana zakładka: {nazwa!r}")
        przycisk, panel = self.ZAKLADKI[nazwa]
        self._kliknij((By.CSS_SELECTOR, przycisk))
        self.czekaj_na_atrybut(
            (By.CSS_SELECTOR, panel), self.ATR_WYPELNIONE, self.WARTOSC_WYPELNIONE
        )

    def stan_paneli(self) -> dict[str, int]:
        """Zwraca liczbę niepustych pól `dd` w panelach `specyfikacja` i `dostawa`.

        Przed kliknięciem zakładki wynik to 0 (panel pusty), po kliknięciu: 7 i 5.
        """
        parametry: dict[str, Any] = {
            "panele": {nazwa: panel for nazwa, (_, panel) in self.ZAKLADKI.items()},
            "pole": self.SEL_POLE_PANELU,
        }
        return self.driver.execute_script(self._JS_STAN_PANELI, parametry)

    def pobierz_pola(self) -> SzczegolyProduktu:
        """Zwraca 13 surowych pól jedną migawką (`execute_script`); wołać po otwarciu zakładek.

        Brak elementu (albo panelu) daje `None`; wartość `—` zostaje surowa (brak danych
        zamienia `parsing/`).
        """
        parametry: dict[str, Any] = {
            "panel_opis": self.SEL_PANEL_OPIS,
            "grupy": [
                {"panel": self.ZAKLADKI["specyfikacja"][1], "pola": self.POLA_SPECYFIKACJA},
                {"panel": self.ZAKLADKI["dostawa"][1], "pola": self.POLA_DOSTAWA},
            ],
        }
        return self.driver.execute_script(self._JS_SZCZEGOLY, parametry)

    def pobierz_szczegoly(self, url: str) -> SzczegolyProduktu:
        """Otwiera produkt, obie zakładki (osobno, z retry) i zwraca 13 pól.

        Wyjątki (po wyczerpaniu prób) przechodzą dalej; łapie je pipeline.
        """
        self.otworz_produkt(url)
        self.otworz_zakladke("specyfikacja")
        self.otworz_zakladke("dostawa")
        return self.pobierz_pola()
