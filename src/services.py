
import time
from datetime import date, datetime, timedelta

from data import TRENINGI, MAKROSKLADNIKI, PRZERWY, AKTYWNY_STOPER
from validators import getIntInput, getFloatInput, getNonEmptyString
from storage import (
    zapisz_cwiczenie,
    zapisz_posilek,
    wczytaj_treningi,
    wczytaj_posilki,
    wczytaj_profil_json
)


def pobierz_date():
    """Pobiera datę od użytkownika i sprawdza jej poprawność."""
    while True:
        tekst = input("Podaj datę (RRRR-MM-DD): ").strip()

        try:
            return datetime.strptime(tekst, "%Y-%m-%d").date()
        except ValueError:
            print("Niepoprawna data. Wpisz ją w formacie RRRR-MM-DD, np. 2026-10-27.")


def dodaj_wpis_treningowy():
    print("\n--- REJESTRACJA TRENINGU SIŁOWEGO ---")

    data_wpisu = pobierz_date().isoformat()
    cwiczenie = getNonEmptyString("Nazwa ćwiczenia: ").capitalize()
    serie = getIntInput("Liczba serii: ", min_val=1, max_val=100)
    powtorzenia = getIntInput(
        "Liczba powtórzeń w serii: ", min_val=1, max_val=200
    )
    ciezar = getFloatInput("Ciężar (kg): ", min_val=0.0, max_val=1000.0)

    objetosc = serie * powtorzenia * ciezar

    treningi = wczytaj_treningi()
    nastepne_id = max([t["id"] for t in treningi], default=0) + 1

    nowy_wpis = {
        "id": nastepne_id,
        "data": data_wpisu,
        "cwiczenie": cwiczenie,
        "serie": serie,
        "powtorzenia": powtorzenia,
        "ciezar_kg": ciezar
    }

    TRENINGI.append(nowy_wpis)
    zapisz_cwiczenie(nowy_wpis)

    print(
        f"Zapisano trening: {cwiczenie} | data: {data_wpisu} | "
        f"{serie}x{powtorzenia}, {ciezar} kg | "
        f"objętość: {objetosc:.1f} kg"
    )


def dodaj_wpis_makroskladnikow():
    print("\n--- REJESTRACJA MAKROSKŁADNIKÓW ---")

    data_wpisu = pobierz_date().isoformat()
    nazwa_posilku = getNonEmptyString("Nazwa posiłku: ").capitalize()
    bialko = getFloatInput("Białko (g): ", min_val=0.0, max_val=1000.0)
    weglowodany = getFloatInput(
        "Węglowodany (g): ", min_val=0.0, max_val=1000.0
    )
    tluszcz = getFloatInput("Tłuszcze (g): ", min_val=0.0, max_val=1000.0)

    kcal = round(bialko * 4 + weglowodany * 4 + tluszcz * 9, 1)

    posilki = wczytaj_posilki()
    nastepne_id = max([m["id"] for m in posilki], default=0) + 1

    nowy_wpis = {
        "id": nastepne_id,
        "data": data_wpisu,
        "nazwa_posilku": nazwa_posilku,
        "bialko_g": bialko,
        "weglowodany_g": weglowodany,
        "tluszcz_g": tluszcz,
        "kcal": kcal
    }

    MAKROSKLADNIKI.append(nowy_wpis)
    zapisz_posilek(nowy_wpis)

    print(
        f"Zapisano posiłek: {nazwa_posilku} | "
        f"data: {data_wpisu} | {kcal} kcal"
    )


def uruchom_stoper_przerwy():
    if AKTYWNY_STOPER["czy_dziala"]:
        print("Stoper już działa!")
        return

    AKTYWNY_STOPER["czy_dziala"] = True
    AKTYWNY_STOPER["czas_startu"] = time.time()
    print("Stoper przerw został URUCHOMIONY!")


def zakoncz_i_zapisz_stoper_przerwy():
    if not AKTYWNY_STOPER["czy_dziala"]:
        print("Stoper nie jest obecnie uruchomiony!")
        return

    uplyniety_czas = int(
        time.time() - AKTYWNY_STOPER["czas_startu"]
    )

    AKTYWNY_STOPER["czy_dziala"] = False
    AKTYWNY_STOPER["czas_startu"] = None

    etykieta = getNonEmptyString("Opis przerwy: ")
    nastepne_id = max([p["id"] for p in PRZERWY], default=0) + 1

    PRZERWY.append({
        "id": nastepne_id,
        "etykieta": etykieta,
        "czas_sekundy": uplyniety_czas
    })

    print(
        f"Stoper zakończony. Czas przerwy: {uplyniety_czas} s "
        f"({uplyniety_czas // 60} min {uplyniety_czas % 60} s)."
    )


def przerwij_stoper_przerwy():
    if not AKTYWNY_STOPER["czy_dziala"]:
        print("Brak aktywnego stopera do przerwania.")
        return

    AKTYWNY_STOPER["czy_dziala"] = False
    AKTYWNY_STOPER["czas_startu"] = None
    print("Stoper został przerwany i nie został zapisany.")


