"""Strona bazowa (Page Object): sterownik, jawne oczekiwania i metody pomocnicze.

Selektory trzymają klasy potomne. Synchronizacja odbywa się wyłącznie przez
`WebDriverWait` i `expected_conditions`.
"""

from weakref import WeakSet

from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from bajtoparser.utils import timing
from bajtoparser.utils.konfiguracja import KONFIGURACJA
from bajtoparser.utils.retry import ponawiaj

Lokator = tuple[str, str]
"""Para (strategia, selektor), np. `(By.CSS_SELECTOR, "#wczytaj-wiecej")`."""

_STEROWNIKI_Z_ZADANIEM: WeakSet = WeakSet()
"""Sterowniki, które wykonały już żądanie: sesja (driver) może mieć wiele stron."""


class _AtrybutElementu:
    """Warunek oczekiwania: atrybut elementu istnieje albo ma dokładnie daną wartość."""

    def __init__(self, lokator: Lokator, atrybut: str, wartosc: str | None) -> None:
        self.lokator = lokator
        self.atrybut = atrybut
        self.wartosc = wartosc

    def __call__(self, driver: WebDriver) -> str | bool:
        aktualna = driver.find_element(*self.lokator).get_attribute(self.atrybut)
        if aktualna is None:
            return False
        if self.wartosc is None or aktualna == self.wartosc:
            return aktualna or True
        return False


class _WzrostAtrybutu:
    """Warunek oczekiwania: atrybut liczbowy jest większy od wartości początkowej."""

    def __init__(self, lokator: Lokator, atrybut: str, poczatkowa: int) -> None:
        self.lokator = lokator
        self.atrybut = atrybut
        self.poczatkowa = poczatkowa

    def __call__(self, driver: WebDriver) -> int | bool:
        tekst = driver.find_element(*self.lokator).get_attribute(self.atrybut)
        try:
            wartosc = int(tekst) if tekst is not None else None
        except ValueError:
            return False
        if wartosc is not None and wartosc > self.poczatkowa:
            return wartosc
        return False


class BasePage:
    """Wspólna logika stron: nawigacja, oczekiwania, klikanie z retry, bezpieczny tekst.

    UWAGA: `@ponawiaj` stoi tylko na metodach najwyższego poziomu (`otworz`, `kliknij`)
    i nie jest zagnieżdżany: metoda z `@ponawiaj` nie woła innej metody z `@ponawiaj`.
    Inaczej próby by się mnożyły, a diagnostyka zapisywałaby się wielokrotnie. Metody
    `czekaj_*` są bez dekoratora (retry nakłada na nie wywołujący na najwyższym poziomie).
    """

    def __init__(
        self,
        driver: WebDriver,
        timeout_s: float | None = None,
        poll_s: float | None = None,
        pauza_s: float | None = None,
    ) -> None:
        self.driver = driver
        self.timeout_s = KONFIGURACJA.timeout_s if timeout_s is None else timeout_s
        self.poll_s = KONFIGURACJA.poll_s if poll_s is None else poll_s
        self.pauza_s = KONFIGURACJA.pauza_s if pauza_s is None else pauza_s
        self.wait = WebDriverWait(
            driver,
            self.timeout_s,
            poll_frequency=self.poll_s,
            ignored_exceptions=(NoSuchElementException, StaleElementReferenceException),
        )

    def _otworz(self, url: str) -> None:
        """Otwiera adres URL bez retry (do użycia w metodach z własnym `@ponawiaj`).

        Przed każdym żądaniem poza pierwszym w sesji (na danym driverze) robi pauzę
        grzecznościową; dotyczy to także ponowień po błędzie.
        """
        if self.driver in _STEROWNIKI_Z_ZADANIEM:
            timing.pauza_grzecznosciowa(self.pauza_s)
        _STEROWNIKI_Z_ZADANIEM.add(self.driver)
        self.driver.get(url)

    @ponawiaj()
    def otworz(self, url: str) -> None:
        """Otwiera adres URL (z retry przy przekroczeniu czasu ładowania)."""
        self._otworz(url)

    def czekaj_na_element(self, lokator: Lokator, widoczny: bool = False) -> WebElement:
        """Czeka na obecność (lub widoczność) elementu i zwraca go."""
        warunek = (
            EC.visibility_of_element_located(lokator)
            if widoczny
            else EC.presence_of_element_located(lokator)
        )
        return self.wait.until(warunek)

    def czekaj_na_atrybut(
        self, lokator: Lokator, atrybut: str, wartosc: str | None = None
    ) -> str | bool:
        """Czeka, aż atrybut elementu pojawi się (lub osiągnie `wartosc`); zwraca jego wartość."""
        return self.wait.until(_AtrybutElementu(lokator, atrybut, wartosc))

    def pobierz_atrybut(self, lokator: Lokator, atrybut: str) -> str | None:
        """Zwraca aktualną wartość atrybutu elementu (`None`, gdy brak atrybutu)."""
        return self.driver.find_element(*lokator).get_attribute(atrybut)

    def czekaj_na_wzrost_atrybutu(self, lokator: Lokator, atrybut: str, poczatkowa: int) -> int:
        """Czeka, aż atrybut liczbowy przekroczy `poczatkowa`; zwraca nową wartość."""
        return self.wait.until(_WzrostAtrybutu(lokator, atrybut, poczatkowa))

    def _kliknij(self, lokator: Lokator) -> None:
        """Czeka, aż element będzie klikalny, i klika go (bez retry)."""
        self.wait.until(EC.element_to_be_clickable(lokator)).click()

    @ponawiaj()
    def kliknij(self, lokator: Lokator) -> None:
        """Czeka, aż element będzie klikalny, i klika go (z retry)."""
        self._kliknij(lokator)

    def tekst(self, lokator: Lokator, domyslny: str | None = None) -> str | None:
        """Zwraca tekst elementu albo `domyslny`, gdy elementu nie ma w DOM (bez czekania).

        Łapie tylko `NoSuchElementException`: `TimeoutException` i inne błędy przechodzą dalej,
        żeby nieudane ładowanie strony nie wyglądało jak brak danych.
        """
        try:
            return self.driver.find_element(*lokator).text
        except NoSuchElementException:
            return domyslny
