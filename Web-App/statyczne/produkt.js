/**
 * Karta pojedynczego produktu — również budowana wyłącznie w przeglądarce.
 *
 * Utrudnienie poziomu 5.0: zakładki „Specyfikacja” oraz „Dostawa i zwroty” wypełniają się
 * dopiero przy pierwszym kliknięciu. Dwanaście atrybutów (EAN, stan magazynowy, sprzedawca,
 * kod producenta, kolor, materiał, waga, wymiary, kraj pochodzenia, czas i koszt dostawy,
 * termin zwrotu) nie istnieje w drzewie DOM, dopóki parser nie wykona interakcji.
 */
(function () {
  "use strict";

  var pomoc = Bajtomarket;

  var PODSUMOWANIE = [
    ["cena", "Cena", function (p) { return p.cena_tekst; }, function (p) { return { "data-waluta": p.waluta }; }],
    ["cena-poprzednia", "Cena poprzednia", function (p) { return p.cena_poprzednia_tekst; }, null],
    ["kategoria", "Kategoria", function (p) { return p.kategoria; }, null],
    ["producent", "Producent", function (p) { return p.producent; }, null],
    ["dostepnosc", "Dostępność", function (p) { return p.dostepnosc; }, null],
    ["ocena", "Ocena", function (p) { return p.ocena_tekst; }, null],
    ["liczba-opinii", "Liczba opinii", function (p) { return String(p.liczba_opinii); }, null],
    ["data-dodania", "Data dodania", function (p) { return p.data_tekst; }, null],
    ["gwarancja", "Gwarancja", function (p) { return p.gwarancja_tekst; }, null],
  ];

  var SPECYFIKACJA = [
    ["ean", "Kod EAN", function (p) { return p.ean; }],
    ["kod-producenta", "Kod producenta", function (p) { return p.kod_producenta; }],
    ["kolor", "Kolor", function (p) { return p.kolor; }],
    ["material", "Materiał", function (p) { return p.material; }],
    ["waga", "Waga", function (p) { return p.waga_tekst; }],
    ["wymiary", "Wymiary", function (p) { return p.wymiary_tekst; }],
    ["kraj-pochodzenia", "Kraj pochodzenia", function (p) { return p.kraj_pochodzenia; }],
  ];

  var DOSTAWA = [
    ["sprzedawca", "Sprzedawca", function (p) { return p.sprzedawca; }],
    ["stan-magazynowy", "Stan magazynowy", function (p) { return p.stan_magazynowy + " szt."; }],
    ["czas-dostawy", "Czas dostawy", function (p) { return p.czas_dostawy_tekst; }],
    ["koszt-dostawy", "Koszt dostawy", function (p) { return p.koszt_dostawy_tekst; }],
    ["zwrot", "Zwrot", function (p) { return p.zwrot_tekst; }],
  ];

  var wypelnione = {};

  function element(identyfikator) { return document.getElementById(identyfikator); }

  document.addEventListener("DOMContentLoaded", async function () {
    var identyfikator = pomoc.meta("produkt");
    if (!identyfikator) return pokazBlad("Strona nie wskazuje żadnego produktu.");

    var produkt;
    try {
      produkt = await pomoc.pobierzJson("/dane/produkt/" + identyfikator + ".json");
    } catch (blad) {
      return pokazBlad("Nie udało się wczytać produktu: " + blad.message);
    }

    zbudujKarte(produkt);
    podepnijZakladki(produkt);
    element("komunikat-wczytywania").hidden = true;
    element("karta-produktu").hidden = false;
    document.body.dataset.stanRenderu = "gotowy";
    document.body.dataset.id = produkt.id;
    return undefined;
  });

  function zbudujKarte(produkt) {
    document.title = produkt.nazwa + " – Bajtomarket";

    var okruszki = element("okruszki");
    okruszki.append(document.createTextNode(" / "));
    okruszki.append(pomoc.utworz("span", { klasa: "okruszek-kategoria", tekst: produkt.kategoria }));

    element("nazwa-produktu").textContent = produkt.nazwa;
    element("karta-produktu").setAttribute("data-id", produkt.id);
    element("identyfikator").textContent = "Symbol oferty: " + produkt.id;
    element("podsumowanie").append(listaDefinicji(produkt, PODSUMOWANIE, "dane-podstawowe"));
    element("panel-opis").append(pomoc.utworz("p", { klasa: "opis", tekst: produkt.opis }));
  }

  function podepnijZakladki(produkt) {
    var zakladki = Array.prototype.slice.call(document.querySelectorAll(".zakladka"));
    zakladki.forEach(function (zakladka) {
      zakladka.addEventListener("click", function () {
        zakladki.forEach(function (inna) {
          var aktywna = inna === zakladka;
          inna.setAttribute("aria-selected", String(aktywna));
          element("panel-" + inna.dataset.panel).hidden = !aktywna;
        });
        wypelnijPanel(produkt, zakladka.dataset.panel);
      });
    });
  }

  /** Treść zakładki powstaje dopiero przy pierwszym jej otwarciu. */
  function wypelnijPanel(produkt, nazwa) {
    if (nazwa === "opis" || wypelnione[nazwa]) return;
    wypelnione[nazwa] = true;
    var panel = element("panel-" + nazwa);
    panel.append(listaDefinicji(produkt, nazwa === "specyfikacja" ? SPECYFIKACJA : DOSTAWA,
                                "dane-" + nazwa));
    panel.dataset.wypelnione = "tak";
  }

  function listaDefinicji(produkt, pola, klasa) {
    var lista = pomoc.utworz("dl", { klasa: klasa });
    pola.forEach(function (pole) {
      var nazwa = pole[0];
      var etykieta = pole[1];
      var wartosc = pole[2](produkt);
      var dodatkowe = pole[3];
      var pusta = wartosc === null || wartosc === undefined;
      if (pusta && nazwa === "cena-poprzednia") return;   // brak promocji to nie brak danych
      lista.append(pomoc.utworz("dt", { klasa: "etykieta-" + nazwa, tekst: etykieta }));
      lista.append(pomoc.utworz("dd", {
        klasa: pusta ? nazwa + " brak-wartosci" : nazwa,
        atrybuty: dodatkowe ? dodatkowe(produkt) : {},
        tekst: pusta ? "—" : wartosc,
      }));
    });
    return lista;
  }

  function pokazBlad(komunikat) {
    element("komunikat-wczytywania").hidden = true;
    var blad = element("komunikat-bledu");
    blad.textContent = komunikat;
    blad.hidden = false;
  }
})();
