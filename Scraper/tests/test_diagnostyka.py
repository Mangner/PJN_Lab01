"""Testy utils/diagnostyka.py z atrapą drivera (bez przeglądarki)."""

import re
from datetime import datetime

from bajtoparser.utils.diagnostyka import nazwa_bazowa, zapisz_diagnostyke


class AtrapaDrivera:
    page_source = "<html><body>zażółć</body></html>"

    def save_screenshot(self, sciezka):
        with open(sciezka, "wb") as plik:
            plik.write(b"PNG")
        return True


def test_zapisuje_png_i_html_ze_znacznikiem_i_nazwa_operacji(tmp_path):
    png, html = zapisz_diagnostyke(AtrapaDrivera(), "CatalogPage.kliknij", tmp_path)
    assert png is not None and html is not None
    assert png.read_bytes() == b"PNG"
    assert "zażółć" in html.read_text(encoding="utf-8")
    assert re.fullmatch(r"\d{8}_\d{6}_\d{3}_CatalogPage_kliknij\.png", png.name)
    assert png.stem == html.stem


def test_nazwa_bazowa_ma_znacznik_czasu():
    nazwa = nazwa_bazowa("op", datetime(2026, 10, 11, 9, 8, 7, 123000))
    assert nazwa == "20261011_090807_123_op"


def test_blad_zrzutu_nie_rzuca_wyjatku_a_html_sie_zapisuje(tmp_path):
    class Zepsuty(AtrapaDrivera):
        def save_screenshot(self, sciezka):
            raise OSError("brak miejsca")

    png, html = zapisz_diagnostyke(Zepsuty(), "op", tmp_path)
    assert png is None
    assert html is not None and html.exists()


def test_blad_zrodla_nie_rzuca_wyjatku(tmp_path):
    class Zepsuty(AtrapaDrivera):
        @property
        def page_source(self):
            raise RuntimeError("sesja zamknięta")

    png, html = zapisz_diagnostyke(Zepsuty(), "op", tmp_path)
    assert png is not None
    assert html is None


def test_niedostepny_katalog_nie_rzuca_wyjatku(tmp_path):
    plik = tmp_path / "plik.txt"
    plik.write_text("x")
    assert zapisz_diagnostyke(AtrapaDrivera(), "op", plik / "podkatalog") == (None, None)
