"""Testy utils/timing.py (bez realnego czekania)."""

import pytest

from bajtoparser.utils import timing


def test_pauza_grzecznosciowa_domyslnie_co_najmniej_pol_sekundy(opoznienia):
    assert timing.pauza_grzecznosciowa() >= 0.5
    assert opoznienia == [0.5]


def test_pauza_grzecznosciowa_nie_schodzi_ponizej_minimum(opoznienia):
    assert timing.pauza_grzecznosciowa(0.1) == 0.5
    assert opoznienia == [0.5]


def test_pauza_grzecznosciowa_pozwala_wydluzyc(opoznienia):
    timing.pauza_grzecznosciowa(1.5)
    assert opoznienia == [1.5]


def test_backoff_wykladniczy_1_2_4():
    assert [timing.opoznienie_backoff(n) for n in (1, 2, 3)] == [1.0, 2.0, 4.0]


def test_backoff_odrzuca_numer_proby_ponizej_1():
    with pytest.raises(ValueError):
        timing.opoznienie_backoff(0)


def test_czekaj_backoff_uzywa_podmienionej_funkcji(opoznienia):
    timing.czekaj_backoff(1)
    timing.czekaj_backoff(2)
    assert opoznienia == [1.0, 2.0]


def test_przywroc_funkcje_czekania():
    zapisane: list[float] = []
    timing.ustaw_funkcje_czekania(zapisane.append)
    timing.przywroc_funkcje_czekania()
    assert timing._czekaj is not zapisane.append
