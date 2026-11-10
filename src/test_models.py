from models import AssistedBodyweightExercise, Exercise, WorkoutSession
from storage import WorkoutSessionRepository
import tempfile
import os


def test_poprawne_instancjonowanie():
    exercise1 = Exercise(
        exercise_id=1,
        name="Przysiad",
        sets=3,
        reps=10,
        weight_kg=50.0
    )

    exercise2 = Exercise(
        exercise_id=2,
        name="Wyciskanie",
        sets=4,
        reps=8,
        weight_kg=60.0
    )

    session = WorkoutSession(
        session_id=1,
        date="2026-11-03",
        exercises=[exercise1, exercise2]
    )

    assert exercise1.volume() == 1500.0
    assert exercise2.volume() == 1920.0
    assert session.session_tonnage() == 3420.0

    print("TEST 1 - Poprawne instancjonowanie: OK")


def test_odrzucanie_blednych_danych():
    try:
        Exercise(3, "Przysiad", 0, 10, 50.0)
        assert False, "Nie wykryto błędnej liczby serii"
    except ValueError:
        pass

    try:
        Exercise(4, "Wyciskanie", 3, 0, 50.0)
        assert False, "Nie wykryto błędnej liczby powtórzeń"
    except ValueError:
        pass

    try:
        Exercise(5, "Martwy ciąg", 3, 10, -5.0)
        assert False, "Nie wykryto ujemnego ciężaru"
    except ValueError:
        pass

    exercise1 = Exercise(1, "Przysiad", 3, 10, 50.0)
    exercise1.sets = 4
    assert exercise1.sets == 4

    try:
        exercise1.sets = 0
        assert False, "Setter powinien odrzucić 0"
    except ValueError:
        pass

    print("TEST 2 - Odrzucanie błędnych danych: OK")


def test_sortowanie_sesji_treningowych():
    session1 = WorkoutSession(1, "2026-11-03")
    session2 = WorkoutSession(2, "2026-11-01")
    session3 = WorkoutSession(3, "2026-11-02")

    sessions = [session1, session2, session3]

    sessions.sort()

    assert sessions[0].date == "2026-11-01"
    assert sessions[1].date == "2026-11-02"
    assert sessions[2].date == "2026-11-03"

    print("TEST 3 - Sortowanie sesji treningowych: OK")


def test_round_trip_serialization(): ## odnawianie plików
    original = WorkoutSession(
        session_id=10,
        date="2026-11-03",
        exercises=[
            Exercise(11, "Przysiad", 3, 10, 50.0),
            Exercise(12, "Wyciskanie", 4, 8, 60.0)
        ]
    )

    serialized = original.to_dict()
    restored = WorkoutSession.from_dict(serialized)

    assert original == restored
    assert original.to_dict() == restored.to_dict()

    print("TEST 4 - Round-Trip Serialization: OK")


def test_repozytorium_json():
    original = WorkoutSession(
        21,
        "2026-11-03",
        [Exercise(22, "Martwy ciąg", 3, 5, 100.0)]
    )
    with tempfile.TemporaryDirectory(dir=".") as directory:
        repository = WorkoutSessionRepository(os.path.join(directory, "sessions.json"))
        repository.save(original)
        restored = repository.get_all()
        assert restored == [original]
        assert restored[0].exercises[0].name == "Martwy ciąg"
        updated = repository.add_exercise(
            Exercise(23, "Wykroki", 2, 10, 20.0), "2026-11-03"
        )
        assert len(updated.exercises) == 2
        assert updated.session_tonnage() == 1900.0
        assert repository.delete(21) is True
        assert repository.get_all() == []
        assert repository.delete(21) is False

    print("TEST 5 - Repozytorium zagnieżdżonego JSON: OK")


def test_niezmiennosc_id():
    exercise = Exercise(31, "Wiosłowanie", 3, 8, 40.0)
    try:
        exercise.exercise_id = 99
        assert False, "Identyfikator ćwiczenia nie powinien być modyfikowalny"
    except AttributeError:
        pass

    session = WorkoutSession(32, "2026-11-03")
    try:
        session.session_id = 99
        assert False, "Identyfikator sesji nie powinien być modyfikowalny"
    except AttributeError:
        pass

    print("TEST 6 - Niezmienność ID: OK")


def test_dziedziczenie_i_polimorfizm():
    regular = Exercise(41, "Wyciskanie", 3, 5, 60.0)
    assisted = AssistedBodyweightExercise(
        42, "Podciąganie", 3, 5, body_weight_kg=80.0, assistance_kg=20.0
    )
    session = WorkoutSession(43, "2026-11-03", [regular, assisted])

    assert isinstance(assisted, Exercise)
    assert regular.volume() == 900.0
    assert assisted.volume() == 900.0
    serialized = session.to_dict()
    restored = WorkoutSession.from_dict(serialized)
    assert isinstance(restored.exercises[1], AssistedBodyweightExercise)
    assert restored.to_dict() == serialized

    print("TEST 7 - Dziedziczenie i polimorfizm: OK")


def uruchom_testy():
    test_poprawne_instancjonowanie()
    test_odrzucanie_blednych_danych()
    test_sortowanie_sesji_treningowych()
    test_round_trip_serialization()
    test_repozytorium_json()
    test_niezmiennosc_id()
    test_dziedziczenie_i_polimorfizm()

    print("\nWszystkie 7 testów zakończone powodzeniem!")


if __name__ == "__main__":
    uruchom_testy()
