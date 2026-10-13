# Wymagania: Laboratorium 1, rola PARSER, ocena 5.0

Źródło: PDF laboratorium (`docs/LAB1.pdf`). Poziom 5.0 zawiera wszystko z 3.0 i 4.0.

Uwaga o progach: dla roli PARSER obowiązuje **min. 200 rekordów i 18 atrybutów** (4.0).
Progi **min. 400 rekordów i 22 atrybuty** (5.0) dotyczą roli AUTOR, nie nas (rozstrzygnięcie
z fazy 9, potwierdzone w PDF-ie). Serwis ma 420 rekordów i 26 atrybutów, więc spełnia oba.

## Obowiązkowe

### Z poziomu 3.0
- [x] Jeden wiersz = jeden rekord, jedna kolumna = jeden atrybut
- [x] Rekordy z obu struktur (tabela i karty) sprowadzone do wspólnego formatu
- [x] Cena jako liczba, nie tekst z symbolem waluty
- [x] UTF-8, poprawne polskie znaki

### Z poziomu 4.0
- [x] Minimum 200 rekordów i 18 atrybutów (serwis: ~420 rekordów, 26 atrybutów)
- [x] Przejście przez wszystkie podstrony i wejście w podstrony szczegółów, połączenie danych z listy i ze szczegółów
- [x] Czyszczenie: ceny na liczby, ujednolicone formaty, usunięte duplikaty
- [x] Brak danych jako pusta wartość, nie wyjątek przerywający działanie
- [x] Opóźnienie min. 0,5 s między żądaniami

### Z poziomu 5.0
- [x] Selenium (Chrome)
- [x] Jawne oczekiwanie: WebDriverWait z warunkiem, nie sleep na sztywno
- [x] Obsługa doładowywania aż do wyczerpania rekordów
- [x] Retry z opóźnieniem wykładniczym (1 s, 2 s, 4 s...) i górnym limitem prób
- [x] Porównanie liczby rekordów w surowym HTML (pobranym BEZ przeglądarki) i w DOM po
      wykonaniu skryptów: konkretne liczby i wniosek (trafia do sprawozdania)

## Wybrane rozszerzenia (wymagane min. 2 na poziom)

### Z listy 4.0
- [x] Parametryzacja z CLI (adres serwisu, liczba stron, pliki wyjściowe, headless)
- [x] Eksport jednocześnie do CSV (UTF-8) i JSON
- [x] Logowanie do pliku z podsumowaniem: liczba stron, rekordów, błędów, czas działania
- [x] Minimum 3 testy jednostkowe funkcji czyszczących (pytest)

### Z listy 5.0
- [x] Tryb headless z pomiarem czasu działania w obu trybach (okno vs headless)
- [x] Automatyczny zrzut ekranu (.png) i zapis źródła (.html) przy błędzie, do `diagnostyka/`

### Opcjonalne (decyzja z fazy 9: pomijamy)
- [ ] Wykrycie i użycie źródła danych strony (pliki JSON w `dane/`) wraz z omówieniem,
      dlaczego jest szybsze. Tanie, bo moduł porównania HTML z DOM i tak pobiera dane bez przeglądarki.

## Poza zakresem (NIE robić)
- Obsługa 429 i Retry-After: serwis nie ma takiego mechanizmu
- Checkpointy i wznawianie sesji, pobieranie równoległe, eksport XLSX
- Porównanie zużycia pamięci
- Zmiany w `../Web-App/`

## Analiza danych (osobny etap, po działającym parserze)
Kontrola jakości danych (wykonać jako pierwszą):
- [x] Liczba rekordów i braki w każdej kolumnie (sztuki i procenty)
- [x] Duplikaty przed i po odrzuceniu
- [x] Typy kolumn: czy liczbowe są liczbowe
- [x] Wartości odstające z interpretacją: anomalia w danych czy błąd parsera
- [x] Wniosek: co analiza mówi o parserze i co poprawiono

Statystyki i wykresy:
- [x] Średnia, mediana, moda, kwartyle, min, max dla cech liczbowych
- [x] Histogram (min. 1 cecha), box-plot (min. 1 cecha)
- [x] Korelacja min. 2 cech z komentarzem merytorycznym

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