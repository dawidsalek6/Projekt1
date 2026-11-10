# Sprawozdanie z Zadania Laboratoryjnego nr 3

**Przedmiot:** Programowanie w języku Python (`IwIK-S1`)  
**Projekt:** FitTrack Pro  
**Zespół:** Dawid Mucha i Dawid Sałek  
**Dawid Mucha:** nr albumu 164852, login Git `dawidmuchapk`  
**Dawid Sałek:** nr albumu do uzupełnienia, login Git `dawidsalek6`  
**Data oddania:** 27.10.2026

---

## 1. Cel i zakres zadania

Celem projektu jest konsolowa aplikacja FitTrack Pro do zapisywania treningów siłowych, spożycia makroskładników i czasu przerw między ćwiczeniami. Program udostępnia menu, waliduje dane wprowadzane przez użytkownika, zapisuje je na dysku i generuje podsumowania dzienne oraz tygodniowe.

W ramach Zadania 3 model został rozbudowany o encję `Exercise` i agregat `WorkoutSession`. Ćwiczenie przechowuje identyfikator, nazwę, liczbę serii i powtórzeń oraz ciężar. Sesja zarządza ćwiczeniami, oblicza łączny tonaż, sortuje się chronologicznie i obsługuje zagnieżdżoną serializację. Dodano również specjalizację `AssistedBodyweightExercise`, repozytorium sesji w JSON oraz testy modelu i zapisu.

---

## 2. Architektura rozwiązania

| Moduł lub plik | Odpowiedzialność |
| --- | --- |
| `main.py` | Pętla programu, menu i przekazywanie wyboru do funkcji usługowych. |
| `services.py` | Rejestracja treningów i posiłków, stoper oraz podsumowania dnia i tygodnia. Nowe ćwiczenie jest zapisywane w CSV i dodawane do sesji JSON. |
| `models.py` | Klasy `Exercise`, `AssistedBodyweightExercise` i `WorkoutSession`; walidacja, obliczanie objętości, porównywanie, agregacja oraz `to_dict()` / `from_dict()`. |
| `storage.py` | Odczyt i zapis CSV oraz profilu JSON. `WorkoutSessionRepository` zarządza zagnieżdżoną bazą sesji JSON. |
| `validators.py` | Walidacja liczb całkowitych, zmiennoprzecinkowych i niepustych napisów wprowadzanych w konsoli. |
| `data.py` | Dane przykładowe i stan stopera działającego w bieżącej sesji programu. |
| `test_models.py` | Siedem scenariuszy sprawdzających model domenowy, serializację, repozytorium i polimorfizm. |
| `data/workouts.csv` | Treningi zapisywane w formacie CSV. |
| `data/nutrition.csv` | Posiłki i makroskładniki zapisywane w formacie CSV. |
| `data/user_profile.json` | Profil użytkownika i dzienne cele żywieniowe. |
| `data/workout_sessions.json` | Zagnieżdżone sesje treningowe; plik jest tworzony przy pierwszym zapisie sesji. |

### Model domenowy

`Exercise` pilnuje, aby liczba serii i powtórzeń była dodatnia, a ciężar nie był ujemny. Metoda `volume()` zwraca iloczyn serii, powtórzeń i ciężaru. Identyfikatory ćwiczenia i sesji są tylko do odczytu. `WorkoutSession` przyjmuje wyłącznie obiekty `Exercise`, sumuje ich objętość i sortuje sesje według daty.

`AssistedBodyweightExercise` dziedziczy po `Exercise` i nadpisuje `volume()`: do obliczeń wykorzystuje masę ciała pomniejszoną o wspomaganie. Agregat zapisuje typ ćwiczenia, dzięki czemu `from_dict()` odtwarza właściwą klasę po odczycie JSON.

`WorkoutSessionRepository` oddziela zarządzanie kolekcją sesji od menu konsolowego. Udostępnia odczyt, zapis lub aktualizację sesji, dodawanie ćwiczenia do sesji z danego dnia i usuwanie sesji. Zapis wykorzystuje plik tymczasowy i atomową podmianę pliku docelowego.

