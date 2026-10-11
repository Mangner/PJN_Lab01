"""Jedyne miejsce w projekcie, w którym wolno czekać na sztywno (opóźnienia, backoff).

Faktyczne czekanie wykonuje podmienialna funkcja `_czekaj`; testy podmieniają ją przez
`ustaw_funkcje_czekania`, żeby nie czekać naprawdę.
"""

import time
from collections.abc import Callable

from bajtoparser.utils.konfiguracja import KONFIGURACJA, MIN_PAUZA_GRZECZNOSCIOWA_S

FunkcjaCzekania = Callable[[float], None]

_czekaj: FunkcjaCzekania = time.sleep


def ustaw_funkcje_czekania(funkcja: FunkcjaCzekania) -> FunkcjaCzekania:
    """Podmienia funkcję czekania i zwraca poprzednią (do przywrócenia)."""
    global _czekaj
    poprzednia = _czekaj
    _czekaj = funkcja
    return poprzednia


def przywroc_funkcje_czekania() -> None:
    """Przywraca prawdziwe czekanie."""
    global _czekaj
    _czekaj = time.sleep


def czekaj(sekundy: float) -> None:
    """Czeka podaną liczbę sekund przez aktualną funkcję czekania."""
    if sekundy > 0:
        _czekaj(sekundy)


def pauza_grzecznosciowa(pauza_s: float | None = None) -> float:
    """Pauza między żądaniami; nie krótsza niż 0,5 s. Zwraca faktyczną długość pauzy."""
    zadana = KONFIGURACJA.pauza_s if pauza_s is None else pauza_s
    pauza = max(zadana, MIN_PAUZA_GRZECZNOSCIOWA_S)
    czekaj(pauza)
    return pauza


def opoznienie_backoff(nr_proby: int, baza_s: float | None = None) -> float:
    """Opóźnienie po nieudanej próbie `nr_proby` (od 1): baza * 2**(nr_proby - 1), czyli 1, 2, 4 s."""
    if nr_proby < 1:
        raise ValueError("nr_proby musi być >= 1")
    baza = KONFIGURACJA.backoff_baza_s if baza_s is None else baza_s
    return baza * 2 ** (nr_proby - 1)


def czekaj_backoff(nr_proby: int, baza_s: float | None = None) -> float:
    """Czeka zgodnie z backoffem wykładniczym i zwraca długość opóźnienia."""
    opoznienie = opoznienie_backoff(nr_proby, baza_s)
    czekaj(opoznienie)
    return opoznienie
