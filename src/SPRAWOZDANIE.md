# Sprawozdanie z Zadania Laboratoryjnego nr [1]
**Przedmiot:** Programowanie w języku Python (`IwIK-S1`)  
**Projekt:** [FitTrack Pro]  
**Zespół (Dawid Mucha, Dawid Sałek):**  
1. [Dawid Mucha](nr albumu: [164852]) – login Git: `[dawidmuchapk]`
2. [Dawid Sałek] (nr albumu: [NUMER]) – login Git: `[dawidsalek6]`  
**Data oddania:** [27.10.2026]  

---

## 1. Cel i Zakres Inżynierski Zadania
Głównym założeniem naszego projektu jest wprowadzanie i zaimplementowanie aplikacji konsolowej, umożliwiającej zarządzanie dziennika treningów siłowych, makroskładników i stopera przerw. Aplikacja umożliwi poznanie sposobu dzielenia programu na pliki, zapisywania i wyświetlania danych, sprawdzania poprawności wpisywanych informacji oraz tworzenia menu, które pozwala użytkownikowi korzystać z różnych funkcji programu. Dane zapisywane są w pamięci komputerowej obsługując pliki csv oraz json.
---

## 2. Architektura Rozwiązania i Struktura Modułów
* `data/nutrition,workouts.csv,user_profile.json` – [przechowuje dane dotyczące ćwiczeń, treningów i makroskładników.]
* `src/validators.py` – [sprawdza poprawność danych wpisywanych przez użytkownika, np. liczb i nazw ćwiczeń.]
* `src/services.py` – [odpowiada za wykonywanie głównych operacji, takich jak wyświetlanie ćwiczeń, dodawanie nowych rekordów i filtrowanie danych.]
* `src/main.py` – [uruchamia program, wyświetla menu główne i pozwala użytkownikowi wybrać odpowiednią funkcję.]
*` src/storage.py –[pozwala zapisywać podane dane do plików zapisu]

---


## 3. Kluczowy Fragment Kodu i Uzasadnienie Inżynierskie
Services i funkcje

**Uzasadnienie wyboru:**  
Wybrany przez nas fragment kodu jest najbardziej kluczowy, ponieważ odpowiada za główne działanie kodu oraz przechowywanie wszystkich siedmiu funkcji zamieszczonych w konsoli main.
---

## 4. Scenariusze Weryfikacji i Wyniki Testów
*(Dowód działania programu w konsoli. Należy przedstawić przynajmniej dwa scenariusze).*

### Scenariusz A: Ścieżka poprawna (Happy Path)
* **Dane wejściowe:** [Opis danych]
Przy zapisywaniu ćwiczenia należy podać odpowiednie wartości, a kod zapisuje podane dane do pliku csv
* **Oczekiwany i uzyskany wynik:**
```text: zapisanie do pliku csv
[Wklej listing z konsoli lub opis poprawnego zachowania]
```Zapisano trening: Przysiad | data: 2026-01-02 | 3x3, 10.0 kg | objętość: 90.0 kg

### Scenariusz B: Obsługa błędów i wartości brzegowych
* **Dane wejściowe (błędne):** [np. litery zamiast cyfr, puste wejście, wartość spoza zakresu]
W przypadku podania wartości większej niż posiada menu konsolowe, konsola poprosi o podanie poprawnej wartosci
* **Reakcja programu:**
```text 
Wybierz opcję [0-7]: 8
Błąd: Wartość > 7
[Wklej listing z konsoli pokazujący bezpieczną reakcję na błąd]
```
Wybierz opcję [0-7]: 8
Błąd: Wartość > 7
---

## 5. Podział Pracy w Zespole
*(Precyzyjne i uczciwe rozliczenie wkładu obu członków zespołu – weryfikowane z historią commitów `git log`).*
* **[Dawid Mucha]:**
  * Odpowiedzialność za moduły: `src/validators.py, src/data.py, src/init.py`
  * Zaimplementowane funkcjonalności: [Walidator, baza danych ćwiczeń oraz makroskładników]
  * Liczba wykonanych commitów: [...]
* **[Dawid Sałek]:**
  * Odpowiedzialność za moduły: `src/main.py, src/__init__.py, src/services.py`
  * Zaimplementowane funkcjonalności: [Menu główne, wybór poszczególnych treningów i makroskładników]
  * Liczba wykonanych commitów: [...]
