/**
 * Funkcje wspólne dla katalogu i karty produktu (Bajtomarket, Lab 1 PJN).
 *
 * Celowo zwykły skrypt, a nie moduł ES: `python -m http.server` bierze typ MIME
 * z rejestru systemu i na części maszyn z Windowsem podaje dla plików .js
 * `text/plain`, co blokuje moduły. Zwykłe skrypty działają wszędzie.
 */
var Bajtomarket = (function () {
  "use strict";

  /** Sztuczne opóźnienie doładowania porcji — wymagane 300–2000 ms (poziom 5.0). */
  var OPOZNIENIE_PORCJI = [300, 2000];

  function pauza(milisekundy) {
    return new Promise(function (gotowe) { setTimeout(gotowe, milisekundy); });
  }

  /** Losowe opóźnienie z zakresu OPOZNIENIE_PORCJI — udaje wolną sieć. */
  function opoznijPorcje() {
    var zakres = OPOZNIENIE_PORCJI;
    return pauza(zakres[0] + Math.random() * (zakres[1] - zakres[0]));
  }

  /** Pobranie pliku JSON z ponawianiem i opóźnieniem wykładniczym (1 s, 2 s, 4 s…). */
  async function pobierzJson(adres, proby) {
    var limit = proby || 3;
    var ostatniBlad = null;
    for (var proba = 1; proba <= limit; proba += 1) {
      try {
        var odpowiedz = await fetch(adres, { headers: { Accept: "application/json" } });
        if (odpowiedz.ok) return await odpowiedz.json();
        ostatniBlad = new Error("serwer odpowiedział kodem " + odpowiedz.status);
      } catch (wyjatek) {
        ostatniBlad = wyjatek;
      }
      if (proba < limit) await pauza(Math.pow(2, proba - 1) * 500);
    }
    throw ostatniBlad || new Error("nie udało się pobrać " + adres);
  }

  /** Skrócony zapis document.createElement z klasą, atrybutami i treścią. */
  function utworz(znacznik, opcje) {
    var ustawienia = opcje || {};
    var element = document.createElement(znacznik);
    if (ustawienia.klasa) element.className = ustawienia.klasa;
    var atrybuty = ustawienia.atrybuty || {};
    Object.keys(atrybuty).forEach(function (nazwa) {
      if (atrybuty[nazwa] !== null && atrybuty[nazwa] !== undefined) {
        element.setAttribute(nazwa, String(atrybuty[nazwa]));
      }
    });
    if (ustawienia.tekst !== undefined && ustawienia.tekst !== null) element.textContent = ustawienia.tekst;
    if (ustawienia.html !== undefined && ustawienia.html !== null) element.innerHTML = ustawienia.html;
    return element;
  }

  function meta(nazwa) {
    var znacznik = document.querySelector('meta[name="' + nazwa + '"]');
    return znacznik ? znacznik.getAttribute("content") : null;
  }

  /** Cena z powrotem na liczbę — wyłącznie na użytek sortowania w przeglądarce. */
  function cenaDoLiczby(rekord) {
    var kursy = { PLN: 1, EUR: 4.28, USD: 3.92 };
    var tekst = String(rekord.cena_tekst || "").replace(/[^\d.,]/g, "");
    var liczba = rekord.waluta === "USD"
      ? Number(tekst.replace(/,/g, ""))
      : Number(tekst.replace(/ /g, "").replace(",", "."));
    return isNaN(liczba) ? 0 : liczba * (kursy[rekord.waluta] || 1);
  }

  return {
    OPOZNIENIE_PORCJI: OPOZNIENIE_PORCJI,
    pauza: pauza,
    opoznijPorcje: opoznijPorcje,
    pobierzJson: pobierzJson,
    utworz: utworz,
    meta: meta,
    cenaDoLiczby: cenaDoLiczby,
  };
})();
