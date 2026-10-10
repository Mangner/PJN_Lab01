# Wymagania: Laboratorium 1, rola PARSER, ocena 5.0

Źródło: PDF laboratorium. Poziom 5.0 zawiera wszystko z 3.0 i 4.0.

## Obowiązkowe

### Z poziomu 3.0
- [ ] Jeden wiersz = jeden rekord, jedna kolumna = jeden atrybut
- [ ] Rekordy z obu struktur (tabela i karty) sprowadzone do wspólnego formatu
- [ ] Cena jako liczba, nie tekst z symbolem waluty
- [ ] UTF-8, poprawne polskie znaki

### Z poziomu 4.0
- [ ] Minimum 200 rekordów i 18 atrybutów (serwis: ~420 rekordów, 26 atrybutów)
- [ ] Przejście przez wszystkie podstrony i wejście w podstrony szczegółów, połączenie danych z listy i ze szczegółów
- [ ] Czyszczenie: ceny na liczby, ujednolicone formaty, usunięte duplikaty
- [ ] Brak danych jako pusta wartość, nie wyjątek przerywający działanie
- [ ] Opóźnienie min. 0,5 s między żądaniami

### Z poziomu 5.0
- [ ] Selenium (Chrome)
- [ ] Jawne oczekiwanie: WebDriverWait z warunkiem, nie sleep na sztywno
- [ ] Obsługa doładowywania aż do wyczerpania rekordów
- [ ] Retry z opóźnieniem wykładniczym (1 s, 2 s, 4 s...) i górnym limitem prób
- [ ] Porównanie liczby rekordów w surowym HTML (pobranym BEZ przeglądarki) i w DOM po
      wykonaniu skryptów: konkretne liczby i wniosek (trafia do sprawozdania)

## Wybrane rozszerzenia (wymagane min. 2 na poziom)

### Z listy 4.0
- [ ] Parametryzacja z CLI (adres serwisu, liczba stron, pliki wyjściowe, headless)
- [ ] Eksport jednocześnie do CSV (UTF-8) i JSON
- [ ] Logowanie do pliku z podsumowaniem: liczba stron, rekordów, błędów, czas działania
- [ ] Minimum 3 testy jednostkowe funkcji czyszczących (pytest)

### Z listy 5.0
- [ ] Tryb headless z pomiarem czasu działania w obu trybach (okno vs headless)
- [ ] Automatyczny zrzut ekranu (.png) i zapis źródła (.html) przy błędzie, do `diagnostyka/`

### Opcjonalne, decyzja później
- [ ] Wykrycie i użycie źródła danych strony (pliki JSON w `dane/`) wraz z omówieniem,
      dlaczego jest szybsze. Tanie, bo moduł porównania HTML z DOM i tak pobiera dane bez przeglądarki.

## Poza zakresem (NIE robić)
- Obsługa 429 i Retry-After: serwis nie ma takiego mechanizmu
- Checkpointy i wznawianie sesji, pobieranie równoległe, eksport XLSX
- Porównanie zużycia pamięci
- Zmiany w `../Web-App/`

## Analiza danych (osobny etap, po działającym parserze)
Kontrola jakości danych (wykonać jako pierwszą):
- [ ] Liczba rekordów i braki w każdej kolumnie (sztuki i procenty)
- [ ] Duplikaty przed i po odrzuceniu
- [ ] Typy kolumn: czy liczbowe są liczbowe
- [ ] Wartości odstające z interpretacją: anomalia w danych czy błąd parsera
- [ ] Wniosek: co analiza mówi o parserze i co poprawiono

Statystyki i wykresy:
- [ ] Średnia, mediana, moda, kwartyle, min, max dla cech liczbowych
- [ ] Histogram (min. 1 cecha), box-plot (min. 1 cecha)
- [ ] Korelacja min. 2 cech z komentarzem merytorycznym

## Sprawozdanie (PDF)
- [ ] Użyta technologia i uzasadnienie
- [ ] Opis parsera: wybrane rozszerzenia, selektory i uzasadnienie wyboru
- [ ] Ocena odporności selektorów: które przetrwają zmianę wyglądu serwisu, a które nie
- [ ] Wyniki kontroli jakości danych
- [ ] Statystyki i wnioski
- [ ] Porównanie surowego HTML z DOM (liczby, wniosek)
- [ ] (opis serwisu dotyczy roli AUTOR, nie nas)

## Oddanie
- [ ] Archiwum `LAB1_Nazwisko_Imie_Nazwisko_Imie.zip` na platformie Delta (jedno na parę)
- [ ] Odpowiedź ustna na laboratoriach