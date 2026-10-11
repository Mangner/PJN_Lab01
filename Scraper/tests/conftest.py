"""Wspólne fixture'y testów infrastruktury (bez przeglądarki)."""

import pytest

from bajtoparser.utils import timing
from bajtoparser.utils.logowanie import LICZNIK_RETRY


@pytest.fixture
def opoznienia():
    """Podmienia funkcję czekania i zwraca listę zarejestrowanych opóźnień (bez czekania)."""
    zapisane: list[float] = []
    poprzednia = timing.ustaw_funkcje_czekania(zapisane.append)
    yield zapisane
    timing.ustaw_funkcje_czekania(poprzednia)


@pytest.fixture(autouse=True)
def czysty_licznik_retry():
    """Zeruje globalny licznik retry przed i po każdym teście."""
    LICZNIK_RETRY.resetuj()
    yield
    LICZNIK_RETRY.resetuj()
