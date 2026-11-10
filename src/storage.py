import csv
import json
import os

from models import Exercise, WorkoutSessionManager

trening = "data/workouts.csv"
makro = "data/nutrition.csv"
profil = "data/user_profile.json"
sesje_treningowe = "data/workout_sessions.json"


class WorkoutSessionRepository:
    """Repozytorium sesji treningowych zapisujące agregaty w zagnieżdżonym JSON."""

    def __init__(self, file_path: str = sesje_treningowe) -> None:
        self.file_path = file_path

    def get_all(self) -> list[WorkoutSessionManager]:
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                raw_sessions = json.load(file)
            if not isinstance(raw_sessions, list):
                raise ValueError("Baza sesji musi zawierać listę obiektów.")
            return [WorkoutSessionManager.from_dict(item) for item in raw_sessions]
        except (json.JSONDecodeError, OSError, KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Nie można odczytać bazy sesji {self.file_path}: {error}") from error

    def save(self, session: WorkoutSessionManager) -> None:
        sessions = self.get_all()
        for index, existing in enumerate(sessions):
            if existing.session_id == session.session_id:
                sessions[index] = session
                break
        else:
            sessions.append(session)

        directory = os.path.dirname(self.file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        temporary_path = f"{self.file_path}.tmp"
        with open(temporary_path, "w", encoding="utf-8") as file:
            json.dump([item.to_dict() for item in sessions], file, ensure_ascii=False, indent=2)
        os.replace(temporary_path, self.file_path)

    def add_exercise(self, exercise: Exercise, session_date: str) -> WorkoutSessionManager:
        """Dodaje ćwiczenie do sesji z danego dnia i zapisuje cały agregat."""
        sessions = self.get_all()
        session = next((item for item in sessions if item.date == session_date), None)
        if session is None:
            next_id = max((item.session_id for item in sessions), default=0) + 1
            session = WorkoutSessionManager(next_id, session_date)
        session.add_exercise(exercise)
        self.save(session)
        return session

    def delete(self, session_id: int) -> bool:
        sessions = self.get_all()
        remaining = [item for item in sessions if item.session_id != session_id]
        if len(remaining) == len(sessions):
            return False
        directory = os.path.dirname(self.file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        temporary_path = f"{self.file_path}.tmp"
        with open(temporary_path, "w", encoding="utf-8") as file:
            json.dump([item.to_dict() for item in remaining], file, ensure_ascii=False, indent=2)
        os.replace(temporary_path, self.file_path)
        return True


def upewnij_sie_ze_katalog_istnieje():
    katalog = os.path.dirname(trening)
    if katalog and not os.path.exists(katalog):
        os.makedirs(katalog, exist_ok=True)


def zapisz_cwiczenie(cwiczenie):
    upewnij_sie_ze_katalog_istnieje()

    pola = [
        "id", "data", "cwiczenie", "serie",
        "powtorzenia", "ciezar_kg"
    ]

    istnieje = os.path.exists(trening) and os.path.getsize(trening) > 0

    with open(trening, "a", newline="", encoding="utf-8") as plik:
        writer = csv.DictWriter(
            plik, fieldnames=pola, extrasaction="ignore"
        )

        if not istnieje:
            writer.writeheader()

        writer.writerow(cwiczenie)

    print("Ćwiczenie zapisane!")


def zapisz_posilek(posilek):
    upewnij_sie_ze_katalog_istnieje()

    pola = [
        "id", "data", "nazwa_posilku", "bialko_g",
        "weglowodany_g", "tluszcz_g", "kcal"
    ]

    istnieje = os.path.exists(makro) and os.path.getsize(makro) > 0

    with open(makro, "a", newline="", encoding="utf-8") as plik:
        writer = csv.DictWriter(
            plik, fieldnames=pola, extrasaction="ignore"
        )

        if not istnieje:
            writer.writeheader()

        writer.writerow(posilek)


def wczytaj_treningi():
    if not os.path.exists(trening) or os.path.getsize(trening) == 0:
        return []

    treningi = []

    try:
        with open(trening, "r", encoding="utf-8", newline="") as plik:
            reader = csv.DictReader(plik)

            for i, row in enumerate(reader, 1):
                if row.get("cwiczenie"):
                    treningi.append({
                        "id": int(row["id"]) if row.get("id") else i,
                        "data": row.get("data", ""),
                        "cwiczenie": row["cwiczenie"],
                        "serie": int(row["serie"]),
                        "powtorzenia": int(row["powtorzenia"]),
                        "ciezar_kg": float(row["ciezar_kg"])
                    })

    except (ValueError, OSError, csv.Error, KeyError) as e:
        print(f"Błąd odczytu pliku {trening}: {e}")
        return []

    return treningi


def wczytaj_posilki():
    if not os.path.exists(makro) or os.path.getsize(makro) == 0:
        return []

    posilki = []

    try:
        with open(makro, "r", encoding="utf-8", newline="") as plik:
            reader = csv.DictReader(plik)

            for row in reader:
                if row.get("nazwa_posilku"):
                    posilki.append({
                        "id": int(row["id"]) if row.get("id") else len(posilki) + 1,
                        "data": row.get("data", ""),
                        "nazwa_posilku": row["nazwa_posilku"],
                        "bialko_g": float(row["bialko_g"]),
                        "weglowodany_g": float(row["weglowodany_g"]),
                        "tluszcz_g": float(row["tluszcz_g"]),
                        "kcal": float(row["kcal"])
                    })

    except (ValueError, OSError, csv.Error, KeyError) as e:
        print(f"Błąd odczytu pliku {makro}: {e}")
        return []

    return posilki


def wczytaj_profil_json():
    domyslny_profil = {
        "cele_dzienne": {
            "kalorie": 2500,
            "bialko": 160,
            "weglowodany": 250,
            "tluszcze": 70
        }
    }

    if not os.path.exists(profil):
        return domyslny_profil

    try:
        with open(profil, "r", encoding="utf-8") as plik:
            return json.load(plik)

    except (json.JSONDecodeError, OSError) as e:
        print(f"Błąd odczytu profilu JSON: {e}")
        return domyslny_profil
