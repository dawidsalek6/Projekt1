import time
from data import TRENINGI, MAKROSKLADNIKI, PRZERWY, AKTYWNY_STOPER
from validators import getIntInput, getFloatInput, getNonEmptyString
from storage import (
    zapisz_cwiczenie,
    zapisz_posilek,
    wczytaj_treningi,
    wczytaj_posilki,
    wczytaj_profil_json
)

def dodaj_wpis_treningowy():
    print("\n--- REJESTRACJA TRENINGU SIŁOWEGO ---")
    cwiczenie = getNonEmptyString("Nazwa ćwiczenia: ").capitalize()
    serie = getIntInput("Liczba serii: ", min_val=1, max_val=100)
    powtorzenia = getIntInput("Liczba powtórzeń w serii: ", min_val=1, max_val=200)
    ciezar = getFloatInput("Ciężar (kg): ", min_val=0.0, max_val=1000.0)
    suma_sumaryczna = (powtorzenia * ciezar) * serie

    treningi_z_plikow = wczytaj_treningi()
    nastepne_id = max([t["id"] for t in treningi_z_plikow], default=0) + 1

    nowy_wpis = {
        "id": nastepne_id,
        "cwiczenie": cwiczenie,
        "serie": serie,
        "powtorzenia": powtorzenia,
        "ciezar_kg": ciezar
    }
    TRENINGI.append(nowy_wpis)
    zapisz_cwiczenie(nowy_wpis)

    print(f" Zapisano trening: {cwiczenie} ({serie}x{powtorzenia}, {ciezar} kg, suma kilogramów: {suma_sumaryczna} kg)")


def dodaj_wpis_makroskladnikow():
    print("\n--- REJESTRACJA MAKROSKŁADNIKÓW ---")
    nazwa_posilku = getNonEmptyString("Nazwa posiłku: ").capitalize()
    bialko = getFloatInput("Białko (g): ", min_val=0.0, max_val=1000.0)
    weglowodany = getFloatInput("Węglowodany (g): ", min_val=0.0, max_val=1000.0)
    tluszcz = getFloatInput("Tłuszcze (g): ", min_val=0.0, max_val=1000.0)

    kcal = round((bialko * 4) + (weglowodany * 4) + (tluszcz * 9), 1)

    posilki_z_plikow = wczytaj_posilki()
    nastepne_id = max([m["id"] for m in posilki_z_plikow], default=0) + 1

    nowy_wpis = {
        "id": nastepne_id,
        "nazwa_posilku": nazwa_posilku,
        "bialko_g": bialko,
        "weglowodany_g": weglowodany,
        "tluszcz_g": tluszcz,
        "kcal": kcal
    }
    MAKROSKLADNIKI.append(nowy_wpis)
    zapisz_posilek(nowy_wpis)
    print(f"\nZapisano posiłek: {nazwa_posilku} ({kcal} kcal)")


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
    treningi_csv = wczytaj_treningi()
    posilki_csv = wczytaj_posilki()
    profil_json = wczytaj_profil_json()

    cele = profil_json.get("cele_dzienne", {
        "kalorie": 2500,
        "bialko": 160,
        "weglowodany": 250,
        "tluszcze": 70
    })

    print("\n" + "=" * 65)
    print("                 PODSUMOWANIE DNIA")
    print("=" * 65)

    print("\nZAREJESTROWANY TRENING SIŁOWY:")
    if not treningi_csv:
        print("   (Brak zarejestrowanych ćwiczeń)")
    else:
        print(f"   {'ID':<4} | {'Ćwiczenie':<20} | {'Serie':<6} | {'Powt.':<6} | {'Ciężar':<8}")
        print("   " + "-" * 58)
        for t in treningi_csv:
            print(f"   {t['id']:<4} | {t['cwiczenie']:<20} | {t['serie']:<6} | {t['powtorzenia']:<6} | {t['ciezar_kg']:<6} kg")
        print("   " + "-" * 58)

    print("\nZAREJESTROWANE POSIŁKI:")
    if not posilki_csv:
        print("   (Brak zarejestrowanych posiłków")
    else:
        suma_bialka = sum(m["bialko_g"] for m in posilki_csv)
        suma_wegli = sum(m["weglowodany_g"] for m in posilki_csv)
        suma_tluszczu = sum(m["tluszcz_g"] for m in posilki_csv)
        suma_kcal = sum(m["kcal"] for m in posilki_csv)

        print(f"   {'ID':<4} | {'Posiłek':<18} | {'Białko':<8} | {'Węgle':<8} | {'Tłuszcz':<8} | {'Kcal':<8}")
        print("   " + "-" * 66)
        for m in posilki_csv:
            print(f"   {m['id']:<4} | {m['nazwa_posilku']:<18} | {m['bialko_g']:<8.1f} | {m['weglowodany_g']:<8.1f} | {m['tluszcz_g']:<8.1f} | {m['kcal']:<8.1f}")
        print("   " + "-" * 66)
        print(f"   SPOŻYTO: Białko: {suma_bialka:.1f}g | Węgle: {suma_wegli:.1f}g | Tłuszcze: {suma_tluszczu:.1f}g | Kalorie: {suma_kcal:.1f} kcal")

        print("\nPORÓWNANIE Z CELEM:")
        print("   " + "-" * 69)

        target_kcal = cele.get("kalorie", 0)
        target_b = cele.get("bialko", 0)
        target_w = cele.get("weglowodany", 0)
        target_t = cele.get("tluszcze", 0)

        p_kcal = (suma_kcal / target_kcal * 100) if target_kcal else 0
        p_b = (suma_bialka / target_b * 100) if target_b else 0
        p_w = (suma_wegli / target_w * 100) if target_w else 0
        p_t = (suma_tluszczu / target_t * 100) if target_t else 0

        print(f"   Kalorie:     {suma_kcal:>6.1f} / {target_kcal:<5} kcal  ({p_kcal:>5.1f}%)  | Pozostało: {target_kcal - suma_kcal:>6.1f} kcal")
        print(f"   Białko:      {suma_bialka:>6.1f} / {target_b:<5} g     ({p_b:>5.1f}%)  | Pozostało: {target_b - suma_bialka:>6.1f} g")
        print(f"   Węglowodany: {suma_wegli:>6.1f} / {target_w:<5} g     ({p_w:>5.1f}%)  | Pozostało: {target_w - suma_wegli:>6.1f} g")
        print(f"   Tłuszcze:    {suma_tluszczu:>6.1f} / {target_t:<5} g     ({p_t:>5.1f}%)  | Pozostało: {target_t - suma_tluszczu:>6.1f} g")

        print("   " + "-" * 69)

    print("\nCZAS PRZERW (STOPER):")
    if not PRZERWY:
        print("   (Brak zarejestrowanych przerw w tej sesji)")
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
    print("=" * 65 + "\n")