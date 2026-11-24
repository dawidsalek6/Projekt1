import json
import os
import sqlite3
import tempfile

from database import BazaDanych, RepozytoriumSesjiTreningowych
from models import CardioExercise, StrengthExercise, WorkoutSessionManager


def _memory_database() -> BazaDanych:
    baza = BazaDanych(
        ":memory:", stary_plik_treningow=None, stary_plik_posilkow=None,
        stary_plik_profilu=None, stary_plik_sesji=None,
    )
    baza.inicjalizuj()
    return baza


def test_klucz_obcy():
    baza = _memory_database()
    with baza.polaczenie() as polaczenie:
        assert polaczenie.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        try:
            polaczenie.execute(
                """INSERT INTO exercises
                   (session_id, exercise_type, name, sets, reps, weight_kg)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (999, "strength", "Przysiad", 3, 10, 40.0),
            )
            assert False, "Klucz obcy powinien odrzucić nieistniejącą sesję"
        except sqlite3.IntegrityError:
            pass
        else:
            assert False, "Oczekiwano sqlite3.IntegrityError dla osieroconego wpisu"


def test_zapis_odczyt():
    baza = _memory_database()
    repository = RepozytoriumSesjiTreningowych(baza)
    expected = WorkoutSessionManager(
        1,
        "2026-11-17",
        [
            StrengthExercise(1, "Przysiad", 3, 10, 40.0),
            CardioExercise(2, "Bieg", 30.0, 5.0, 140),
        ],
    )

    repository.zapisz(expected, nazwa_zawodnika="Dawid")
    restored = repository.pobierz_wszystkie()

    assert len(restored) == 1
    assert restored[0].to_dict() == expected.to_dict()


def test_usuwanie():
    baza = _memory_database()
    repository = RepozytoriumSesjiTreningowych(baza)
    session_id = repository.zapisz(
        WorkoutSessionManager(
            1, "2026-11-17", [StrengthExercise(1, "Martwy ciąg", 3, 5, 80.0)]
        )
    )

    assert repository.usun(session_id) is True
    with baza.polaczenie() as polaczenie:
        count = polaczenie.execute(
            "SELECT COUNT(*) FROM exercises WHERE session_id = ?", (session_id,)
        ).fetchone()[0]
    assert count == 0


def test_migracja_json():
    with tempfile.TemporaryDirectory() as directory:
        database_path = os.path.join(directory, "fittrack.db")
        source_path = os.path.join(directory, "workout_sessions.json")
        dane = [
            {
                "session_id": 7,
                "date": "2026-11-16",
                "exercises": [
                    {
                        "type": "strength", "exercise_id": 15, "name": "Wyciskanie",
                        "sets": 4, "reps": 8, "load_kg": 50.0,
                    }
                ],
            }
        ]
        with open(source_path, "w", encoding="utf-8") as strumien:
            json.dump(dane, strumien, ensure_ascii=False)
        baza = BazaDanych(
            database_path, stary_plik_treningow=None, stary_plik_posilkow=None,
            stary_plik_profilu=None, stary_plik_sesji=source_path,
        )

        baza.inicjalizuj()
        restored = RepozytoriumSesjiTreningowych(baza).pobierz_wszystkie()

        assert len(restored) == 1
        assert restored[0].date == "2026-11-16"
        assert restored[0].exercises[0].name == "Wyciskanie"
        assert not os.path.exists(source_path)
        assert os.path.exists(source_path + ".bak")


def test_pelna_baza():
    with tempfile.TemporaryDirectory() as directory:
        database_path = os.path.join(directory, "fittrack.db")
        source_path = os.path.join(directory, "workout_sessions.json")
        with open(source_path, "w", encoding="utf-8") as strumien:
            json.dump([{
                "session_id": 9, "date": "2026-11-16",
                "exercises": [{
                    "type": "strength", "exercise_id": 91, "name": "Nie importuj",
                    "sets": 1, "reps": 1, "load_kg": 1.0,
                }],
            }], strumien)
        baza = BazaDanych(
            database_path, stary_plik_treningow=None, stary_plik_posilkow=None,
            stary_plik_profilu=None, stary_plik_sesji=None,
        )
        baza.inicjalizuj()
        RepozytoriumSesjiTreningowych(baza).zapisz(
            WorkoutSessionManager(1, "2026-11-17", [StrengthExercise(1, "Przysiad", 2, 5, 20)])
        )
        database_with_legacy = BazaDanych(
            database_path, stary_plik_treningow=None, stary_plik_posilkow=None,
            stary_plik_profilu=None, stary_plik_sesji=source_path,
        )

        database_with_legacy.inicjalizuj()

        sesje = RepozytoriumSesjiTreningowych(database_with_legacy).pobierz_wszystkie()
        assert len(sesje) == 1
        assert sesje[0].date == "2026-11-17"
        assert os.path.exists(source_path)


def test_migracja_bez_duplikatow_csv_json():
    with tempfile.TemporaryDirectory() as directory:
        database_path = os.path.join(directory, "fittrack.db")
        json_path = os.path.join(directory, "workout_sessions.json")
        csv_path = os.path.join(directory, "workouts.csv")
        with open(json_path, "w", encoding="utf-8") as stream:
            json.dump([{
                "session_id": 1, "date": "2026-11-16",
                "exercises": [{"type": "strength", "exercise_id": 3, "name": "Przysiad",
                               "sets": 3, "reps": 8, "load_kg": 40}],
            }], stream)
        with open(csv_path, "w", encoding="utf-8", newline="") as stream:
            stream.write("id,data,cwiczenie,serie,powtorzenia,ciezar_kg\n")
            stream.write("1,2026-11-16,Przysiad,3,8,40\n")
            stream.write("2,2026-11-16,Wyciskanie,4,6,50\n")
        baza = BazaDanych(
            database_path, stary_plik_treningow=csv_path, stary_plik_posilkow=None,
            stary_plik_profilu=None, stary_plik_sesji=json_path,
        )

        baza.inicjalizuj()
        sesje = RepozytoriumSesjiTreningowych(baza).pobierz_wszystkie()
        cwiczenia = [cwiczenie for sesja in sesje for cwiczenie in sesja.exercises]

        assert len(cwiczenia) == 2
        assert sorted(c.name for c in cwiczenia) == ["Przysiad", "Wyciskanie"]


def test_parametryzowane_wyszukiwanie_cwiczen():
    baza = _memory_database()
    repository = RepozytoriumSesjiTreningowych(baza)
    repository.zapisz(WorkoutSessionManager(1, "2026-11-10", [
        StrengthExercise(1, "Przysiad", 3, 8, 80),
        StrengthExercise(2, "Przysiad przedni", 3, 6, 60),
    ]))
    repository.zapisz(WorkoutSessionManager(2, "2026-11-17", [
        StrengthExercise(3, "Martwy ciąg", 3, 5, 120),
    ]))

    results = repository.wyszukaj_cwiczenia("Przys", "2026-11-01", "2026-11-15", 70)
    assert len(results) == 1
    assert results[0]["cwiczenie"] == "Przysiad"
    # Tekst próbujący zmienić warunek SQL pozostaje zwykłą wartością parametru.
    assert repository.wyszukaj_cwiczenia("%' OR 1=1 --") == []
    try:
        repository.wyszukaj_cwiczenia(sortuj_po="name; DROP TABLE exercises")
        assert False, "Sortowanie musi być ograniczone białą listą"
    except ValueError:
        pass


def test_raport_join_group_by_having():
    repository = RepozytoriumSesjiTreningowych(_memory_database())
    repository.zapisz(WorkoutSessionManager(1, "2026-11-10", [
        StrengthExercise(1, "Przysiad", 3, 8, 80),
        StrengthExercise(2, "Wyciskanie", 4, 6, 50),
        CardioExercise(3, "Bieg", 20, 3, 130),
    ]))
    repository.zapisz(WorkoutSessionManager(2, "2026-11-11", []))

    report = repository.raport_tonazu_sesji(2000)
    assert report == [{
        "session_id": 1, "data": "2026-11-10", "liczba_cwiczen": 2, "tonaz_kg": 3120.0
    }]
    all_rows = repository.raport_tonazu_sesji()
    assert all_rows[1]["liczba_cwiczen"] == 0
    assert all_rows[1]["tonaz_kg"] == 0


def test_rollback_calej_sesji_po_bledzie_check():
    repository = RepozytoriumSesjiTreningowych(_memory_database())
    original = WorkoutSessionManager(1, "2026-11-10", [
        StrengthExercise(1, "Przysiad", 3, 8, 80),
    ])
    repository.zapisz(original)
    # Ograniczenie CHECK/trigger odrzuca ostatnie ćwiczenie po pierwszym INSERT-zie.
    # Transakcja ma odtworzyć także poprzednią wersję sesji.
    invalid_update = WorkoutSessionManager(1, "2026-11-11", [
        StrengthExercise(2, "Martwy ciąg", 3, 5, 100),
        StrengthExercise(3, "Wyciskanie", 3, 8, 1001),
    ])
    try:
        repository.zapisz(invalid_update)
        assert False, "Oczekiwano błędu integralności"
    except sqlite3.IntegrityError:
        pass
    restored = repository.pobierz_wszystkie()
    assert len(restored) == 1
    assert restored[0].to_dict() == original.to_dict()


def run_tests() -> None:
    tests = [
        test_klucz_obcy,
        test_zapis_odczyt,
        test_usuwanie,
        test_migracja_json,
        test_pelna_baza,
        test_migracja_bez_duplikatow_csv_json,
        test_parametryzowane_wyszukiwanie_cwiczen,
        test_raport_join_group_by_having,
        test_rollback_calej_sesji_po_bledzie_check,
    ]
    for number, test in enumerate(tests, 1):
        test()
        print(f"TEST {number} - {test.__name__}: OK")
    print(f"\nWszystkie {len(tests)} testy bazy danych zakończone powodzeniem!")


if __name__ == "__main__":
    run_tests()
