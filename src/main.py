from validators import getIntInput, getFloatInput, getNonEmptyString
from services import (
    dodaj_wpis_treningowy,
    dodaj_wpis_makroskladnikow,
    uruchom_stoper_przerwy,
    przerwij_stoper_przerwy,
    zakoncz_i_zapisz_stoper_przerwy,
    wyswietl_podsumowanie_dnia
)


def print_menu():
    print("\n" + "=" * 50)
    print("     SYSTEM ZARZĄDZANIA TRENINGIEM I DIETĄ     ")
    print("=" * 50)
    print("1. Zarejestruj ćwiczenie siłowe")
    print("2. Zapisz makroskładniki (posiłek)")
    print("3. Uruchom stoper przerwy")
    print("4. Przerwij (anuluj) stoper")
    print("5. Zakończ i zapisz stoper przerwy")
    print("6. Wyświetl podsumowanie dnia")
    print("0. Wyjście z programu")
    print("-" * 50)


def handle_menu_choice(choice: int) -> bool:
    match choice:
        case 1:
            dodaj_wpis_treningowy()
        case 2:
            dodaj_wpis_makroskladnikow()
        case 3:
            uruchom_stoper_przerwy()
        case 4:
            przerwij_stoper_przerwy()
        case 5:
            zakoncz_i_zapisz_stoper_przerwy()
        case 6:
            wyswietl_podsumowanie_dnia()
        case 0:
            print("Dziękujemy za skorzystanie z programu! Do zobaczenia.")
            return False
        case _:
            print("Nieprawidłowa opcja! Wybierz cyfrę z zakresu 0-6.")
    return True


def main():
    running = True
    while running:
        print_menu()
        user_choice = getIntInput("Wybierz opcję [0-6]: ")
        running = handle_menu_choice(user_choice)


if __name__ == "__main__":
    main()