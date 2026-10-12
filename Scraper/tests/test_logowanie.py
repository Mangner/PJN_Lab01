"""Testy utils/logowanie.py: plik logu i podsumowanie przebiegu."""

import logging
import re

import pytest

from bajtoparser.utils.logowanie import (
    LICZNIK_RETRY,
    PodsumowaniePrzebiegu,
    nazwa_trybu,
    skonfiguruj_logowanie,
    wylacz_logowanie,
)


@pytest.fixture
def logi(tmp_path):
    sciezka = skonfiguruj_logowanie(tmp_path)
    yield sciezka
    wylacz_logowanie()


def test_plik_logu_ma_znacznik_czasu_i_zawiera_wpisy(logi):
    assert re.fullmatch(r"bajtoparser_\d{8}_\d{6}\.log", logi.name)
    logging.getLogger("bajtoparser.test").info("Zażółć gęślą jaźń")
    for uchwyt in logging.getLogger("bajtoparser").handlers:
        uchwyt.flush()
    assert "Zażółć gęślą jaźń" in logi.read_text(encoding="utf-8")


def test_podsumowanie_zawiera_wszystkie_pola():
    czasy = iter([100.0, 112.5])
    p = PodsumowaniePrzebiegu(tryb=nazwa_trybu(True), zegar=lambda: next(czasy))
    p.strony, p.rekordy, p.bledy = 6, 420, 1
    LICZNIK_RETRY.zwieksz()
    LICZNIK_RETRY.zwieksz()
    p.zakoncz()
    tekst = p.jako_tekst()
    for fragment in ("headless", "stron=6", "rekordów=420", "błędów=1", "retry=2", "12.50 s"):
        assert fragment in tekst


def test_linia_przebiegu_ma_tryb_czas_i_czas_na_rekord(caplog):
    czasy = iter([0.0, 113.88])
    p = PodsumowaniePrzebiegu(tryb="okno", zegar=lambda: next(czasy))
    p.rekordy = 143
    p.zakoncz()
    linia = p.linia_przebiegu()
    assert linia.startswith("PRZEBIEG: tryb=okno | czas=113.88 s (01:54)")
    assert "rekordów=143" in linia and "s/rekord=0.80" in linia

    with caplog.at_level(logging.INFO, logger=__name__):
        p.zapisz_do_logu(logging.getLogger(__name__))
    assert [r.message.split(":")[0] for r in caplog.records] == ["PODSUMOWANIE", "PRZEBIEG"]


def test_linia_przebiegu_bez_rekordow_nie_dzieli_przez_zero():
    p = PodsumowaniePrzebiegu(tryb="headless")
    p.zakoncz()
    assert "s/rekord=-" in p.linia_przebiegu()


def test_nazwa_trybu():
    assert nazwa_trybu(False) == "okno"
    assert nazwa_trybu(True) == "headless"


def test_licznik_retry_resetuj():
    LICZNIK_RETRY.zwieksz()
    LICZNIK_RETRY.resetuj()
    assert LICZNIK_RETRY.wartosc == 0
