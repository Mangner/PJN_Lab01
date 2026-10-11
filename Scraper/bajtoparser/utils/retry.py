"""Dekorator retry z backoffem wykładniczym (1 s, 2 s, 4 s) i limitem prób.

Dekorator stawiamy tylko na metodach najwyższego poziomu, bez zagnieżdżania: zagnieżdżone
dekoratory mnożą próby i zapisują diagnostykę wielokrotnie.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any, ParamSpec, TypeVar

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    StaleElementReferenceException,
    TimeoutException,
)

from bajtoparser.utils import timing
from bajtoparser.utils.diagnostyka import zapisz_diagnostyke
from bajtoparser.utils.konfiguracja import KONFIGURACJA
from bajtoparser.utils.logowanie import LICZNIK_RETRY

log = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")

WYJATKI_PONAWIANE: tuple[type[Exception], ...] = (
    TimeoutException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
)


def ponawiaj(
    max_prob: int | None = None, baza_s: float | None = None
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Dekorator ponawiający wywołanie przy wyjątkach z `WYJATKI_PONAWIANE`.

    Opóźnienia (przez `utils/timing.py`) wynoszą baza, 2*baza, 4*baza... Po wyczerpaniu
    prób zapisuje diagnostykę (gdy pierwszy argument ma atrybut `driver`) i rzuca wyjątek dalej.
    Inne wyjątki przechodzą od razu, bez ponowień.
    """

    def dekorator(funkcja: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(funkcja)
        def opakowana(*args: P.args, **kwargs: P.kwargs) -> R:
            limit = KONFIGURACJA.max_prob if max_prob is None else max_prob
            if limit < 1:
                raise ValueError("max_prob musi być >= 1")
            nazwa = funkcja.__qualname__
            for proba in range(1, limit + 1):
                try:
                    return funkcja(*args, **kwargs)
                except WYJATKI_PONAWIANE as blad:
                    if proba == limit:
                        log.error("%s: wyczerpano %d prób (%s)", nazwa, limit, type(blad).__name__)
                        _zapisz_diagnostyke(args, nazwa)
                        raise
                    LICZNIK_RETRY.zwieksz()
                    opoznienie = timing.czekaj_backoff(proba, baza_s)
                    log.warning(
                        "%s: próba %d/%d nieudana (%s), ponowienie za %.1f s",
                        nazwa,
                        proba,
                        limit,
                        type(blad).__name__,
                        opoznienie,
                    )
            raise AssertionError("nieosiągalne")  # pragma: no cover

        return opakowana

    return dekorator


def _zapisz_diagnostyke(args: tuple[Any, ...], operacja: str) -> None:
    """Zapisuje diagnostykę, jeśli obiekt (pierwszy argument) ma `driver`."""
    driver = getattr(args[0], "driver", None) if args else None
    if driver is not None:
        zapisz_diagnostyke(driver, operacja)