def wyswietl_podsumowanie_dnia():
    data_wybrana = pobierz_date().isoformat()

    treningi = [
        t for t in wczytaj_treningi()
        if t.get("data") == data_wybrana
    ]
    posilki = [
        m for m in wczytaj_posilki()
        if m.get("data") == data_wybrana
    ]

    profil = wczytaj_profil_json()
    cele = profil.get("cele_dzienne", {
        "kalorie": 2500,
        "bialko": 160,
        "weglowodany": 250,
        "tluszcze": 70
    })

    print("\n" + "=" * 65)
    print("                 PODSUMOWANIE DNIA")
    print(f"                    {data_wybrana}")
    print("=" * 65)

    print("\nTRENINGI:")
    if not treningi:
        print("   Brak treningów w wybranym dniu.")
    else:
        suma_objetosci = 0

        for t in treningi:
            objetosc = t["serie"] * t["powtorzenia"] * t["ciezar_kg"]
            suma_objetosci += objetosc
            print(
                f"   {t['cwiczenie']} | {t['serie']}x{t['powtorzenia']} | "
                f"{t['ciezar_kg']} kg | objętość: {objetosc:.1f} kg"
            )

        print(f"   Łączna objętość: {suma_objetosci:.1f} kg")

    suma_bialka = sum(m["bialko_g"] for m in posilki)
    suma_wegli = sum(m["weglowodany_g"] for m in posilki)
    suma_tluszczu = sum(m["tluszcz_g"] for m in posilki)
    suma_kcal = sum(m["kcal"] for m in posilki)

    print("\nPOSIŁKI:")
    if not posilki:
        print("   Brak posiłków w wybranym dniu.")
    else:
        for m in posilki:
            print(
                f"   {m['nazwa_posilku']} | "
                f"B: {m['bialko_g']:.1f} g | "
                f"W: {m['weglowodany_g']:.1f} g | "
                f"T: {m['tluszcz_g']:.1f} g | "
                f"{m['kcal']:.1f} kcal"
            )

    print("\nPODSUMOWANIE MAKROSKŁADNIKÓW:")
    print(f"   Białko: {suma_bialka:.1f} / {cele.get('bialko', 0)} g")
    print(f"   Węglowodany: {suma_wegli:.1f} / {cele.get('weglowodany', 0)} g")
    print(f"   Tłuszcze: {suma_tluszczu:.1f} / {cele.get('tluszcze', 0)} g")
    print(f"   Kalorie: {suma_kcal:.1f} / {cele.get('kalorie', 0)} kcal")

    print("\nCZAS PRZERW (STOPER):")
    if not PRZERWY:
        print("   Brak zarejestrowanych przerw w tej sesji.")
    else:
        suma_sekund = sum(p["czas_sekundy"] for p in PRZERWY)

        for p in PRZERWY:
            print(
                f"   {p['etykieta']}: "
                f"{p['czas_sekundy'] // 60} min "
                f"{p['czas_sekundy'] % 60} sek"
            )

        print(f"   Łączny czas przerw: {suma_sekund} sekund")

    print("=" * 65 + "\n")


def wyswietl_podsumowanie_tygodnia():
    print("\n--- PODSUMOWANIE TYGODNIA ---")
    wybrana_data = pobierz_date()

    poczatek = wybrana_data - timedelta(days=wybrana_data.weekday())
    koniec = poczatek + timedelta(days=6)

    def w_okresie(wpis):
        try:
            data_wpisu = date.fromisoformat(wpis.get("data", ""))
            return poczatek <= data_wpisu <= koniec
        except (ValueError, TypeError):
            return False

    treningi = [
        t for t in wczytaj_treningi() if w_okresie(t)
    ]
    posilki = [
        m for m in wczytaj_posilki() if w_okresie(m)
    ]

    suma_objetosci = sum(
        t["serie"] * t["powtorzenia"] * t["ciezar_kg"]
        for t in treningi
    )
    suma_bialka = sum(m["bialko_g"] for m in posilki)
    suma_wegli = sum(m["weglowodany_g"] for m in posilki)
    suma_tluszczu = sum(m["tluszcz_g"] for m in posilki)
    suma_kcal = sum(m["kcal"] for m in posilki)

    dni_treningowe = len({
        t["data"] for t in treningi if t.get("data")
    })

    print("\n" + "=" * 65)
    print("                 PODSUMOWANIE TYGODNIA")
    print("=" * 65)
    print(f"Wybrana data: {wybrana_data}")
    print(f"Okres: {poczatek} - {koniec}")

    print("\nTRENINGI:")
    if not treningi:
        print("   Brak treningów w tym tygodniu.")
    else:
        for t in treningi:
            objetosc = t["serie"] * t["powtorzenia"] * t["ciezar_kg"]
            print(
                f"   {t['data']} | {t['cwiczenie']} | "
                f"{t['serie']}x{t['powtorzenia']} | "
                f"{t['ciezar_kg']} kg | objętość: {objetosc:.1f} kg"
            )

    print(f"\nLiczba dni z treningiem: {dni_treningowe}")
    print(f"Łączna objętość treningowa: {suma_objetosci:.1f} kg")

    print("\nODŻYWIANIE:")
    print(f"   Liczba posiłków: {len(posilki)}")
    print(f"   Białko łącznie: {suma_bialka:.1f} g")
    print(f"   Węglowodany łącznie: {suma_wegli:.1f} g")
    print(f"   Tłuszcze łącznie: {suma_tluszczu:.1f} g")
    print(f"   Kalorie łącznie: {suma_kcal:.1f} kcal")

    print("\nŚREDNIA DZIENNA (7 DNI):")
    print(f"   Białko: {suma_bialka / 7:.1f} g")
    print(f"   Węglowodany: {suma_wegli / 7:.1f} g")
    print(f"   Tłuszcze: {suma_tluszczu / 7:.1f} g")
    print(f"   Kalorie: {suma_kcal / 7:.1f} kcal")

    print("=" * 65 + "\n")
