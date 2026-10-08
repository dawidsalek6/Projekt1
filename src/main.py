from validators import get_int_input


def print_menu():
    print("\n" + "=" * 50)
    print("   FITTRACK PRO – DZIENNIK TRENINGÓW I DIETY   ")
    print("=" * 50)
    print("1. Zarejestruj trening siłowy")
    print("2. Zapisz makroskładniki (dieta)")
    print("3. Uruchom stoper przerw")
    print("4. Podsumowanie dnia")
    print("5. Wyjście z programu")
    print("-" * 50)


def handle_menu_choice(choice: int) -> bool:
    match choice:
        case 1:
            print("\n Rejestracja treningu siłowego")
        case 2:
            print("\n Zapisywanie makroskładników")
        case 3:
            print("\n Stoper przerw")
        case 4:
            print("\n Podsumowanie dnia")
        case 5:
            print("\n Wyjście z programu FitTrack Pro")
            return False
        case _:
            print("\n Nieprawidłowa opcja! Wybierz cyfrę od 1 do 5")

    return True


def main():
    running = True
    while running:
        print_menu()
        user_choice = get_int_input("Wybierz opcję [1-5]: ")
        running = handle_menu_choice(user_choice)


if __name__ == "__main__":
    main()