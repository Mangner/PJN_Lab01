"""Testy parsera argumentów i ścieżek CLI bez uruchamiania Chrome'a."""

from pathlib import Path

import pytest

from bajtoparser import cli
from bajtoparser.porownanie import StronaHtml, WynikPorownania
from bajtoparser.utils.logowanie import (
    PodsumowaniePrzebiegu,
    skonfiguruj_logowanie,
    wylacz_logowanie,
)


@pytest.fixture(autouse=True)
def logi_w_tmp(tmp_path, monkeypatch):
    """Logi CLI trafiają do katalogu tymczasowego, uchwyty są zamykane po teście."""
    monkeypatch.setattr(cli, "skonfiguruj_logowanie", lambda: skonfiguruj_logowanie(tmp_path))
    yield
    wylacz_logowanie()


def test_wartosci_domyslne():
    a = cli.zbuduj_parser().parse_args([])
    assert a.adres == "http://localhost:8000/"
    assert a.strony is None and a.limit is None and a.headless is False
    assert a.wyjscie == "produkty" and a.katalog_wyjscia == Path("output")
    assert a.pauza == 0.5 and a.timeout == 10.0


def test_wszystkie_parametry():
    pary = {
        "--adres": "http://x:1/",
        "--strony": "2",
        "--limit": "5",
        "--wyjscie": "t",
        "--katalog-wyjscia": "wyn",
        "--pauza": "1,5",
        "--timeout": "20",
    }
    argumenty = [x for para in pary.items() for x in para] + ["--headless"]
    a = cli.zbuduj_parser().parse_args(argumenty)
    k = cli.zbuduj_konfiguracje(a)
    assert (k.adres_serwisu, k.strony, k.limit, k.headless) == ("http://x:1/", 2, 5, True)
    assert (k.nazwa_wyjscia, k.katalog_wyjscia) == ("t", Path("wyn"))
    assert (k.pauza_s, k.timeout_s) == (1.5, 20.0)


def test_pauza_ponizej_minimum_jest_podnoszona():
    k = cli.zbuduj_konfiguracje(cli.zbuduj_parser().parse_args(["--pauza", "0.1"]))
    assert k.pauza_s == 0.5


@pytest.mark.parametrize(
    "argumenty",
    [["--strony", "0"], ["--limit", "-3"], ["--strony", "dwie"], ["--timeout", "0"]],
)
def test_niepoprawne_wartosci_sa_odrzucane(argumenty):
    with pytest.raises(SystemExit) as wyjatek:
        cli.zbuduj_parser().parse_args(argumenty)
    assert wyjatek.value.code == 2


def test_serwis_niedostepny_kod_2_bez_chrome(monkeypatch, caplog):
    monkeypatch.setattr(cli, "serwis_odpowiada", lambda adres: False)

    def zakazany_driver(*args, **kwargs):
        raise AssertionError("Chrome nie powinien się uruchomić")

    monkeypatch.setattr(cli, "otworz_driver", zakazany_driver)
    assert cli.main(["--adres", "http://localhost:1/"]) == cli.KOD_BLAD_KRYTYCZNY
    assert any("Serwis nie odpowiada" in r.message for r in caplog.records)


def test_serwis_odpowiada_false_dla_zamknietego_portu():
    assert cli.serwis_odpowiada("http://127.0.0.1:1/", timeout_s=0.5) is False


class _AtrapaDrivera:
    def __enter__(self):
        return object()

    def __exit__(self, *args):
        return False


def _przygotuj_przebieg(monkeypatch, bledy=0):
    """Podmienia serwis, driver, strony i pipeline; zwraca listę kolejności zdarzeń."""
    zdarzenia: list[str] = []
    podsumowanie = PodsumowaniePrzebiegu(tryb="headless")
    podsumowanie.strony = 1
    podsumowanie.rekordy = 3
    podsumowanie.bledy = bledy
    podsumowanie.probka_produktow = [{"id": "A", "nazwa": "Produkt A", "url": "/produkt/A.html"}]

    class AtrapaPipeline:
        def __init__(self, *args):
            pass

        def uruchom(self):
            zdarzenia.append("przebieg")
            return podsumowanie

    monkeypatch.setattr(cli, "serwis_odpowiada", lambda adres: True)
    monkeypatch.setattr(cli, "otworz_driver", lambda *a, **k: _AtrapaDrivera())
    monkeypatch.setattr(cli, "CatalogPage", lambda *a, **k: None)
    monkeypatch.setattr(cli, "ProductPage", lambda *a, **k: None)
    monkeypatch.setattr(cli, "Pipeline", AtrapaPipeline)
    return zdarzenia


def test_porownanie_po_przebiegu_nie_zmienia_kodu_wyjscia(monkeypatch, tmp_path):
    zdarzenia = _przygotuj_przebieg(monkeypatch)

    def atrapa_porownaj(adres, liczba_podstron, probka, **kwargs):
        zdarzenia.append("porownanie")
        assert (liczba_podstron, [p["id"] for p in probka]) == (1, ["A"])
        return WynikPorownania(podstrony=[StronaHtml(url="u", pobrano=False)])  # błąd sieci

    monkeypatch.setattr(cli, "porownaj", atrapa_porownaj)
    kod = cli.main(
        ["--porownanie", "--katalog-wyjscia", str(tmp_path), "--wyjscie", "t", "--strony", "1"]
    )

    assert kod == cli.KOD_SUKCES
    assert zdarzenia == ["przebieg", "porownanie"]
    assert (tmp_path / "t_porownanie.json").exists()


def test_bez_flagi_porownanie_nie_jest_uruchamiane(monkeypatch):
    _przygotuj_przebieg(monkeypatch)

    def zakazane(*args, **kwargs):
        raise AssertionError("porównanie nie powinno się uruchomić")

    monkeypatch.setattr(cli, "porownaj", zakazane)
    assert cli.main([]) == cli.KOD_SUKCES


def test_blad_krytyczny_daje_kod_2(monkeypatch):
    monkeypatch.setattr(cli, "serwis_odpowiada", lambda adres: True)

    def awaria(*args, **kwargs):
        raise RuntimeError("Chrome się nie uruchomił")

    monkeypatch.setattr(cli, "otworz_driver", awaria)
    assert cli.main([]) == cli.KOD_BLAD_KRYTYCZNY
