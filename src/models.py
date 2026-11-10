from typing import Any, Self


class Exercise:
    __slots__ = ("_exercise_id", "name", "_sets", "_reps", "_weight_kg")

    def __init__(
            self,
            exercise_id: int,
            name: str,
            sets: int,
            reps: int,
            weight_kg: float
    ) -> None:
        self._exercise_id: int = int(exercise_id)
        self.name: str = str(name).strip()
        self.sets = sets  # Wywołuje setter z walidacją
        self.reps = reps  # Wywołuje setter z walidacją
        self.weight_kg = weight_kg  # Wywołuje setter z walidacją

    @property
    def exercise_id(self) -> int:
        return self._exercise_id

    @property
    def sets(self) -> int:
        return self._sets

    @sets.setter
    def sets(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"Liczba serii musi być liczbą całkowitą większą od 0 (podano: {value}).")
        self._sets = value

    @property
    def reps(self) -> int:
        return self._reps

    @reps.setter
    def reps(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(f"Liczba powtórzeń musi być liczbą całkowitą większą od 0 (podano: {value}).")
        self._reps = value

    @property
    def weight_kg(self) -> float:
        return self._weight_kg

    @weight_kg.setter
    def weight_kg(self, value: float | int) -> None:
        if not isinstance(value, (int, float)):
            raise TypeError("Ciężar musi być wartością liczbową.")
        if value < 0.0:
            raise ValueError(f"Ciężar nie może być ujemny (podano: {value}).")
        self._weight_kg = round(float(value), 2)

    def volume(self) -> float:
        return round(self.sets * self.reps * self.weight_kg, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "exercise_type": "strength",
            "exercise_id": self.exercise_id,
            "name": self.name,
            "sets": self.sets,
            "reps": self.reps,
            "weight_kg": self.weight_kg
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        if cls is Exercise and data.get("exercise_type") == "assisted_bodyweight":
            return AssistedBodyweightExercise(
                exercise_id=int(data["exercise_id"]),
                name=str(data["name"]),
                sets=int(data["sets"]),
                reps=int(data["reps"]),
                body_weight_kg=float(data["body_weight_kg"]),
                assistance_kg=float(data.get("assistance_kg", 0.0))
            )
        return cls(
            exercise_id=int(data["exercise_id"]),
            name=str(data["name"]),
            sets=int(data["sets"]),
            reps=int(data["reps"]),
            weight_kg=float(data["weight_kg"])
        )

    def __repr__(self) -> str:
        return (
            f"Exercise(exercise_id={self.exercise_id}, name={self.name!r}, "
            f"sets={self.sets}, reps={self.reps}, weight_kg={self.weight_kg})"
        )

    def __str__(self) -> str:
        return f"[{self.exercise_id:02d}] {self.name:<20} {self.sets}x{self.reps} @ {self.weight_kg:>6.2f} kg (Objętość: {self.volume():>7.2f} kg)"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Exercise):
            return False
        return self.exercise_id == other.exercise_id

    def __lt__(self, other: "Exercise") -> bool:
        if not isinstance(other, Exercise):
            return NotImplemented
        return (-self.volume(), self.name) < (-other.volume(), other.name)


class AssistedBodyweightExercise(Exercise):

    __slots__ = ("body_weight_kg", "assistance_kg")

    def __init__(
            self,
            exercise_id: int,
            name: str,
            sets: int,
            reps: int,
            body_weight_kg: float,
            assistance_kg: float = 0.0
    ) -> None:
        super().__init__(exercise_id, name, sets, reps, 0.0)
        if body_weight_kg <= 0:
            raise ValueError("Masa ciała musi być większa od 0 kg.")
        if assistance_kg < 0 or assistance_kg > body_weight_kg:
            raise ValueError("Wspomaganie musi mieścić się w zakresie 0-masa ciała.")
        self.body_weight_kg = round(float(body_weight_kg), 2)
        self.assistance_kg = round(float(assistance_kg), 2)

    def volume(self) -> float:
        effective_weight = self.body_weight_kg - self.assistance_kg
        return round(self.sets * self.reps * effective_weight, 2)

    def to_dict(self) -> dict[str, Any]:
        data = super().to_dict()
        data.update({
            "exercise_type": "assisted_bodyweight",
            "body_weight_kg": self.body_weight_kg,
            "assistance_kg": self.assistance_kg
        })
        return data


class WorkoutSession:
    __slots__ = ("_session_id", "_date", "_exercises")

    def __init__(
            self,
            session_id: int,
            date: str,
            exercises: list[Exercise] | None = None
    ) -> None:
        self._session_id: int = int(session_id)
        self._date: str = str(date).strip()
        self._exercises: list[Exercise] = []
        for exercise in exercises or []:
            self.add_exercise(exercise)

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
        if not isinstance(exercise, Exercise):
            raise TypeError("W sesji treningowej można umieszczać wyłącznie instancje klasy Exercise.")
        self._exercises.append(exercise)

    def session_tonnage(self) -> float:
        return round(sum(e.volume() for e in self._exercises), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "date": self.date,
            "exercises": [ex.to_dict() for ex in self._exercises]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        restored_exercises = [Exercise.from_dict(raw) for raw in data.get("exercises", [])]
        return cls(
            session_id=int(data["session_id"]),
            date=str(data["date"]),
            exercises=restored_exercises
        )

    def __repr__(self) -> str:
        return f"WorkoutSession(session_id={self.session_id}, date={self.date!r}, exercises={self._exercises!r})"

    def __str__(self) -> str:
        lines = [f"=== SESJA TRENINGOWA #{self.session_id} ({self.date}) ==="]
        if not self._exercises:
            lines.append("   (Brak ćwiczeń w tej sesji)")
        else:
            lines.extend(f"   • {ex}" for ex in self._exercises)
        lines.append(f"   ŁĄCZNY TONAŻ SESJI: {self.session_tonnage():.2f} kg")
        return "\n".join(lines)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WorkoutSession):
            return False
        return self.session_id == other.session_id and self.date == other.date and self._exercises == other._exercises

    def __lt__(self, other: "WorkoutSession") -> bool:
        if not isinstance(other, WorkoutSession):
            return NotImplemented
        return self.date < other.date