---

## 3. Kluczowy fragment kodu i uzasadnienie inżynierskie

Kluczową częścią Zadania 3 jest wspólna metoda `volume()` używana przez agregat. Sesja nie musi znać szczegółów obliczeń konkretnego rodzaju ćwiczenia — wywołuje metodę polimorficznie dla każdego elementu kolekcji.

```python
class Exercise:
    def volume(self) -> float:
        return round(self.sets * self.reps * self.weight_kg, 2)


class AssistedBodyweightExercise(Exercise):
    def volume(self) -> float:
        effective_weight = self.body_weight_kg - self.assistance_kg
        return round(self.sets * self.reps * effective_weight, 2)


class WorkoutSession:
    def session_tonnage(self) -> float:
        return round(sum(exercise.volume() for exercise in self._exercises), 2)
```

Takie rozwiązanie łączy kompozycję (sesja zawiera listę ćwiczeń) z dziedziczeniem i polimorfizmem. Reguły poprawności danych znajdują się w modelu, a zapis i odczyt kolekcji są wydzielone do repozytorium.

---

## 4. Weryfikacja i wyniki testów

Testy uruchamia się z katalogu `src` poleceniem:

```text
python test_models.py
```

Skrypt zakończył się powodzeniem: wszystkie siedem scenariuszy przeszło.

| Nr | Scenariusz | Sprawdzany wynik |
| --- | --- | --- |
| 1 | Poprawne tworzenie ćwiczeń i sesji | Objętość ćwiczeń oraz łączny tonaż sesji są zgodne z obliczeniami. |
| 2 | Błędne dane | Konstruktor i settery odrzucają zerową liczbę serii lub powtórzeń oraz ujemny ciężar. |
| 3 | Sortowanie sesji | `list.sort()` ustawia sesje chronologicznie przez `WorkoutSession.__lt__`. |
| 4 | Round-trip serializacji | Sesja odtworzona przez `from_dict()` jest równa oryginałowi, a jej słownik ma tę samą zawartość. |
| 5 | Repozytorium JSON | Zapis, odczyt, dodanie ćwiczenia do istniejącej sesji i usunięcie sesji działają poprawnie. |
| 6 | Niezmienność ID | Próba przypisania nowego ID ćwiczeniu lub sesji kończy się `AttributeError`. |
| 7 | Dziedziczenie i polimorfizm | Podklasa jest instancją `Exercise`, oblicza objętość zgodnie z własną regułą i zachowuje typ po serializacji. |

Przykładowy scenariusz poprawny: dla przysiadu `3` serie × `10` powtórzeń × `50 kg` metoda zwraca `1500 kg`. Scenariusz błędnych danych potwierdza odrzucenie `sets = 0`, `reps = 0` i `weight_kg = -5`.

Walidację wejścia menu można sprawdzić, wpisując `8` przy pytaniu `Wybierz opcję [0-7]`. Walidator odrzuca tę wartość komunikatem `Błąd: Wartość > 7` i ponownie prosi o wybór.

---

## 5. Podział pracy i historia Git

Podział odpowiedzialności poniżej opisuje główne obszary kodu. Historia repozytorium zawiera również zmiany współdzielone, dlatego liczby commitów nie są równoważne procentowemu wkładowi w każdą funkcję.

| Osoba / login Git | Główne obszary i funkcjonalności | Liczba commitów w historii |
| --- | --- | ---: |
| Dawid Mucha (`dawidmuchapk`) | Modele domenowe, walidatory, dane przykładowe oraz część funkcji zapisu i podsumowań. | 10 |
| Dawid Sałek (`dawidsalek6`) | Menu główne, usługi aplikacji i część warstwy zapisu/odczytu. | 18 |
| Autor `dawid` | Autor jednego commitu; przypisanie tego konta do członka zespołu wymaga potwierdzenia. | 1 |

Liczby pochodzą z `git log` dla dostępnej historii repozytorium. Przed oddaniem należy potwierdzić, do kogo należy konto `dawid`, i uzupełnić numer albumu Dawida Sałka.
