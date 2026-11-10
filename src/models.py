from abc import ABC, abstractmethod
from typing import Any, ClassVar, Self


# stworzenie abstrakcyjnej klasy
class Exercise(ABC):
    #Abstrakcyjny kontrakt wspólny dla ćwiczeń treningowych.

    __slots__ = ("_exercise_id", "name")
    type_tag: ClassVar[str]

    def __init__(self, exercise_id: int, name: str) -> None:
        self._exercise_id = int(exercise_id)
        self.name = str(name).strip()
        if not self.name:
            raise ValueError("Nazwa ćwiczenia nie może być pusta.")

    @property
    def exercise_id(self) -> int:
        return self._exercise_id

    @abstractmethod
    def calculate_burn_kcal(self, user_weight_kg: float) -> float:
        """Szacuje wydatek energetyczny ćwiczenia dla masy użytkownika."""

    def calculate_tonnage_kg(self) -> float:
        """Ćwiczenia bez zewnętrznego obciążenia nie zwiększają tonażu."""
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type_tag,
            "exercise_id": self.exercise_id,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Exercise":
        type_tag = str(data.get("type", ""))
        exercise_class = EXERCISE_REGISTRY.get(type_tag)
        if exercise_class is None:
            raise ValueError(f"Nieznany typ ćwiczenia w JSON: {type_tag!r}.")
        return exercise_class.from_dict(data)

    def __eq__(self, other: object) -> bool:
        other_to_dict = getattr(other, "to_dict", None)
        return type(self) is type(other) and callable(other_to_dict) and self.to_dict() == other_to_dict()

    def __repr__(self) -> str:
        return f"{type(self).__name__}(exercise_id={self.exercise_id}, name={self.name!r})"


