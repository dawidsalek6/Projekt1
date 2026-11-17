from typing import Any

from database import (
    DOMYSLNA_SCIEZKA_BAZY,
    DOMYSLNY_PLIK_POSILKOW,
    DOMYSLNY_PLIK_PROFILU,
    DOMYSLNY_PLIK_SESJI,
    DOMYSLNY_PLIK_TRENINGOW,
    BazaDanych,
    RepozytoriumSesjiTreningowych,
    pobierz_polaczenie,
    pobierz_wpisy_posilkow,
    pobierz_profil_uzytkownika,
    inicjalizuj_baze,
    zapisz_wpis_posilku,
)
from models import StrengthExercise

trening = str(DOMYSLNY_PLIK_TRENINGOW)
makro = str(DOMYSLNY_PLIK_POSILKOW)
profil = str(DOMYSLNY_PLIK_PROFILU)
sesje_treningowe = str(DOMYSLNY_PLIK_SESJI)


def zapisz_cwiczenie(cwiczenie: dict[str, Any]) -> None:
    repository = RepozytoriumSesjiTreningowych()
    repository.dodaj_cwiczenie(
        StrengthExercise(
            int(cwiczenie["id"]), cwiczenie["cwiczenie"], int(cwiczenie["serie"]),
            int(cwiczenie["powtorzenia"]), float(cwiczenie["ciezar_kg"]),
        ),
        str(cwiczenie["data"]),
    )


def zapisz_posilek(posilek: dict[str, Any]) -> None:
    zapisz_wpis_posilku(posilek)


def wczytaj_treningi() -> list[dict[str, Any]]:
    return RepozytoriumSesjiTreningowych().pobierz_treningi()


def wczytaj_posilki() -> list[dict[str, Any]]:
    return pobierz_wpisy_posilkow()


def wczytaj_profil_json() -> dict[str, Any]:
    return pobierz_profil_uzytkownika()
