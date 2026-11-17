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


def run_tests() -> None:
    tests = [
        test_klucz_obcy,
        test_zapis_odczyt,
        test_usuwanie,
        test_migracja_json,
        test_pelna_baza,
    ]
    for number, test in enumerate(tests, 1):
        test()
        print(f"TEST {number} - {test.__name__}: OK")
    print(f"\nWszystkie {len(tests)} testy bazy danych zakończone powodzeniem!")


if __name__ == "__main__":
    run_tests()
