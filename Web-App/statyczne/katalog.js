/**
 * Katalog Bajtomarketu — cała lista powstaje tutaj, w przeglądarce.
 *
 * W źródle HTML (Ctrl+U) nie ma ani jednego rekordu: dane pochodzą z plików
 * dane/strona-<n>-porcja-<k>.json, doładowywanych po 12 sztuk przyciskiem
 * „Wczytaj więcej”, z opóźnieniem 300–2000 ms przed pokazaniem każdej porcji.
 *
 * Rekordy trafiają do dwóch różnych struktur: pięć z każdej porcji do tabeli,
 * siedem do kart `article.produkt`.
 */
(function () {
  "use strict";

  var pomoc = Bajtomarket;
  var ZASTEPNIK_BRAKU = "—";
  var NA_TABELE = 5;        // tyle rekordów z każdej dwunastki idzie do tabeli
  var NA_PORCJE = 12;

  /** Opis atrybutu: skąd wziąć wartość i jaką klasą go oznaczyć. */
  var POLA = [
    { klasa: "cena", etykieta: "Cena", wartosc: function (p) { return p.cena_tekst; },
      atrybuty: function (p) { return { "data-waluta": p.waluta }; } },
    { klasa: "cena-poprzednia", etykieta: "Cena poprzednia", pomijalne: true,
      wartosc: function (p) { return p.cena_poprzednia_tekst; } },
    { klasa: "kategoria", etykieta: "Kategoria", wartosc: function (p) { return p.kategoria; } },
    { klasa: "producent", etykieta: "Producent", wartosc: function (p) { return p.producent; } },
    { klasa: "dostepnosc", etykieta: "Dostępność", wartosc: function (p) { return p.dostepnosc; } },
    { klasa: "ocena", etykieta: "Ocena", wartosc: function (p) { return p.ocena_tekst; } },
    { klasa: "liczba-opinii", etykieta: "Liczba opinii",
      wartosc: function (p) { return String(p.liczba_opinii); } },
    { klasa: "data-dodania", etykieta: "Data dodania", wartosc: function (p) { return p.data_tekst; } },
    { klasa: "gwarancja", etykieta: "Gwarancja", wartosc: function (p) { return p.gwarancja_tekst; } },
  ];

  var stan = {
    strona: 1,
    stronLacznie: 1,
    porcja: 0,          // ile porcji już wczytano
    porcjiLacznie: 0,
    razem: 0,
    wczytane: [],       // wszystkie rekordy pobrane dla tej podstrony
    kategoria: "",
    sort: "domyslne",
    wczytywanie: false,
  };

  var widoki = {};

  function element(identyfikator) { return document.getElementById(identyfikator); }

  // ─────────────────────────── uruchomienie ───────────────────────────

  document.addEventListener("DOMContentLoaded", async function () {
    widoki = {
      sekcjaTabeli: element("sekcja-tabeli"),
      miejsceTabeli: element("miejsce-tabeli"),
      sekcjaKart: element("sekcja-kart"),
      miejsceKart: element("miejsce-kart"),
      przycisk: element("wczytaj-wiecej"),
      licznik: element("licznik-porcji"),
      blad: element("komunikat-bledu"),
      podsumowanie: element("podsumowanie-strony"),
    };
    stan.strona = Number(pomoc.meta("podstrona")) || 1;
    stan.stronLacznie = Number(pomoc.meta("stron-lacznie")) || 1;

    widoki.przycisk.addEventListener("click", function () { doladuj(); });
    element("filtry").addEventListener("change", zmienFiltry);
    element("wyczysc-filtry").addEventListener("click", function () {
      element("filtr-kategoria").value = "";
      element("filtr-sort").value = "domyslne";
      zmienFiltry();
    });

    try {
      var katalog = await pomoc.pobierzJson("/dane/katalog.json");
      przygotujFiltry(katalog);
      zbudujPaginacje(katalog);
      element("data-stanu").textContent = katalog.data_stanu;
      element("data-stanu").setAttribute("datetime", katalog.data_stanu);
    } catch (blad) {
      pokazBlad("Nie udało się wczytać opisu katalogu: " + blad.message);
      return;
    }
    await doladuj();
  });

  function przygotujFiltry(katalog) {
    var wybor = element("filtr-kategoria");
    katalog.kategorie.forEach(function (nazwa) {
      wybor.append(pomoc.utworz("option", { atrybuty: { value: nazwa }, tekst: nazwa }));
    });
  }

  function zbudujPaginacje(katalog) {
    var nawigacja = element("paginacja");
    nawigacja.replaceChildren();
    katalog.strony.forEach(function (strona) {
      nawigacja.append(strona.numer === stan.strona
        ? pomoc.utworz("span", { klasa: "strona strona-biezaca", tekst: String(strona.numer),
                                 atrybuty: { "aria-current": "page" } })
        : pomoc.utworz("a", { klasa: "strona", tekst: String(strona.numer),
                              atrybuty: { href: "/" + strona.adres } }));
    });
  }

  // ─────────────────────────── doładowywanie porcjami ───────────────────────────

  async function doladuj() {
    if (stan.wczytywanie) return;
    if (stan.porcjiLacznie && stan.porcja >= stan.porcjiLacznie) return;
    stan.wczytywanie = true;
    document.body.dataset.wczytywanie = "tak";
    widoki.przycisk.disabled = true;
    widoki.licznik.textContent = "Wczytywanie porcji ofert…";

    var adres = "/dane/strona-" + stan.strona + "-porcja-" + (stan.porcja + 1) + ".json";
    try {
      var porcja = await pomoc.pobierzJson(adres);
      await pomoc.opoznijPorcje();          // sztuczne opóźnienie 300–2000 ms
      stan.porcja = porcja.porcja;
      stan.porcjiLacznie = porcja.porcji_lacznie;
      stan.razem = porcja.razem;
      stan.wczytane = stan.wczytane.concat(porcja.produkty);
      widoki.blad.hidden = true;
      rysuj();
    } catch (blad) {
      pokazBlad("Nie udało się doładować ofert: " + blad.message);
    } finally {
      stan.wczytywanie = false;
      delete document.body.dataset.wczytywanie;
      widoki.przycisk.disabled = false;
      widoki.przycisk.hidden = stan.porcja >= stan.porcjiLacznie;
    }
  }

  // ─────────────────────────── filtrowanie i sortowanie bez przeładowania ───────────────────────────

  function zmienFiltry() {
    stan.kategoria = element("filtr-kategoria").value;
    stan.sort = element("filtr-sort").value;
    element("stan-filtrow").textContent = (stan.kategoria || stan.sort !== "domyslne")
      ? "filtr: " + (stan.kategoria || "wszystkie kategorie") + ", sortowanie: " + stan.sort
      : "";
    rysuj();                                 // bez przeładowania strony i bez nowego żądania
  }

  function doPokazania() {
    var widoczne = stan.wczytane.filter(function (rekord) {
      return !stan.kategoria || rekord.kategoria === stan.kategoria;
    });
    var porzadki = {
      "cena-rosnaco": function (a, b) { return pomoc.cenaDoLiczby(a) - pomoc.cenaDoLiczby(b); },
      "cena-malejaco": function (a, b) { return pomoc.cenaDoLiczby(b) - pomoc.cenaDoLiczby(a); },
      "ocena-malejaco": function (a, b) {
        return (Number(String(b.ocena_tekst).replace(",", ".")) || -1)
             - (Number(String(a.ocena_tekst).replace(",", ".")) || -1);
      },
      "nazwa-rosnaco": function (a, b) { return a.nazwa.localeCompare(b.nazwa, "pl"); },
    };
    return porzadki[stan.sort] ? widoczne.slice().sort(porzadki[stan.sort]) : widoczne;
  }

  // ─────────────────────────── rysowanie listy ───────────────────────────

  function rysuj() {
    var widoczne = doPokazania();
    var doTabeli = widoczne.filter(function (_, indeks) { return indeks % NA_PORCJE < NA_TABELE; });
    var doKart = widoczne.filter(function (_, indeks) { return indeks % NA_PORCJE >= NA_TABELE; });

    widoki.miejsceTabeli.replaceChildren(tabela(doTabeli));
    widoki.miejsceKart.replaceChildren.apply(widoki.miejsceKart, doKart.map(karta));
    widoki.sekcjaTabeli.hidden = doTabeli.length === 0;
    widoki.sekcjaKart.hidden = doKart.length === 0;

    widoki.licznik.textContent = stan.porcja >= stan.porcjiLacznie
      ? "Pokazano wszystkie " + widoczne.length + " ofert z tej podstrony."
      : "Pokazano " + widoczne.length + " z " + stan.razem + " ofert.";
    widoki.podsumowanie.textContent = "Podstrona " + stan.strona + " z " + stan.stronLacznie
      + " · " + stan.razem + " ofert · porcja " + stan.porcja + " z " + stan.porcjiLacznie;

    document.body.dataset.wczytano = String(stan.wczytane.length);
    document.body.dataset.widocznych = String(widoczne.length);
    document.body.dataset.porcja = String(stan.porcja);
    document.body.dataset.porcjiLacznie = String(stan.porcjiLacznie);
  }

  function tabela(rekordy) {
    var tabelaOfert = pomoc.utworz("table", { klasa: "tabela-ofert" });
    var naglowek = pomoc.utworz("thead");
    var wierszNaglowka = pomoc.utworz("tr");
    wierszNaglowka.append(pomoc.utworz("th", { klasa: "naglowek-nazwa", tekst: "Nazwa",
                                               atrybuty: { scope: "col" } }));
    POLA.forEach(function (pole) {
      wierszNaglowka.append(pomoc.utworz("th", { klasa: "naglowek-" + pole.klasa, tekst: pole.etykieta,
                                                 atrybuty: { scope: "col" } }));
    });
    naglowek.append(wierszNaglowka);
    tabelaOfert.append(naglowek);

    var tresc = pomoc.utworz("tbody");
    rekordy.forEach(function (rekord) { tresc.append(wiersz(rekord)); });
    tabelaOfert.append(tresc);
    return tabelaOfert;
  }

  function wiersz(rekord) {
    var wierszProduktu = pomoc.utworz("tr", { klasa: "wiersz-produktu",
                                              atrybuty: { "data-id": rekord.id } });
    var komorkaNazwy = pomoc.utworz("td", { klasa: "nazwa-produktu" });
    komorkaNazwy.append(odnosnik(rekord));
    wierszProduktu.append(komorkaNazwy);

    POLA.forEach(function (pole) {
      var wartosc = pole.wartosc(rekord);
      var pusta = wartosc === null || wartosc === undefined;
      // kolumny tabeli muszą się zgadzać, więc brak zostaje jako pusta komórka
      // (brak promocji) albo myślnik z klasą `brak-wartosci` (faktyczny brak danych)
      wierszProduktu.append(pomoc.utworz("td", {
        klasa: pusta && !pole.pomijalne ? pole.klasa + " brak-wartosci" : pole.klasa,
        atrybuty: pole.atrybuty ? pole.atrybuty(rekord) : {},
        tekst: pusta ? (pole.pomijalne ? "" : ZASTEPNIK_BRAKU) : wartosc,
      }));
    });
    return wierszProduktu;
  }

  function karta(rekord) {
    var kartaProduktu = pomoc.utworz("article", { klasa: "produkt",
                                                  atrybuty: { "data-id": rekord.id } });
    var tytul = pomoc.utworz("h3", { klasa: "nazwa-produktu" });
    tytul.append(odnosnik(rekord));
    kartaProduktu.append(tytul);

    var atrybuty = pomoc.utworz("div", { klasa: "atrybuty" });
    POLA.forEach(function (pole) {
      var wartosc = pole.wartosc(rekord);
      var pusta = wartosc === null || wartosc === undefined;
      if (pusta && pole.pomijalne) return;      // brak promocji to nie brak danych
      var akapit = pomoc.utworz("p", {
        klasa: pusta ? pole.klasa + " brak-wartosci" : pole.klasa,
        atrybuty: pole.atrybuty ? pole.atrybuty(rekord) : {},
      });
      akapit.append(pomoc.utworz("span", { klasa: "etykieta", tekst: pole.etykieta + ":" }));
      akapit.append(document.createTextNode(" " + (pusta ? ZASTEPNIK_BRAKU : wartosc)));
      atrybuty.append(akapit);
    });
    kartaProduktu.append(atrybuty);
    return kartaProduktu;
  }

  function odnosnik(rekord) {
    return pomoc.utworz("a", {
      klasa: "odnosnik-produktu",
      atrybuty: { href: "/" + rekord.url, "data-id": rekord.id },
      tekst: rekord.nazwa,
    });
  }

  function pokazBlad(komunikat) {
    widoki.blad.textContent = komunikat;
    widoki.blad.hidden = false;
    widoki.licznik.textContent = "";
  }
})();
