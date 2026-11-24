from __future__ import annotations

import csv
import json
import os
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator

from models import Exercise, StrengthExercise, WorkoutSessionManager

KATALOG_DANYCH = Path(__file__).resolve().parent / "data"
DOMYSLNA_SCIEZKA_BAZY = Path(os.environ.get("FITTRACK_DB_PATH", str(KATALOG_DANYCH / "fittrack.db")))
DOMYSLNY_PLIK_TRENINGOW = KATALOG_DANYCH / "workouts.csv"
DOMYSLNY_PLIK_POSILKOW = KATALOG_DANYCH / "nutrition.csv"
DOMYSLNY_PLIK_PROFILU = KATALOG_DANYCH / "user_profile.json"
DOMYSLNY_PLIK_SESJI = KATALOG_DANYCH / "workout_sessions.json"

SCHEMAT_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_name TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workout_sessions (
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_str TEXT NOT NULL,
    athlete_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS exercises (
    exercise_id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    exercise_type TEXT NOT NULL CHECK (exercise_type IN ('strength', 'cardio')),
    name TEXT NOT NULL,
    sets INTEGER,
    reps INTEGER,
    weight_kg REAL,
    duration_min REAL,
    distance_km REAL,
    heart_rate_bpm INTEGER,
    FOREIGN KEY (session_id) REFERENCES workout_sessions(session_id) ON DELETE CASCADE,
    CHECK (
        (exercise_type = 'strength' AND sets IS NOT NULL AND sets > 0
         AND reps IS NOT NULL AND reps > 0 AND weight_kg IS NOT NULL AND weight_kg >= 0
         AND weight_kg <= 1000
         AND duration_min IS NULL AND distance_km IS NULL AND heart_rate_bpm IS NULL)
        OR
        (exercise_type = 'cardio' AND duration_min IS NOT NULL AND duration_min > 0
         AND distance_km IS NOT NULL AND distance_km >= 0
         AND heart_rate_bpm IS NOT NULL AND heart_rate_bpm > 0
         AND sets IS NULL AND reps IS NULL AND weight_kg IS NULL)
    )
);

CREATE TABLE IF NOT EXISTS nutrition_entries (
    nutrition_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TEXT NOT NULL,
    meal_name TEXT NOT NULL,
    protein_g REAL NOT NULL CHECK (protein_g >= 0),
    carbohydrates_g REAL NOT NULL CHECK (carbohydrates_g >= 0),
    fat_g REAL NOT NULL CHECK (fat_g >= 0),
    kcal REAL NOT NULL CHECK (kcal >= 0)
);

CREATE TABLE IF NOT EXISTS user_profile (
    profile_id INTEGER PRIMARY KEY CHECK (profile_id = 1),
    calories_goal REAL NOT NULL CHECK (calories_goal >= 0),
    protein_goal REAL NOT NULL CHECK (protein_goal >= 0),
    carbohydrates_goal REAL NOT NULL CHECK (carbohydrates_goal >= 0),
    fat_goal REAL NOT NULL CHECK (fat_goal >= 0)
);

CREATE INDEX IF NOT EXISTS idx_exercises_session ON exercises(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON workout_sessions(date_str);
CREATE INDEX IF NOT EXISTS idx_nutrition_date ON nutrition_entries(entry_date);

-- Zabezpiecza również bazy utworzone przed dodaniem ograniczenia CHECK.
CREATE TRIGGER IF NOT EXISTS trg_exercises_strength_weight_limit_insert
BEFORE INSERT ON exercises
WHEN NEW.exercise_type = 'strength' AND NEW.weight_kg > 1000
BEGIN
    SELECT RAISE(ABORT, 'weight_kg exceeds 1000 kg');
END;

CREATE TRIGGER IF NOT EXISTS trg_exercises_strength_weight_limit_update
BEFORE UPDATE OF exercise_type, weight_kg ON exercises
WHEN NEW.exercise_type = 'strength' AND NEW.weight_kg > 1000
BEGIN
    SELECT RAISE(ABORT, 'weight_kg exceeds 1000 kg');
END;
"""


def pobierz_polaczenie(sciezka_bazy: str | os.PathLike[str] = DOMYSLNA_SCIEZKA_BAZY) -> sqlite3.Connection:
    sciezka = str(sciezka_bazy)
    if sciezka != ":memory:":
        Path(sciezka).parent.mkdir(parents=True, exist_ok=True)
    polaczenie = sqlite3.connect(sciezka)
    polaczenie.execute("PRAGMA foreign_keys = ON")
    polaczenie.row_factory = sqlite3.Row
    return polaczenie


class BazaDanych:
    def __init__(
        self,
        sciezka_bazy: str | os.PathLike[str] = DOMYSLNA_SCIEZKA_BAZY,
        *,
        stary_plik_treningow: str | os.PathLike[str] | None = None,
        stary_plik_posilkow: str | os.PathLike[str] | None = None,
        stary_plik_profilu: str | os.PathLike[str] | None = None,
        stary_plik_sesji: str | os.PathLike[str] | None = None,
    ) -> None:
        self.sciezka_bazy = str(sciezka_bazy)
        uzyj_plikow_zrodlowych = self.sciezka_bazy == str(DOMYSLNA_SCIEZKA_BAZY)
        self.stary_plik_treningow = Path(stary_plik_treningow) if stary_plik_treningow else (
            DOMYSLNY_PLIK_TRENINGOW if uzyj_plikow_zrodlowych else None
        )
        self.stary_plik_posilkow = Path(stary_plik_posilkow) if stary_plik_posilkow else (
            DOMYSLNY_PLIK_POSILKOW if uzyj_plikow_zrodlowych else None
        )
        self.stary_plik_profilu = Path(stary_plik_profilu) if stary_plik_profilu else (
            DOMYSLNY_PLIK_PROFILU if uzyj_plikow_zrodlowych else None
        )
        self.stary_plik_sesji = Path(stary_plik_sesji) if stary_plik_sesji else (
            DOMYSLNY_PLIK_SESJI if uzyj_plikow_zrodlowych else None
        )
        self._polaczenie_pamieciowe = pobierz_polaczenie(":memory:") if self.sciezka_bazy == ":memory:" else None

    def _nowe_polaczenie(self) -> sqlite3.Connection:
        if self._polaczenie_pamieciowe is not None:
            return self._polaczenie_pamieciowe
        return pobierz_polaczenie(self.sciezka_bazy)

    @contextmanager
    def polaczenie(self) -> Iterator[sqlite3.Connection]:
        polaczenie = self._nowe_polaczenie()
        try:
            with polaczenie:
                yield polaczenie
        finally:
            if self._polaczenie_pamieciowe is None:
                polaczenie.close()

    def inicjalizuj(self) -> None:
        archiwizuj_po_zatwierdzeniu = False
        with self.polaczenie() as polaczenie:
            polaczenie.executescript(SCHEMAT_SQL)
            polaczenie.execute(
                """INSERT OR IGNORE INTO user_profile
                   (profile_id, calories_goal, protein_goal, carbohydrates_goal, fat_goal)
                   VALUES (1, 2500, 160, 250, 70)"""
            )

            liczba_sesji = polaczenie.execute(
                "SELECT COUNT(*) FROM workout_sessions"
            ).fetchone()[0]
            if liczba_sesji == 0:
                archiwizuj_po_zatwierdzeniu = self._migruj_treningi(polaczenie)

            self._migruj_posilki_i_profil(polaczenie)
        if archiwizuj_po_zatwierdzeniu and self.stary_plik_sesji and self.stary_plik_sesji.exists():
            self._archiwizuj_json(self.stary_plik_sesji)

    def _migruj_treningi(self, polaczenie: sqlite3.Connection) -> bool:
        zmigrowano_json = False
        zaimportowane: set[tuple[Any, ...]] = set()

        def sygnatura(data: str, cwiczenie: Exercise) -> tuple[Any, ...]:
            if hasattr(cwiczenie, "sets"):
                szczegoly = ("strength", cwiczenie.name, cwiczenie.sets, cwiczenie.reps, cwiczenie.load_kg)
            else:
                szczegoly = (
                    "cardio", cwiczenie.name, cwiczenie.duration_min,
                    cwiczenie.distance_km, cwiczenie.heart_rate_bpm,
                )
            return (data, *szczegoly)
        if self.stary_plik_sesji and self.stary_plik_sesji.exists():
            surowe_sesje = json.loads(self.stary_plik_sesji.read_text(encoding="utf-8"))
            if not isinstance(surowe_sesje, list):
                raise ValueError("Plik sesji musi zawierać listę sesji.")
            for surowa_sesja in surowe_sesje:
                data_sesji_iso = str(surowa_sesja.get("date", "")).strip()
                if not data_sesji_iso:
                    raise ValueError("Migrowana sesja nie ma daty.")
                stare_id_sesji = int(surowa_sesja.get("session_id") or 0)
                if stare_id_sesji and not polaczenie.execute(
                    "SELECT 1 FROM workout_sessions WHERE session_id = ?",
                    (stare_id_sesji,),
                ).fetchone():
                    polaczenie.execute(
                        """INSERT INTO workout_sessions (session_id, date_str, athlete_name)
                           VALUES (?, ?, ?)""",
                        (stare_id_sesji, data_sesji_iso, "Użytkownik"),
                    )
                    session_id = stare_id_sesji
                else:
                    kursor = polaczenie.execute(
                        "INSERT INTO workout_sessions (date_str, athlete_name) VALUES (?, ?)",
                        (data_sesji_iso, "Użytkownik"),
                    )
                    session_id = int(kursor.lastrowid)
                for surowe_cwiczenie in surowa_sesja.get("exercises", []):
                    dane = dict(surowe_cwiczenie)
                    dane.setdefault("type", "strength")
                    if "load_kg" not in dane and "weight_kg" in dane:
                        dane["load_kg"] = dane["weight_kg"]
                    cwiczenie = Exercise.from_dict(dane)
                    klucz = sygnatura(data_sesji_iso, cwiczenie)
                    if klucz not in zaimportowane:
                        self._wstaw_cwiczenie(polaczenie, session_id, cwiczenie, zachowaj_id=False)
                        zaimportowane.add(klucz)
            zmigrowano_json = True
        if self.stary_plik_treningow and self.stary_plik_treningow.exists():
            with self.stary_plik_treningow.open("r", encoding="utf-8-sig", newline="") as strumien:
                for indeks, wiersz in enumerate(csv.DictReader(strumien), 1):
                    if not wiersz.get("cwiczenie"):
                        continue
                    data_sesji_iso = wiersz.get("data", "")
                    session_id = self._id_sesji(polaczenie, data_sesji_iso, "Użytkownik")
                    cwiczenie = StrengthExercise(
                        int(wiersz.get("id") or indeks), wiersz["cwiczenie"], int(wiersz["serie"]),
                        int(wiersz["powtorzenia"]), float(wiersz["ciezar_kg"]),
                    )
                    klucz = sygnatura(data_sesji_iso, cwiczenie)
                    if klucz not in zaimportowane:
                        self._wstaw_cwiczenie(polaczenie, session_id, cwiczenie, zachowaj_id=False)
                        zaimportowane.add(klucz)
        return zmigrowano_json

    def _migruj_posilki_i_profil(self, polaczenie: sqlite3.Connection) -> None:
        for nazwa_migracji, zrodlo in (
            ("nutrition_csv", self.stary_plik_posilkow),
            ("profile_json", self.stary_plik_profilu),
        ):
            if zrodlo is None or not zrodlo.exists():
                continue
            if polaczenie.execute(
                "SELECT 1 FROM schema_migrations WHERE migration_name = ?", (nazwa_migracji,)
            ).fetchone():
                continue
            if nazwa_migracji == "nutrition_csv":
                with zrodlo.open("r", encoding="utf-8-sig", newline="") as strumien:
                    for wiersz in csv.DictReader(strumien):
                        if wiersz.get("nazwa_posilku"):
                            polaczenie.execute(
                                """INSERT INTO nutrition_entries
                                   (entry_date, meal_name, protein_g, carbohydrates_g, fat_g, kcal)
                                   VALUES (?, ?, ?, ?, ?, ?)""",
                                (
                                    wiersz.get("data", ""), wiersz["nazwa_posilku"],
                                    float(wiersz["bialko_g"]), float(wiersz["weglowodany_g"]),
                                    float(wiersz["tluszcz_g"]), float(wiersz["kcal"]),
                                ),
                            )
            else:
                profil = json.loads(zrodlo.read_text(encoding="utf-8"))
                cele = profil.get("cele_dzienne", {})
                polaczenie.execute(
                    """UPDATE user_profile SET calories_goal = ?, protein_goal = ?,
                       carbohydrates_goal = ?, fat_goal = ? WHERE profile_id = 1""",
                    (
                        float(cele.get("kalorie", 2500)), float(cele.get("bialko", 160)),
                        float(cele.get("weglowodany", 250)), float(cele.get("tluszcze", 70)),
                    ),
                )
            polaczenie.execute(
                "INSERT INTO schema_migrations (migration_name) VALUES (?)", (nazwa_migracji,)
            )

    @staticmethod
    def _archiwizuj_json(zrodlo: Path) -> Path:
        cel_archiwum = zrodlo.with_suffix(zrodlo.suffix + ".bak")
        if cel_archiwum.exists():
            znacznik_czasu = datetime.now().strftime("%Y%m%d_%H%M%S")
            cel_archiwum = zrodlo.with_suffix(zrodlo.suffix + f".{znacznik_czasu}.bak")
            licznik = 1
            while cel_archiwum.exists():
                cel_archiwum = zrodlo.with_suffix(
                    zrodlo.suffix + f".{znacznik_czasu}_{licznik}.bak"
                )
                licznik += 1
        shutil.move(str(zrodlo), str(cel_archiwum))
        return cel_archiwum

    @staticmethod
    def _id_sesji(
        polaczenie: sqlite3.Connection, date_str: str, nazwa_zawodnika: str
    ) -> int:
        wiersz = polaczenie.execute(
            "SELECT session_id FROM workout_sessions WHERE date_str = ?", (date_str,)
        ).fetchone()
        if wiersz:
            return int(wiersz["session_id"])
        kursor = polaczenie.execute(
            "INSERT INTO workout_sessions (date_str, athlete_name) VALUES (?, ?)",
            (date_str, nazwa_zawodnika),
        )
        return int(kursor.lastrowid)

    @staticmethod
    def _wstaw_cwiczenie(
        polaczenie: sqlite3.Connection,
        session_id: int,
        cwiczenie: Exercise,
        *,
        zachowaj_id: bool = True,
    ) -> None:
        dane = cwiczenie.to_dict()
        wartosci = (
            session_id, dane["type"], dane["name"], dane.get("sets"),
            dane.get("reps"), dane.get("load_kg"), dane.get("duration_min"),
            dane.get("distance_km"), dane.get("heart_rate_bpm"),
        )
        if zachowaj_id:
            polaczenie.execute(
                """INSERT INTO exercises
                   (exercise_id, session_id, exercise_type, name, sets, reps, weight_kg,
                    duration_min, distance_km, heart_rate_bpm)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (cwiczenie.exercise_id, *wartosci),
            )
        else:
            polaczenie.execute(
                """INSERT INTO exercises
                   (session_id, exercise_type, name, sets, reps, weight_kg,
                    duration_min, distance_km, heart_rate_bpm)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                wartosci,
            )


class RepozytoriumSesjiTreningowych:
    def __init__(self, baza: BazaDanych | str | os.PathLike[str] = DOMYSLNA_SCIEZKA_BAZY) -> None:
        if hasattr(baza, "polaczenie"):
            self.baza = baza
        elif str(baza) == str(DOMYSLNA_SCIEZKA_BAZY):
            self.baza = BazaDanych(baza)
        else:
            self.baza = BazaDanych(
                baza, stary_plik_treningow=None, stary_plik_posilkow=None,
                stary_plik_profilu=None, stary_plik_sesji=None,
            )
        self.baza.inicjalizuj()

    def zapisz(self, sesja: WorkoutSessionManager, nazwa_zawodnika: str = "Użytkownik") -> int:

        with self.baza.polaczenie() as polaczenie:
            wiersz = polaczenie.execute(
                "SELECT session_id FROM workout_sessions WHERE session_id = ?",
                (sesja.session_id,),
            ).fetchone()
            if wiersz:
                polaczenie.execute(
                    "UPDATE workout_sessions SET date_str = ?, athlete_name = ? WHERE session_id = ?",
                    (sesja.date, nazwa_zawodnika, sesja.session_id),
                )
                polaczenie.execute(
                    "DELETE FROM exercises WHERE session_id = ?", (sesja.session_id,)
                )
                session_id = sesja.session_id
            else:
                wiersz_dla_daty = polaczenie.execute(
                    "SELECT session_id FROM workout_sessions WHERE date_str = ?",
                    (sesja.date,),
                ).fetchone()
                if wiersz_dla_daty:
                    session_id = int(wiersz_dla_daty["session_id"])
                else:
                    polaczenie.execute(
                        """INSERT INTO workout_sessions (session_id, date_str, athlete_name)
                           VALUES (?, ?, ?)""",
                        (sesja.session_id, sesja.date, nazwa_zawodnika),
                    )
                    session_id = sesja.session_id
            for cwiczenie in sesja.exercises:
                BazaDanych._wstaw_cwiczenie(polaczenie, session_id, cwiczenie)
            return session_id

    def dodaj_cwiczenie(
        self, cwiczenie: Exercise, data_sesji: str, nazwa_zawodnika: str = "Użytkownik"
    ) -> WorkoutSessionManager:
        with self.baza.polaczenie() as polaczenie:
            session_id = BazaDanych._id_sesji(polaczenie, data_sesji, nazwa_zawodnika)
            BazaDanych._wstaw_cwiczenie(polaczenie, session_id, cwiczenie)
        return next(
            sesja for sesja in self.pobierz_wszystkie()
            if sesja.session_id == session_id
        )

    def pobierz_wszystkie(self) -> list[WorkoutSessionManager]:
        with self.baza.polaczenie() as polaczenie:
            sesje_nadrzedne = polaczenie.execute(
                "SELECT session_id, date_str FROM workout_sessions ORDER BY date_str"
            ).fetchall()
            sesje = []
            for rodzic in sesje_nadrzedne:
                wiersze = polaczenie.execute(
                    """SELECT exercise_id, exercise_type AS type, name, sets, reps,
                       weight_kg AS load_kg, duration_min, distance_km, heart_rate_bpm
                       FROM exercises WHERE session_id = ? ORDER BY exercise_id""",
                    (rodzic["session_id"],),
                ).fetchall()
                cwiczenia = [Exercise.from_dict(dict(wiersz)) for wiersz in wiersze]
                sesje.append(WorkoutSessionManager(
                    int(rodzic["session_id"]), rodzic["date_str"], cwiczenia
                ))
            return sesje

    def pobierz_treningi(self) -> list[dict[str, Any]]:
        with self.baza.polaczenie() as polaczenie:
            wiersze = polaczenie.execute(
                """SELECT e.exercise_id, s.date_str, e.name, e.sets, e.reps, e.weight_kg
                   FROM exercises AS e JOIN workout_sessions AS s
                     ON s.session_id = e.session_id
                   WHERE e.exercise_type = ? ORDER BY e.exercise_id""",
                ("strength",),
            ).fetchall()
            return [
                {
                    "id": wiersz["exercise_id"], "data": wiersz["date_str"],
                    "cwiczenie": wiersz["name"], "serie": wiersz["sets"],
                    "powtorzenia": wiersz["reps"], "ciezar_kg": wiersz["weight_kg"],
                }
                for wiersz in wiersze
            ]

    def wyszukaj_cwiczenia(
        self,
        fraza: str = "",
        data_od: str | None = None,
        data_do: str | None = None,
        minimalny_ciezar: float = 0.0,
        sortuj_po: str = "data",
        kierunek: str = "ASC",
    ) -> list[dict[str, Any]]:
        kolumny_sortowania = {
            "data": "s.date_str", "nazwa": "e.name", "ciezar": "e.weight_kg",
        }
        if sortuj_po not in kolumny_sortowania:
            raise ValueError(f"Niedozwolona kolumna sortowania: {sortuj_po}")
        kierunek_sql = kierunek.upper()
        if kierunek_sql not in {"ASC", "DESC"}:
            raise ValueError(f"Niedozwolony kierunek sortowania: {kierunek}")
        warunki = ["e.exercise_type = ?", "e.name LIKE ?", "e.weight_kg >= ?"]
        parametry: list[Any] = ["strength", f"%{fraza}%", float(minimalny_ciezar)]
        if data_od is not None:
            warunki.append("s.date_str >= ?")
            parametry.append(data_od)
        if data_do is not None:
            warunki.append("s.date_str <= ?")
            parametry.append(data_do)
        sql = f"""SELECT e.exercise_id AS id, s.date_str AS data, e.name AS cwiczenie,
                         e.sets AS serie, e.reps AS powtorzenia,
                         e.weight_kg AS ciezar_kg
                  FROM exercises AS e
                  INNER JOIN workout_sessions AS s ON s.session_id = e.session_id
                  WHERE {' AND '.join(warunki)}
                  ORDER BY {kolumny_sortowania[sortuj_po]} {kierunek_sql}, e.exercise_id"""
        with self.baza.polaczenie() as polaczenie:
            return [dict(wiersz) for wiersz in polaczenie.execute(sql, parametry).fetchall()]

    def raport_tonazu_sesji(self, minimalny_tonaz: float = 0.0) -> list[dict[str, Any]]:
        sql = """SELECT s.session_id, s.date_str AS data,
                         COUNT(e.exercise_id) AS liczba_cwiczen,
                         COALESCE(SUM(e.sets * e.reps * e.weight_kg), 0) AS tonaz_kg
                  FROM workout_sessions AS s
                  LEFT JOIN exercises AS e
                    ON e.session_id = s.session_id AND e.exercise_type = ?
                  GROUP BY s.session_id, s.date_str
                  HAVING COALESCE(SUM(e.sets * e.reps * e.weight_kg), 0) >= ?
                  ORDER BY tonaz_kg DESC, s.date_str ASC"""
        with self.baza.polaczenie() as polaczenie:
            return [dict(wiersz) for wiersz in polaczenie.execute(
                sql, ("strength", float(minimalny_tonaz))
            ).fetchall()]

    def pobierz_treningi_z_tonazem_powyzej_2000kg(self) -> list[dict[str, Any]]:
        """Zwraca sesje, których tonaż ćwiczeń siłowych przekracza 2000 kg."""
        sql = """SELECT s.session_id, s.date_str AS data,
                         COUNT(e.exercise_id) AS liczba_cwiczen,
                         COALESCE(SUM(e.sets * e.reps * e.weight_kg), 0) AS tonaz_kg
                  FROM workout_sessions AS s
                  LEFT JOIN exercises AS e
                    ON e.session_id = s.session_id AND e.exercise_type = ?
                  GROUP BY s.session_id, s.date_str
                  HAVING COALESCE(SUM(e.sets * e.reps * e.weight_kg), 0) > ?
                  ORDER BY tonaz_kg DESC, s.date_str ASC"""
        with self.baza.polaczenie() as polaczenie:
            return [dict(wiersz) for wiersz in polaczenie.execute(
                sql, ("strength", 2000)
            ).fetchall()]

    def pobierz_zestawy_z_wiecej_niz_3_cwiczeniami(self) -> list[dict[str, Any]]:
        """Zwraca sesje treningowe zawierające więcej niż trzy ćwiczenia."""
        sql = """SELECT s.session_id, s.date_str AS data,
                         COUNT(e.exercise_id) AS liczba_cwiczen,
                         COALESCE(SUM(CASE WHEN e.exercise_type = 'strength'
                                           THEN e.sets * e.reps * e.weight_kg
                                           ELSE 0 END), 0) AS tonaz_kg
                  FROM workout_sessions AS s
                  LEFT JOIN exercises AS e ON e.session_id = s.session_id
                  GROUP BY s.session_id, s.date_str
                  HAVING COUNT(e.exercise_id) > ?
                  ORDER BY liczba_cwiczen DESC, s.date_str ASC"""
        with self.baza.polaczenie() as polaczenie:
            return [dict(wiersz) for wiersz in polaczenie.execute(sql, (3,)).fetchall()]

    def nastepne_id_cwiczenia(self) -> int:
        with self.baza.polaczenie() as polaczenie:
            return int(polaczenie.execute(
                "SELECT COALESCE(MAX(exercise_id), 0) + 1 FROM exercises"
            ).fetchone()[0])

    def usun(self, session_id: int) -> bool:
        with self.baza.polaczenie() as polaczenie:
            kursor = polaczenie.execute(
                "DELETE FROM workout_sessions WHERE session_id = ?", (session_id,)
            )
            return kursor.rowcount > 0


def inicjalizuj_baze(sciezka_bazy: str | os.PathLike[str] = DOMYSLNA_SCIEZKA_BAZY) -> None:
    BazaDanych(sciezka_bazy).inicjalizuj()


def zapisz_wpis_posilku(wpis: dict[str, Any]) -> None:
    baza = BazaDanych()
    baza.inicjalizuj()
    with baza.polaczenie() as polaczenie:
        polaczenie.execute(
            """INSERT INTO nutrition_entries
               (entry_date, meal_name, protein_g, carbohydrates_g, fat_g, kcal)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                wpis["data"], wpis["nazwa_posilku"], wpis["bialko_g"],
                wpis["weglowodany_g"], wpis["tluszcz_g"], wpis["kcal"],
            ),
        )