class StrengthExercise(Exercise):
    """Ćwiczenie siłowe opisane seriami, powtórzeniami i obciążeniem."""

    __slots__ = ("_sets", "_reps", "_load_kg")
    type_tag = "strength"

    def __init__(
            self,
            exercise_id: int,
            name: str,
            sets: int,
            reps: int,
            load_kg: float
    ) -> None:
        super().__init__(exercise_id, name)
        self.sets = sets
        self.reps = reps
        self.load_kg = load_kg

    @property
    def sets(self) -> int:
        return self._sets

    @sets.setter
    def sets(self, value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError("Liczba serii musi być dodatnią liczbą całkowitą.")
        self._sets = value

    @property
    def reps(self) -> int:
        return self._reps

    @reps.setter
    def reps(self, value: int) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise ValueError("Liczba powtórzeń musi być dodatnią liczbą całkowitą.")
        self._reps = value

    @property
    def load_kg(self) -> float:
        return self._load_kg

    @load_kg.setter
    def load_kg(self, value: float | int) -> None:
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise TypeError("Obciążenie musi być wartością liczbową.")
        if value < 0:
            raise ValueError("Obciążenie nie może być ujemne.")
        self._load_kg = round(float(value), 2)

    # inmplementacja abstrakcyjnej metody
    def calculate_burn_kcal(self, user_weight_kg: float) -> float:
        if user_weight_kg <= 0:
            raise ValueError("Masa użytkownika musi być większa od 0 kg.")
        return round((user_weight_kg + self.load_kg) * self.sets * self.reps * 0.01, 2)

    def calculate_tonnage_kg(self) -> float:
        return round(self.sets * self.reps * self.load_kg, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "sets": self.sets,
            "reps": self.reps,
            "load_kg": self.load_kg,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            exercise_id=int(data["exercise_id"]),
            name=str(data["name"]),
            sets=int(data["sets"]),
            reps=int(data["reps"]),
            load_kg=float(data["load_kg"]),
        )


class CardioExercise(Exercise):
    """Ćwiczenie cardio opisane czasem, dystansem i tętnem."""

    __slots__ = ("_duration_min", "_distance_km", "_heart_rate_bpm")
    type_tag = "cardio"

    def __init__(
            self,
            exercise_id: int,
            name: str,
            duration_min: float,
            distance_km: float,
            heart_rate_bpm: int
    ) -> None:
        super().__init__(exercise_id, name)
        if duration_min <= 0:
            raise ValueError("Czas ćwiczenia musi być większy od 0 minut.")
        if distance_km < 0:
            raise ValueError("Dystans nie może być ujemny.")
        if not isinstance(heart_rate_bpm, int) or isinstance(heart_rate_bpm, bool) or heart_rate_bpm <= 0:
            raise ValueError("Tętno musi być dodatnią liczbą całkowitą.")
        self._duration_min = round(float(duration_min), 2)
        self._distance_km = round(float(distance_km), 2)
        self._heart_rate_bpm = heart_rate_bpm

    @property
    def duration_min(self) -> float:
        return self._duration_min

    @property
    def distance_km(self) -> float:
        return self._distance_km

    @property
    def heart_rate_bpm(self) -> int:
        return self._heart_rate_bpm

    def calculate_burn_kcal(self, user_weight_kg: float) -> float:
        if user_weight_kg <= 0:
            raise ValueError("Masa użytkownika musi być większa od 0 kg.")
        return round(user_weight_kg * self.duration_min * self.heart_rate_bpm / 1000, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            **super().to_dict(),
            "duration_min": self.duration_min,
            "distance_km": self.distance_km,
            "heart_rate_bpm": self.heart_rate_bpm,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            exercise_id=int(data["exercise_id"]),
            name=str(data["name"]),
            duration_min=float(data["duration_min"]),
            distance_km=float(data["distance_km"]),
            heart_rate_bpm=int(data["heart_rate_bpm"]),
        )


EXERCISE_REGISTRY: dict[str, type[Exercise]] = {
    StrengthExercise.type_tag: StrengthExercise,
    CardioExercise.type_tag: CardioExercise,
}


class WorkoutSessionManager:
    """Menedżer kolekcji ćwiczeń jednej sesji treningowej."""

    __slots__ = ("_session_id", "_date", "_exercises")

    def __init__(
            self,
            session_id: int,
            date: str,
            exercises: list[Exercise] | None = None
    ) -> None:
        self._session_id = int(session_id)
        self._date = str(date).strip()
        self._exercises: list[Exercise] = list(exercises) if exercises is not None else []

    @property
    def session_id(self) -> int:
        return self._session_id

    @property
    def date(self) -> str:
        return self._date

    @property
    def exercises(self) -> list[Exercise]:
        return list(self._exercises)

    def add_exercise(self, exercise: Exercise) -> None:
        self._exercises.append(exercise)

    def remove_exercise(self, exercise_id: int) -> bool:
        for index, exercise in enumerate(self._exercises):
            if exercise.exercise_id == exercise_id:
                del self._exercises[index]
                return True
        return False

    def filter_exercises(self, predicate) -> list[Exercise]:
        return [exercise for exercise in self._exercises if predicate(exercise)]

    def total_burn_kcal(self, user_weight_kg: float) -> float:
        return round(sum(
            exercise.calculate_burn_kcal(user_weight_kg)
            for exercise in self._exercises
        ), 2)

    def total_tonnage_kg(self) -> float:
        return round(sum(exercise.calculate_tonnage_kg() for exercise in self._exercises), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "date": self.date,
            "exercises": [exercise.to_dict() for exercise in self._exercises],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        exercises = [Exercise.from_dict(item) for item in data.get("exercises", [])]
        return cls(int(data["session_id"]), str(data["date"]), exercises)

    def __lt__(self, other: "WorkoutSessionManager") -> bool:
        if not hasattr(other, "date"):
            return NotImplemented
        return self.date < other.date

    def __str__(self) -> str:
        return (
            f"Sesja #{self.session_id} ({self.date}): "
            f"{len(self._exercises)} ćwiczeń, "
            f"tonaże {self.total_tonnage_kg():.2f} kg"
        )


WorkoutSession = WorkoutSessionManager
