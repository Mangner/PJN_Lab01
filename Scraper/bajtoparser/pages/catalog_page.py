"""Strona katalogu (Page Object): nawigacja po podstronach, doładowywanie, zbieranie rekordów.

Zwraca surowe stringi i `None`; czyszczenie wartości jest w `parsing/`. Jedyna ingerencja
w tekst to wycięcie prefiksu `span.etykieta` z kart (artefakt struktury strony).
"""

import re
from collections.abc import Iterable
from typing import Any, ClassVar, Literal, TypedDict

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from bajtoparser.pages.base_page import BasePage, Lokator
from bajtoparser.utils import timing
from bajtoparser.utils.konfiguracja import KONFIGURACJA
from bajtoparser.utils.retry import ponawiaj

_WZORZEC_PODSTRONY = re.compile(r"strona-(\d+)\.html")


class RekordListy(TypedDict):
    """Surowy rekord z listy; brak elementu w DOM to `None`."""

    id: str | None
    nazwa: str | None
    url: str | None
    cena: str | None
    waluta: str | None
    cena_poprzednia: str | None
    kategoria: str | None
    producent: str | None
    dostepnosc: str | None
    gwarancja: str | None
    ocena: str | None
    liczba_opinii: str | None
    data_dodania: str | None
    zrodlo: Literal["tabela", "karta"]


def url_podstrony(adres_serwisu: str, nr: int) -> str:
    """Zwraca adres podstrony: `index.html` dla 1, `strona-N.html` dla N > 1."""
    if nr < 1:
        raise ValueError("numer podstrony musi być >= 1")
    baza = adres_serwisu.rstrip("/") + "/"
    return baza + ("index.html" if nr == 1 else f"strona-{nr}.html")


def ustal_liczbe_podstron(hrefy: Iterable[str | None]) -> int:
    """Wyznacza liczbę podstron z linków paginacji: największe N z `strona-N.html`, min. 1."""
    numery = [1]
    for href in hrefy:
        if href and (dopasowanie := _WZORZEC_PODSTRONY.search(href)):
            numery.append(int(dopasowanie.group(1)))
    return max(numery)


def wczytano_wszystko(porcja: str | None, porcji_lacznie: str | None) -> bool:
    """Warunek końca doładowywania: `data-porcja` == `data-porcji-lacznie` (liczby)."""
    try:
        return int(porcja) == int(porcji_lacznie)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


