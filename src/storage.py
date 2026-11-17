"""Warstwa persystencji FitTrack Pro oparta na relacyjnej bazie SQLite."""

import csv
import json
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from models import (
    Exercise,
    WorkoutSessionManager,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = Path(os.environ.get("FITTRACK_DB_PATH", str(DATA_DIR / "fittrack.db")))
LEGACY_WORKOUTS = DATA_DIR / "workouts.csv"
LEGACY_NUTRITION = DATA_DIR / "nutrition.csv"
LEGACY_PROFILE = DATA_DIR / "user_profile.json"
LEGACY_SESSIONS = DATA_DIR / "workout_sessions.json"

DEFAULT_PROFILE = {
    "cele_dzienne": {
        "kalorie": 2500,
        "bialko": 160,
        "weglowodany": 250,
        "tluszcze": 70,
    }
}


def _connect(db_path: str | os.PathLike[str] | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path is not None else DB_PATH
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def _database(db_path: str | os.PathLike[str] | None = None):
    connection = _connect(db_path)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            migration_name TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY,
            workout_date TEXT NOT NULL,
            exercise_name TEXT NOT NULL,
            sets INTEGER NOT NULL CHECK (sets > 0),
            reps INTEGER NOT NULL CHECK (reps > 0),
            load_kg REAL NOT NULL CHECK (load_kg >= 0)
        );

        CREATE TABLE IF NOT EXISTS nutrition_entries (
            id INTEGER PRIMARY KEY,
            entry_date TEXT NOT NULL,
            meal_name TEXT NOT NULL,
            protein_g REAL NOT NULL CHECK (protein_g >= 0),
            carbohydrates_g REAL NOT NULL CHECK (carbohydrates_g >= 0),
            fat_g REAL NOT NULL CHECK (fat_g >= 0),
            kcal REAL NOT NULL CHECK (kcal >= 0)
        );

        CREATE TABLE IF NOT EXISTS workout_sessions (
            session_id INTEGER PRIMARY KEY,
            session_date TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS session_exercises (
            exercise_id INTEGER PRIMARY KEY,
            session_id INTEGER NOT NULL,
            exercise_type TEXT NOT NULL CHECK (exercise_type IN ('strength', 'cardio')),
            name TEXT NOT NULL,
            sets INTEGER,
            reps INTEGER,
            load_kg REAL,
            duration_min REAL,
            distance_km REAL,
            heart_rate_bpm INTEGER,
            FOREIGN KEY (session_id) REFERENCES workout_sessions(session_id) ON DELETE CASCADE,
            CHECK (
                (exercise_type = 'strength' AND sets IS NOT NULL AND sets > 0
                    AND reps IS NOT NULL AND reps > 0 AND load_kg IS NOT NULL AND load_kg >= 0
                    AND duration_min IS NULL AND distance_km IS NULL AND heart_rate_bpm IS NULL)
                OR
                (exercise_type = 'cardio' AND duration_min IS NOT NULL AND duration_min > 0
                    AND distance_km IS NOT NULL AND distance_km >= 0
                    AND heart_rate_bpm IS NOT NULL AND heart_rate_bpm > 0
                    AND sets IS NULL AND reps IS NULL AND load_kg IS NULL)
            )
        );

        CREATE TABLE IF NOT EXISTS user_profile (
            profile_id INTEGER PRIMARY KEY CHECK (profile_id = 1),
            calories_goal REAL NOT NULL,
            protein_goal REAL NOT NULL,
            carbohydrates_goal REAL NOT NULL,
            fat_goal REAL NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_workouts_date ON workouts(workout_date);
        CREATE INDEX IF NOT EXISTS idx_nutrition_date ON nutrition_entries(entry_date);
        CREATE INDEX IF NOT EXISTS idx_sessions_date ON workout_sessions(session_date);
        """
    )
    connection.execute(
        """INSERT OR IGNORE INTO user_profile
           (profile_id, calories_goal, protein_goal, carbohydrates_goal, fat_goal)
           VALUES (1, ?, ?, ?, ?)""",
        (
            DEFAULT_PROFILE["cele_dzienne"]["kalorie"],
            DEFAULT_PROFILE["cele_dzienne"]["bialko"],
            DEFAULT_PROFILE["cele_dzienne"]["weglowodany"],
            DEFAULT_PROFILE["cele_dzienne"]["tluszcze"],
        ),
    )


def _migration_done(connection: sqlite3.Connection, name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM schema_migrations WHERE migration_name = ?", (name,)
    ).fetchone() is not None


def _mark_migration(connection: sqlite3.Connection, name: str) -> None:
    connection.execute(
        "INSERT OR IGNORE INTO schema_migrations (migration_name) VALUES (?)", (name,)
    )


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def _migrate_legacy_files(connection: sqlite3.Connection) -> None:
    """Jednorazowo importuje CSV/JSON; pliki źródłowe pozostają nietknięte."""
    migrations = (
        ("legacy_workouts_csv", LEGACY_WORKOUTS),
        ("legacy_nutrition_csv", LEGACY_NUTRITION),
        ("legacy_profile_json", LEGACY_PROFILE),
        ("legacy_sessions_json", LEGACY_SESSIONS),
    )
    for migration_name, source_path in migrations:
        if _migration_done(connection, migration_name) or not source_path.exists():
            continue

        connection.execute("SAVEPOINT legacy_import")
        try:
            if migration_name == "legacy_workouts_csv":
                for index, row in enumerate(_read_csv(source_path), 1):
                    name = row.get("cwiczenie")
                    if not name:
                        continue
                    legacy_id = int(row.get("id") or index)
                    if connection.execute(
                        "SELECT 1 FROM workouts WHERE id = ?", (legacy_id,)
                    ).fetchone():
                        legacy_id = None
                    connection.execute(
                        """INSERT INTO workouts
                           (id, workout_date, exercise_name, sets, reps, load_kg)
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (
                            legacy_id, row.get("data", ""), name,
                            int(row["serie"]), int(row["powtorzenia"]), float(row["ciezar_kg"]),
                        ),
                    )
            elif migration_name == "legacy_nutrition_csv":
                for index, row in enumerate(_read_csv(source_path), 1):
                    name = row.get("nazwa_posilku")
                    if not name:
                        continue
                    legacy_id = int(row.get("id") or index)
                    if connection.execute(
                        "SELECT 1 FROM nutrition_entries WHERE id = ?", (legacy_id,)
                    ).fetchone():
                        legacy_id = None
                    connection.execute(
                        """INSERT INTO nutrition_entries
                           (id, entry_date, meal_name, protein_g, carbohydrates_g, fat_g, kcal)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            legacy_id, row.get("data", ""), name,
                            float(row["bialko_g"]), float(row["weglowodany_g"]),
                            float(row["tluszcz_g"]), float(row["kcal"]),
                        ),
                    )
            elif migration_name == "legacy_profile_json":
                with source_path.open("r", encoding="utf-8") as stream:
                    goals = json.load(stream).get("cele_dzienne", {})
                connection.execute(
                    """UPDATE user_profile SET calories_goal = ?, protein_goal = ?,
                       carbohydrates_goal = ?, fat_goal = ? WHERE profile_id = 1""",
                    (
                        float(goals.get("kalorie", DEFAULT_PROFILE["cele_dzienne"]["kalorie"])),
                        float(goals.get("bialko", DEFAULT_PROFILE["cele_dzienne"]["bialko"])),
                        float(goals.get("weglowodany", DEFAULT_PROFILE["cele_dzienne"]["weglowodany"])),
                        float(goals.get("tluszcze", DEFAULT_PROFILE["cele_dzienne"]["tluszcze"])),
                    ),
                )
            else:
                with source_path.open("r", encoding="utf-8") as stream:
                    raw_sessions = json.load(stream)
                for raw_session in raw_sessions:
                    payload = dict(raw_session)
                    payload["exercises"] = [
                        {
                            **row,
                            "type": row.get("type", "strength"),
                            "load_kg": row.get("load_kg", row.get("weight_kg")),
                        }
                        for row in raw_session.get("exercises", [])
                    ]
                    session = WorkoutSessionManager.from_dict(payload)
                    _save_session(connection, session)
            _mark_migration(connection, migration_name)
            connection.execute("RELEASE SAVEPOINT legacy_import")
        except (OSError, csv.Error, json.JSONDecodeError, KeyError, TypeError, ValueError, sqlite3.IntegrityError) as error:
            # Zachowujemy oryginał i ponawiamy import przy kolejnym uruchomieniu,
            # zamiast oznaczać niepełną migrację jako zakończoną.
            connection.execute("ROLLBACK TO SAVEPOINT legacy_import")
            connection.execute("RELEASE SAVEPOINT legacy_import")
            print(f"Nie udało się zaimportować {source_path}: {error}")


def initialize_database(db_path: str | os.PathLike[str] | None = None) -> None:
    with _database(db_path) as connection:
        _create_schema(connection)
        if db_path is None or Path(db_path) == DB_PATH:
            _migrate_legacy_files(connection)


def zapisz_cwiczenie(cwiczenie: dict[str, Any]) -> None:
    initialize_database()
    with _database() as connection:
        connection.execute(
            """INSERT INTO workouts
               (id, workout_date, exercise_name, sets, reps, load_kg)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                cwiczenie["id"], cwiczenie["data"], cwiczenie["cwiczenie"],
                cwiczenie["serie"], cwiczenie["powtorzenia"], cwiczenie["ciezar_kg"],
            ),
        )
    print("Ćwiczenie zapisane!")


def zapisz_posilek(posilek: dict[str, Any]) -> None:
    initialize_database()
    with _database() as connection:
        connection.execute(
            """INSERT INTO nutrition_entries
               (id, entry_date, meal_name, protein_g, carbohydrates_g, fat_g, kcal)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                posilek["id"], posilek["data"], posilek["nazwa_posilku"],
                posilek["bialko_g"], posilek["weglowodany_g"],
                posilek["tluszcz_g"], posilek["kcal"],
            ),
        )


def wczytaj_treningi() -> list[dict[str, Any]]:
    initialize_database()
    with _database() as connection:
        rows = connection.execute(
            """SELECT id, workout_date, exercise_name, sets, reps, load_kg
               FROM workouts ORDER BY id"""
        ).fetchall()
    return [
        {
            "id": row["id"], "data": row["workout_date"],
            "cwiczenie": row["exercise_name"], "serie": row["sets"],
            "powtorzenia": row["reps"], "ciezar_kg": row["load_kg"],
        }
        for row in rows
    ]


def wczytaj_posilki() -> list[dict[str, Any]]:
    initialize_database()
    with _database() as connection:
        rows = connection.execute(
            """SELECT id, entry_date, meal_name, protein_g, carbohydrates_g, fat_g, kcal
               FROM nutrition_entries ORDER BY id"""
        ).fetchall()
    return [
        {
            "id": row["id"], "data": row["entry_date"],
            "nazwa_posilku": row["meal_name"], "bialko_g": row["protein_g"],
            "weglowodany_g": row["carbohydrates_g"],
            "tluszcz_g": row["fat_g"], "kcal": row["kcal"],
        }
        for row in rows
    ]


def wczytaj_profil_json() -> dict[str, Any]:
    """Zachowuje dawny kształt wyniku API, choć profil jest już w SQLite."""
    initialize_database()
    with _database() as connection:
        row = connection.execute(
            """SELECT calories_goal, protein_goal, carbohydrates_goal, fat_goal
               FROM user_profile WHERE profile_id = ?""", (1,)
        ).fetchone()
    if row is None:
        return DEFAULT_PROFILE.copy()
    return {
        "cele_dzienne": {
            "kalorie": row["calories_goal"], "bialko": row["protein_goal"],
            "weglowodany": row["carbohydrates_goal"], "tluszcze": row["fat_goal"],
        }
    }


def _exercise_from_row(row: sqlite3.Row) -> Exercise:
    return Exercise.from_dict({
        "type": row["exercise_type"],
        "exercise_id": row["exercise_id"],
        "name": row["name"],
        "sets": row["sets"],
        "reps": row["reps"],
        "load_kg": row["load_kg"],
        "duration_min": row["duration_min"],
        "distance_km": row["distance_km"],
        "heart_rate_bpm": row["heart_rate_bpm"],
    })


def _save_session(connection: sqlite3.Connection, session: WorkoutSessionManager) -> None:
    connection.execute(
        """INSERT INTO workout_sessions (session_id, session_date) VALUES (?, ?)
           ON CONFLICT(session_id) DO UPDATE SET session_date = excluded.session_date""",
        (session.session_id, session.date),
    )
    connection.execute(
        "DELETE FROM session_exercises WHERE session_id = ?", (session.session_id,)
    )
    for exercise in session.exercises:
        values = (
            exercise.exercise_id, session.session_id, exercise.type_tag, exercise.name,
            getattr(exercise, "sets", None), getattr(exercise, "reps", None),
            getattr(exercise, "load_kg", None), getattr(exercise, "duration_min", None),
            getattr(exercise, "distance_km", None), getattr(exercise, "heart_rate_bpm", None),
        )
        connection.execute(
            """INSERT INTO session_exercises
               (exercise_id, session_id, exercise_type, name, sets, reps, load_kg,
                duration_min, distance_km, heart_rate_bpm)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            values,
        )


class WorkoutSessionRepository:
    """Repozytorium relacji sesja → ćwiczenia w bazie SQLite."""

    def __init__(self, file_path: str | os.PathLike[str] | None = None) -> None:
        # file_path utrzymuje zgodność wywołań; wskazuje teraz plik SQLite.
        self.db_path = Path(file_path) if file_path is not None else DB_PATH
        initialize_database(self.db_path)

    def get_all(self) -> list[WorkoutSessionManager]:
        with _database(self.db_path) as connection:
            sessions = connection.execute(
                "SELECT session_id, session_date FROM workout_sessions ORDER BY session_date"
            ).fetchall()
            result = []
            for session in sessions:
                rows = connection.execute(
                    """SELECT * FROM session_exercises WHERE session_id = ?
                       ORDER BY exercise_id""", (session["session_id"],)
                ).fetchall()
                result.append(WorkoutSessionManager(
                    session["session_id"], session["session_date"],
                    [_exercise_from_row(row) for row in rows],
                ))
            return result

    def save(self, session: WorkoutSessionManager) -> None:
        with _database(self.db_path) as connection:
            _save_session(connection, session)

    def next_exercise_id(self) -> int:
        with _database(self.db_path) as connection:
            workout_id = connection.execute(
                "SELECT COALESCE(MAX(id), 0) FROM workouts"
            ).fetchone()[0]
            session_exercise_id = connection.execute(
                "SELECT COALESCE(MAX(exercise_id), 0) FROM session_exercises"
            ).fetchone()[0]
            return max(workout_id, session_exercise_id) + 1

    def add_exercise(self, exercise: Exercise, session_date: str) -> WorkoutSessionManager:
        with _database(self.db_path) as connection:
            session_row = connection.execute(
                "SELECT session_id FROM workout_sessions WHERE session_date = ?",
                (session_date,),
            ).fetchone()
            if session_row is None:
                next_id = connection.execute(
                    "SELECT COALESCE(MAX(session_id), 0) + 1 FROM workout_sessions"
                ).fetchone()[0]
                connection.execute(
                    "INSERT INTO workout_sessions (session_id, session_date) VALUES (?, ?)",
                    (next_id, session_date),
                )
                session_id = next_id
            else:
                session_id = session_row["session_id"]
            session = WorkoutSessionManager(session_id, session_date)
            sets = getattr(exercise, "sets", None)
            reps = getattr(exercise, "reps", None)
            load_kg = getattr(exercise, "load_kg", None)
            if sets is not None:
                connection.execute(
                    """INSERT INTO workouts
                       (id, workout_date, exercise_name, sets, reps, load_kg)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (exercise.exercise_id, session_date, exercise.name, sets, reps, load_kg),
                )
            values = (
                exercise.exercise_id, session_id, exercise.type_tag, exercise.name,
                getattr(exercise, "sets", None), getattr(exercise, "reps", None),
                getattr(exercise, "load_kg", None), getattr(exercise, "duration_min", None),
                getattr(exercise, "distance_km", None), getattr(exercise, "heart_rate_bpm", None),
            )
            connection.execute(
                """INSERT INTO session_exercises
                   (exercise_id, session_id, exercise_type, name, sets, reps, load_kg,
                    duration_min, distance_km, heart_rate_bpm)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", values,
            )
        session = next((item for item in self.get_all() if item.date == session_date), session)
        return session

    def delete(self, session_id: int) -> bool:
        with _database(self.db_path) as connection:
            cursor = connection.execute(
                "DELETE FROM workout_sessions WHERE session_id = ?", (session_id,)
            )
            return cursor.rowcount > 0