def pobierz_wpisy_posilkow() -> list[dict[str, Any]]:
    baza = BazaDanych()
    baza.inicjalizuj()
    with baza.polaczenie() as polaczenie:
        wiersze = polaczenie.execute(
            """SELECT nutrition_id, entry_date, meal_name, protein_g, carbohydrates_g,
               fat_g, kcal FROM nutrition_entries ORDER BY nutrition_id"""
        ).fetchall()
        return [
            {
                "id": wiersz["nutrition_id"], "data": wiersz["entry_date"],
                "nazwa_posilku": wiersz["meal_name"], "bialko_g": wiersz["protein_g"],
                "weglowodany_g": wiersz["carbohydrates_g"],
                "tluszcz_g": wiersz["fat_g"], "kcal": wiersz["kcal"],
            }
            for wiersz in wiersze
        ]


def pobierz_profil_uzytkownika() -> dict[str, Any]:
    baza = BazaDanych()
    baza.inicjalizuj()
    with baza.polaczenie() as polaczenie:
        wiersz = polaczenie.execute(
            """SELECT calories_goal, protein_goal, carbohydrates_goal, fat_goal
               FROM user_profile WHERE profile_id = ?""", (1,)
        ).fetchone()
    return {"cele_dzienne": {
        "kalorie": wiersz["calories_goal"], "bialko": wiersz["protein_goal"],
        "weglowodany": wiersz["carbohydrates_goal"], "tluszcze": wiersz["fat_goal"],
    }}
