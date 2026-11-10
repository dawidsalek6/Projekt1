import os
import tempfile

from models import (
    BodyweightExercise,
    CardioExercise,
    Exercise,
    StrengthExercise,
    WorkoutSessionManager,
)
from storage import WorkoutSessionRepository


def test_kontrakt_abstrakcyjny_i_podklasy():
    try:
        Exercise(1, "Nieokreślone")
        assert False, "Nie można tworzyć instancji klasy abstrakcyjnej"
    except TypeError:
        pass

    strength = StrengthExercise(1, "Przysiad", 3, 10, 40.0)
    cardio = CardioExercise(2, "Bieg", 30.0, 5.0, 140)
    assert strength.calculate_tonnage_kg() == 1200.0
    assert cardio.calculate_tonnage_kg() == 0.0


def test_polimorficzne_kalkulacje_menedzera():
    manager = WorkoutSessionManager(
        1,
        "2026-11-10",
        [
            StrengthExercise(1, "Przysiad", 3, 10, 40.0),
            CardioExercise(2, "Bieg", 30.0, 5.0, 140),
            BodyweightExercise(3, "Pompki", 2, 8, 70.0),
        ],
    )
    assert manager.total_burn_kcal(70.0) == 338.2
    assert manager.total_tonnage_kg() == 2320.0


def test_operacje_na_kolekcji():
    manager = WorkoutSessionManager(
        2,
        "2026-11-10",
        [
            StrengthExercise(11, "Wyciskanie", 4, 8, 50.0),
            CardioExercise(12, "Rower", 20.0, 7.0, 125),
        ],
    )
    assert [item.exercise_id for item in manager.filter_exercises(
        lambda item: item.calculate_tonnage_kg() > 0
    )] == [11]
    assert manager.remove_exercise(12) is True
    assert manager.remove_exercise(12) is False
    assert len(manager.exercises) == 1


def test_dyskryminator_json_i_round_trip():
    original = WorkoutSessionManager(
        3,
        "2026-11-10",
        [
            StrengthExercise(21, "Martwy ciąg", 3, 5, 100.0),
            CardioExercise(22, "Bieg", 25.0, 4.0, 135),
            BodyweightExercise(23, "Pompki", 2, 12, 70.0),
        ],
    )
    payload = original.to_dict()
    assert [item["type"] for item in payload["exercises"]] == ["strength", "cardio", "bodyweight"]
    restored = WorkoutSessionManager.from_dict(payload)
    assert restored.to_dict() == payload
    assert type(restored.exercises[0]) is StrengthExercise
    assert type(restored.exercises[1]) is CardioExercise
    assert type(restored.exercises[2]) is BodyweightExercise

    try:
        Exercise.from_dict({"type": "unknown"})
        assert False, "Nieznany dyskryminator powinien zostać odrzucony"
    except ValueError:
        pass


def test_repozytorium_sesji_json():
    session = WorkoutSessionManager(
        4,
        "2026-11-10",
        [StrengthExercise(31, "Wiosłowanie", 3, 8, 40.0)],
    )
    with tempfile.TemporaryDirectory(dir=".") as directory:
        repository = WorkoutSessionRepository(os.path.join(directory, "sessions.json"))
        repository.save(session)
        loaded = repository.get_all()
        assert len(loaded) == 1
        assert loaded[0].to_dict() == session.to_dict()
        assert repository.delete(4) is True
        assert repository.get_all() == []


def test_dane_brzegowe():
    invalid_builders = [
        lambda: StrengthExercise(1, "Przysiad", 0, 10, 50.0),
        lambda: StrengthExercise(1, "Przysiad", 3, 0, 50.0),
        lambda: StrengthExercise(1, "Przysiad", 3, 10, -1.0),
        lambda: CardioExercise(2, "Bieg", 0, 5.0, 140),
        lambda: CardioExercise(2, "Bieg", 30, -1.0, 140),
        lambda: CardioExercise(2, "Bieg", 30, 5.0, 0),
        lambda: BodyweightExercise(3, "Pompki", 2, 10, 0),
    ]
    for build in invalid_builders:
        try:
            build()
            assert False, "Niepoprawne dane powinny zostać odrzucone"
        except (TypeError, ValueError):
            pass


def run_tests() -> None:
    tests = [
        test_kontrakt_abstrakcyjny_i_podklasy,
        test_polimorficzne_kalkulacje_menedzera,
        test_operacje_na_kolekcji,
        test_dyskryminator_json_i_round_trip,
        test_repozytorium_sesji_json,
        test_dane_brzegowe,
    ]
    for number, test in enumerate(tests, 1):
        test()
        print(f"TEST {number} - {test.__name__}: OK")
    print(f"\nWszystkie {len(tests)} testów zakończone powodzeniem!")

#
if __name__ == "__main__":
    run_tests()