class CatalogPage(BasePage):
    """Lista produktów: podstrony `index.html`, `strona-N.html`.

    `@ponawiaj` stoi na `otworz_podstrone` i `wczytaj_porcje` (metody najwyższego poziomu);
    wołają one wyłącznie wersje bez retry (`_otworz`, `_kliknij`), więc próby się nie mnożą.
    Pętla `wczytaj_wszystko` nie ma dekoratora: ponawianie jest per porcja.
    """

    # Znaczniki stanu (body), wszystkie [DOM] w docs/SELEKTORY.md
    BODY: Lokator = (By.TAG_NAME, "body")
    ATR_WCZYTANO = "data-wczytano"
    ATR_PORCJA = "data-porcja"
    ATR_PORCJI_LACZNIE = "data-porcji-lacznie"

    # Doładowywanie i paginacja
    PRZYCISK_WCZYTAJ: Lokator = (By.CSS_SELECTOR, "#wczytaj-wiecej")
    LINKI_PAGINACJI: Lokator = (By.CSS_SELECTOR, 'a[href*="strona-"]')

    # Rekordy: tabela (tr) i karty (article); używane w skrypcie JS jako selektory CSS
    SEL_WIERSZ = "tr.wiersz-produktu"
    SEL_KARTA = "article.produkt"
    SEL_ODNOSNIK = "a.odnosnik-produktu"
    SEL_ETYKIETA = ".etykieta"
    ATR_ID = "data-id"
    ATR_WALUTA = "data-waluta"
    ATR_HREF = "href"
    POLA: ClassVar[dict[str, str]] = {
        "cena": ".cena",
        "cena_poprzednia": ".cena-poprzednia",
        "kategoria": ".kategoria",
        "producent": ".producent",
        "dostepnosc": ".dostepnosc",
        "gwarancja": ".gwarancja",
        "ocena": ".ocena",
        "liczba_opinii": ".liczba-opinii",
        "data_dodania": ".data-dodania",
    }

    MAKS_PORCJI = 20
    """Twardy limit iteracji doładowywania (oczekiwane: 6 porcji na podstronę)."""

    # Skrypt statyczny: selektory dostaje z Pythona (`arguments[0]`), sam żadnych nie zawiera.
    _JS_REKORDY = """
        const k = arguments[0];
        const tekst = (el) => {
            if (!el) return null;
            const kopia = el.cloneNode(true);
            kopia.querySelectorAll(k.etykieta).forEach((e) => e.remove());
            return kopia.textContent.trim();
        };
        const rekord = (korzen, zrodlo) => {
            const odnosnik = korzen.querySelector(k.odnosnik);
            const cena = korzen.querySelector(k.selektor_ceny);
            const r = {
                id: korzen.getAttribute(k.atr_id),
                nazwa: tekst(odnosnik),
                url: odnosnik ? odnosnik.getAttribute(k.atr_href) : null,
                waluta: cena ? cena.getAttribute(k.atr_waluta) : null,
            };
            for (const [klucz, selektor] of Object.entries(k.pola)) {
                r[klucz] = tekst(korzen.querySelector(selektor));
            }
            r.zrodlo = zrodlo;
            return r;
        };
        return [
            ...Array.from(document.querySelectorAll(k.wiersz)).map((e) => rekord(e, 'tabela')),
            ...Array.from(document.querySelectorAll(k.karta)).map((e) => rekord(e, 'karta')),
        ];
    """

    def __init__(
        self,
        driver: WebDriver,
        adres_serwisu: str | None = None,
        timeout_s: float | None = None,
        poll_s: float | None = None,
    ) -> None:
        super().__init__(driver, timeout_s=timeout_s, poll_s=poll_s)
        self.adres_serwisu = adres_serwisu or KONFIGURACJA.adres_serwisu

    @ponawiaj()
    def otworz_podstrone(self, nr: int) -> None:
        """Otwiera podstronę `nr` i czeka na pierwszą porcję (`data-wczytano` > 0)."""
        self._otworz(url_podstrony(self.adres_serwisu, nr))
        self.czekaj_na_wzrost_atrybutu(self.BODY, self.ATR_WCZYTANO, 0)

    def liczba_podstron(self) -> int:
        """Liczba podstron ustalona z linków paginacji w aktualnym DOM-ie (min. 1)."""
        linki = self.driver.find_elements(*self.LINKI_PAGINACJI)
        return ustal_liczbe_podstron(link.get_attribute("href") for link in linki)

    def czy_wczytano_wszystko(self) -> bool:
        """Czy wszystkie porcje bieżącej podstrony są wczytane (po znacznikach `body`)."""
        return wczytano_wszystko(
            self.pobierz_atrybut(self.BODY, self.ATR_PORCJA),
            self.pobierz_atrybut(self.BODY, self.ATR_PORCJI_LACZNIE),
        )

    @ponawiaj()
    def wczytaj_porcje(self) -> int:
        """Wczytuje jedną porcję i zwraca nowe `data-wczytano`.

        Zapamiętuje `data-wczytano` przed kliknięciem i czeka na jego WZROST (flaga
        `data-wczytywanie` migocze, więc jej nie używamy). Jeśli podstrona jest już
        wczytana (np. po ponowieniu), niczego nie klika.
        """
        if self.czy_wczytano_wszystko():
            return int(self.pobierz_atrybut(self.BODY, self.ATR_WCZYTANO) or 0)
        poczatkowa = int(self.pobierz_atrybut(self.BODY, self.ATR_WCZYTANO) or 0)
        timing.pauza_grzecznosciowa()  # kliknięcie wyzwala fetch
        self._kliknij(self.PRZYCISK_WCZYTAJ)
        return self.czekaj_na_wzrost_atrybutu(self.BODY, self.ATR_WCZYTANO, poczatkowa)

    def wczytaj_wszystko(self) -> int:
        """Doładowuje porcje do wyczerpania i zwraca końcowe `data-wczytano`.

        Koniec to `data-porcja == data-porcji-lacznie` (przycisk po ostatniej porcji zostaje
        w DOM, więc nie jest podstawą warunku). Po `MAKS_PORCJI` iteracjach rzuca
        `RuntimeError` (zabezpieczenie przed zawieszeniem).
        """
        for _ in range(self.MAKS_PORCJI):
            if self.czy_wczytano_wszystko():
                return int(self.pobierz_atrybut(self.BODY, self.ATR_WCZYTANO) or 0)
            self.wczytaj_porcje()
        if self.czy_wczytano_wszystko():
            return int(self.pobierz_atrybut(self.BODY, self.ATR_WCZYTANO) or 0)
        raise RuntimeError(f"Doładowywanie nie zakończyło się po {self.MAKS_PORCJI} porcjach")

    def pobierz_rekordy(self) -> list[RekordListy]:
        """Zwraca surowe rekordy z całego DOM-u: najpierw tabela, potem karty (kolejność DOM).

        Jedno `execute_script` daje atomową migawkę (zamiast ~900 wywołań WebDrivera).
        Trzy rodzaje braku zostają rozróżnione w surowych danych:
        - element z klasą `brak-wartosci`: tekst `"—"` (brak danych: `producent`, `ocena`),
        - pusta komórka `.cena-poprzednia` w tabeli: `""` (brak promocji),
        - brak elementu `.cena-poprzednia` w karcie: `None` (brak promocji).
        Sprowadzenie do `None`/`NaN` robi `parsing/`. `url` to surowy `href` (względny).
        """
        parametry: dict[str, Any] = {
            "wiersz": self.SEL_WIERSZ,
            "karta": self.SEL_KARTA,
            "odnosnik": self.SEL_ODNOSNIK,
            "etykieta": self.SEL_ETYKIETA,
            "pola": self.POLA,
            "selektor_ceny": self.POLA["cena"],
            "atr_id": self.ATR_ID,
            "atr_waluta": self.ATR_WALUTA,
            "atr_href": self.ATR_HREF,
        }
        return self.driver.execute_script(self._JS_REKORDY, parametry)
