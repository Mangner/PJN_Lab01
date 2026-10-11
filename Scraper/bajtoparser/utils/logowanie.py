"""Logowanie do pliku i na konsolę, licznik retry oraz podsumowanie przebiegu."""

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from bajtoparser.utils.konfiguracja import KONFIGURACJA

NAZWA_LOGGERA = "bajtoparser"
FORMAT_LOGU = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"

log = logging.getLogger(__name__)


class LicznikRetry:
    """Globalny licznik ponowień (każde opóźnienie backoffu to jedno ponowienie)."""

    def __init__(self) -> None:
        self.wartosc = 0

    def zwieksz(self) -> None:
        """Zwiększa licznik o jeden."""
        self.wartosc += 1

    def resetuj(self) -> None:
        """Zeruje licznik (początek przebiegu, testy)."""
        self.wartosc = 0


LICZNIK_RETRY = LicznikRetry()


def nazwa_trybu(headless: bool) -> str:
    """Zwraca nazwę trybu do podsumowania: `headless` albo `okno`."""
    return "headless" if headless else "okno"


def skonfiguruj_logowanie(katalog: Path | None = None, poziom: int = logging.INFO) -> Path:
    """Konfiguruje logger pakietu: plik `logs/bajtoparser_<znacznik>.log` i konsola.

    Zwraca ścieżkę pliku logu. Ponowne wywołanie zastępuje poprzednie uchwyty.
    """
    cel = Path(katalog) if katalog is not None else KONFIGURACJA.katalog_logow
    cel.mkdir(parents=True, exist_ok=True)
    sciezka = cel / f"bajtoparser_{datetime.now():%Y%m%d_%H%M%S}.log"

    wylacz_logowanie()
    logger = logging.getLogger(NAZWA_LOGGERA)
    logger.setLevel(poziom)
    formatter = logging.Formatter(FORMAT_LOGU)
    for uchwyt in (
        logging.FileHandler(sciezka, encoding="utf-8"),
        logging.StreamHandler(),
    ):
        uchwyt.setFormatter(formatter)
        logger.addHandler(uchwyt)
    return sciezka


def wylacz_logowanie() -> None:
    """Zamyka i odpina uchwyty loggera pakietu."""
    logger = logging.getLogger(NAZWA_LOGGERA)
    for uchwyt in list(logger.handlers):
        logger.removeHandler(uchwyt)
        uchwyt.close()


@dataclass
class PodsumowaniePrzebiegu:
    """Podsumowanie przebiegu: strony, rekordy, błędy, retry, czas działania i tryb."""

    tryb: str
    strony: int = 0
    rekordy: int = 0
    bledy: int = 0
    retry: int = 0
    zegar: Callable[[], float] = field(default=time.perf_counter, repr=False)
    _start: float = field(init=False, repr=False)
    _koniec: float | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._start = self.zegar()

    def zakoncz(self) -> None:
        """Zatrzymuje pomiar czasu i pobiera liczbę retry z globalnego licznika."""
        self._koniec = self.zegar()
        self.retry = LICZNIK_RETRY.wartosc

    @property
    def czas_s(self) -> float:
        """Czas działania w sekundach (do chwili `zakoncz()` albo do teraz)."""
        koniec = self._koniec if self._koniec is not None else self.zegar()
        return koniec - self._start

    def jako_tekst(self) -> str:
        """Zwraca podsumowanie w jednej linii."""
        return (
            f"PODSUMOWANIE: tryb={self.tryb}, stron={self.strony}, rekordów={self.rekordy}, "
            f"błędów={self.bledy}, retry={self.retry}, czas={self.czas_s:.2f} s"
        )

    def zapisz_do_logu(self, logger: logging.Logger | None = None) -> None:
        """Zapisuje podsumowanie do logu."""
        (logger or log).info(self.jako_tekst())
