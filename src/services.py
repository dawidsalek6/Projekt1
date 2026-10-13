import time
from data import TRENINGI, MAKROSKLADNIKI, PRZERWY, AKTYWNY_STOPER
from validators import getIntInput, getFloatInput, getNonEmptyString


def dodaj_wpis_treningowy():
    print("\n--- REJESTRACJA TRENINGU SIŁOWEGO ---")
    cwiczenie = getNonEmptyString("Nazwa ćwiczenia: ")
    serie = getIntInput("Liczba serii: ", min_val=1, max_val=100)
    powtorzenia = getIntInput("Liczba powtórzeń w serii: ", min_val=1, max_val=200)
    ciezar = getFloatInput("Ciężar (kg): ", min_val=0.0, max_val=1000.0)

    nastepne_id = max([t["id"] for t in TRENINGI], default=0) + 1
    nowy_wpis = {
        "id": nastepne_id,
        "cwiczenie": cwiczenie,
        "serie": serie,
        "powtorzenia": powtorzenia,
        "ciezar_kg": ciezar
    }
    TRENINGI.append(nowy_wpis)
    print(f" Zapisano trening: {cwiczenie} ({serie}x{powtorzenia}, {ciezar} kg)")


def dodaj_wpis_makroskladnikow():
    print("\n--- REJESTRACJA MAKROSKŁADNIKÓW ---")
    nazwa_posilku = getNonEmptyString("Nazwa posiłku: ")
    bialko = getFloatInput("Białko (g): ", min_val=0.0, max_val=1000.0)
    weglowodany = getFloatInput("Węglowodany (g): ", min_val=0.0, max_val=1000.0)
    tluszcz = getFloatInput("Tłuszcze (g): ", min_val=0.0, max_val=1000.0)

    kcal = round((bialko * 4) + (weglowodany * 4) + (tluszcz * 9), 1)

    nastepne_id = max([m["id"] for m in MAKROSKLADNIKI], default=0) + 1
    nowy_wpis = {
        "id": nastepne_id,
        "nazwa_posilku": nazwa_posilku,
        "bialko_g": bialko,
        "weglowodany_g": weglowodany,
        "tluszcz_g": tluszcz,
        "kcal": kcal
    }
    MAKROSKLADNIKI.append(nowy_wpis)
    print(f" Zapisano posiłek: {nazwa_posilku} ({kcal} kcal)")


def uruchom_stoper_przerwy():
    if AKTYWNY_STOPER["czy_dziala"]:
        print(" Stoper już działa!")
        return

    AKTYWNY_STOPER["czy_dziala"] = True
    AKTYWNY_STOPER["czas_startu"] = time.time()
    print(" Stoper przerw został URUCHOMIONY!")


def zakoncz_i_zapisz_stoper_przerwy():
    if not AKTYWNY_STOPER["czy_dziala"]:
        print(" Stoper nie jest obecnie uruchomiony!")
        return

    uplyniety_czas = int(time.time() - AKTYWNY_STOPER["czas_startu"])
    AKTYWNY_STOPER["czy_dziala"] = False
    AKTYWNY_STOPER["czas_startu"] = None

    etykieta = getNonEmptyString("Opis przerwy ")
    nastepne_id = max([p["id"] for p in PRZERWY], default=0) + 1

    PRZERWY.append({
        "id": nastepne_id,
        "etykieta": etykieta,
        "czas_sekundy": uplyniety_czas
    })
    print(f" Stoper ZAKOŃCZONY. Czas przerwy: {uplyniety_czas} s ({uplyniety_czas // 60}m {uplyniety_czas % 60}s).")


def przerwij_stoper_przerwy():
    if not AKTYWNY_STOPER["czy_dziala"]:
        print(" Brak aktywnego stopera do przerwania.")
        return

    AKTYWNY_STOPER["czy_dziala"] = False
    AKTYWNY_STOPER["czas_startu"] = None
    print(" Stoper został PRZERWANY i nie został zapisany.")


def wyswietl_podsumowanie_dnia():
    print("\n" + "=" * 58)
    print("                 PODSUMOWANIE DNIA")
    print("=" * 58)

    # Zarejestrowane treningi
    print("\n  ZAREJESTROWANY TRENING SIŁOWY:")
    if not TRENINGI:
        print("   (Brak zarejestrowanych ćwiczeń)")
    else:
        print(f"   {'ID':<4} | {'Ćwiczenie':<20} | {'Serie':<6} | {'Powt.':<6} | {'Ciężar':<8}")
        print("   " + "-" * 52)
        for t in TRENINGI:
            print(f"   {t['id']:<4} | {t['cwiczenie']:<20} | {t['serie']:<6} | {t['powtorzenia']:<6} | {t['ciezar_kg']:<6} kg")

    # Zarejestrowane posiłki
    print("\n ZAREJESTROWANE MAKROSKŁADNIKI I POSIŁKI:")
    if not MAKROSKLADNIKI:
        print("   (Brak zarejestrowanych posiłków)")
    else:
        suma_bialka = sum(m["bialko_g"] for m in MAKROSKLADNIKI)
        suma_wegli = sum(m["weglowodany_g"] for m in MAKROSKLADNIKI)
        suma_tluszczu = sum(m["tluszcz_g"] for m in MAKROSKLADNIKI)
        suma_kcal = sum(m["kcal"] for m in MAKROSKLADNIKI)

        print(f"   {'ID':<4} | {'Posiłek':<18} | {'Białko':<8} | {'Węgle':<8} | {'Tłuszcz':<8} | {'Kcal':<8}")
        print("   " + "-" * 64)
        for m in MAKROSKLADNIKI:
            print(f"   {m['id']:<4} | {m['nazwa_posilku']:<18} | {m['bialko_g']:<8.1f} | {m['weglowodany_g']:<8.1f} | {m['tluszcz_g']:<8.1f} | {m['kcal']:<8.1f}")
        print("   " + "-" * 64)
        print(f"   SUMA: Białko: {suma_bialka:.1f}g | Węglowodany: {suma_wegli:.1f}g | Tłuszcze: {suma_tluszczu:.1f}g | Kalorie: {suma_kcal:.1f} kcal")

    # Zarejestrowane przerwy
    print("\n  CZAS PRZERW (STOPER):")
    if not PRZERWY:
        print("   (Brak zarejestrowanych przerw)")
    else:
        suma_sekund = sum(p["czas_sekundy"] for p in PRZERWY)
        for p in PRZERWY:
            minuty = p['czas_sekundy'] // 60
            sekundy = p['czas_sekundy'] % 60
            print(f"   - {p['etykieta']}: {p['czas_sekundy']}s ({minuty}m {sekundy}s)")

        suma_minut = suma_sekund // 60
        reszta_sekund = suma_sekund % 60
        print("   " + "-" * 42)
        print(f"   SUMARYCZNY CZAS PRZERW: {suma_sekund} sekund ({suma_minut} min {reszta_sekund} sek)")
    print("=" * 58 + "\n")