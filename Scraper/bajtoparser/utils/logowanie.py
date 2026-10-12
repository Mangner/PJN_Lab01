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
    """Podsumowanie przebiegu: strony, rekordy, błędy, retry, czas działania i tryb.

    `rekordy` to liczba rekordów w eksporcie; pola dodatkowe opisują kontrolę jakości:
    pozycje na liście przed i po deduplikacji, duplikaty różniące się od oryginału,
    nierozpoznane wartości (nieznany format, nie brak danych) i produkty ze szczegółami.
    """

    tryb: str
    strony: int = 0
    rekordy: int = 0
    bledy: int = 0
    retry: int = 0
    rekordy_lista: int = 0
    rekordy_po_dedup: int = 0
    duplikaty: int = 0
    duplikaty_rozne: int = 0
    nierozpoznane: int = 0
    ze_szczegolami: int = 0
    podstrony_w_serwisie: int = 0
    pozycje_zrodlo: dict[str, int] = field(default_factory=dict)
    probka_produktow: list[dict[str, str | None]] = field(default_factory=list)
    pominiete_strony: list[int] = field(default_factory=list)
    przerwano: bool = False
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
            f"błędów={self.bledy}, retry={self.retry}, czas={self.czas_s:.2f} s; "
            f"lista={self.rekordy_lista}, po deduplikacji={self.rekordy_po_dedup}, "
            f"duplikatów={self.duplikaty} (różnych od oryginału: {self.duplikaty_rozne}), "
            f"ze szczegółami={self.ze_szczegolami}, nierozpoznanych={self.nierozpoznane}, "
            f"pominięte podstrony={self.pominiete_strony or '-'}, "
            f"przerwano={'tak' if self.przerwano else 'nie'}"
        )

    def linia_przebiegu(self) -> str:
        """Zwraca wyraźną linię trybu i czasu do zestawiania przebiegów (okno vs headless)."""
        czas = self.czas_s
        minuty, sekundy = divmod(round(czas), 60)
        na_rekord = f"{czas / self.rekordy:.2f}" if self.rekordy else "-"
        return (
            f"PRZEBIEG: tryb={self.tryb} | czas={czas:.2f} s ({minuty:02d}:{sekundy:02d}) | "
            f"rekordów={self.rekordy} | s/rekord={na_rekord}"
        )

    def zapisz_do_logu(self, logger: logging.Logger | None = None) -> None:
        """Zapisuje podsumowanie i linię trybu/czasu do logu."""
        cel = logger or log
        cel.info(self.jako_tekst())
        cel.info(self.linia_przebiegu())
