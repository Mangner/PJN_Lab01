---
name: koniec-fazy
description: Zamyka bieżącą fazę pracy: weryfikacja, aktualizacja planu i notatek, commit.
disable-model-invocation: true
---

Zamknij bieżącą fazę z docs/PLAN.md. Wykonaj po kolei:

1. Uruchom `pytest` i `ruff check .`. Jeśli coś nie przechodzi, NIE rób commita:
   pokaż błędy i zatrzymaj się.
2. Odhacz fazę w docs/PLAN.md.
3. Dopisz do docs/NOTATKI-DO-SPRAWOZDANIA.md (utwórz plik, jeśli go nie ma):
   nagłówek z numerem fazy, 2-3 zdania o podjętych decyzjach i konkretne liczby
   (czasy, liczby rekordów, liczba retry), jeśli faza je wytworzyła.
4. Pokaż `git status --short`.
5. Zrób `git add -A .` i commit w formie `faza N: krótki opis po polsku`.
6. Powiedz, jaka jest następna faza z PLAN.md. Nie zaczynaj jej.