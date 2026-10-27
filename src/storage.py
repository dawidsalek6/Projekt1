import csv
import json
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

trening = "data/workouts.csv"
makro = "data/nutrition.csv"
profil = "data/user_profile.json"
katalog_kopii = "data/backups"
katalog_kwarantanny = "data/corrupted"


def upewnij_sie_ze_katalog_istnieje():
    katalog = os.path.dirname(trening)
    if katalog and not os.path.exists(katalog):
        os.makedirs(katalog, exist_ok=True)
    if not os.path.exists(katalog_kopii):
        os.makedirs(katalog_kopii, exist_ok=True)
    if not os.path.exists(katalog_kwarantanny):
        os.makedirs(katalog_kwarantanny, exist_ok=True)


def stworz_kopie_zapasowa_i_rotuj(sciezka_pliku: str, max_kopii: int = 3):
    if not os.path.exists(sciezka_pliku) or os.path.getsize(sciezka_pliku) == 0:
        return

    upewnij_sie_ze_katalog_istnieje()
    nazwa_bazowa = Path(sciezka_pliku).stem
    stempel = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    nazwa_bak = f"{nazwa_bazowa}_{stempel}.bak"
    sciezka_bak = os.path.join(katalog_kopii, nazwa_bak)

    shutil.copy2(sciezka_pliku, sciezka_bak)

    istniejace_kopie = [
        os.path.join(katalog_kopii, f) for f in os.listdir(katalog_kopii)
        if f.startswith(nazwa_bazowa) and f.endswith(".bak")
    ]
    istniejace_kopie.sort(key=os.path.getmtime)

    while len(istniejace_kopie) > max_kopii:
        najstarszy = istniejace_kopie.pop(0)
        try:
            os.remove(najstarszy)
        except OSError as e:
            print(f"Ostrzeżenie: Nie udało się usunąć starej kopii {najstarszy}: {e}")


def _zapisz_atomowo_csv(sciezka_pliku: str, pola: list, wiersze: list) -> None:
    upewnij_sie_ze_katalog_istnieje()

    # Tworzenie kopii zapasowej
    stworz_kopie_zapasowa_i_rotuj(sciezka_pliku, max_kopii=3)

    katalog = os.path.dirname(sciezka_pliku) or "."

    with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=katalog, encoding="utf-8", newline="") as plik:
        sciezka_tmp = plik.name
        writer = csv.DictWriter(plik, fieldnames=pola, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(wiersze)

        plik.flush()
        os.fsync(plik.fileno())

    os.replace(sciezka_tmp, sciezka_pliku)


def zapisz_profil_json(dane_profilu: dict) -> None:
    upewnij_sie_ze_katalog_istnieje()
    stworz_kopie_zapasowa_i_rotuj(profil, max_kopii=3)

    katalog = os.path.dirname(profil) or "."

    with tempfile.NamedTemporaryFile(mode="w", delete=False, dir=katalog, encoding="utf-8") as plik:
        sciezka_tmp = plik.name
        json.dump(dane_profilu, plik, indent=4, ensure_ascii=False)
        plik.flush()
        os.fsync(plik.fileno())

    os.replace(sciezka_tmp, profil)


def przenies_do_kwarantanny_i_napraw(sciezka_pliku: str) -> None:
    upewnij_sie_ze_katalog_istnieje()
    nazwa_bazowa = Path(sciezka_pliku).name
    stempel = datetime.now().strftime("%Y%m%d_%H%M%S")
    sciezka_kwarantanny = os.path.join(katalog_kwarantanny, f"corrupted_{stempel}_{nazwa_bazowa}")

    if os.path.exists(sciezka_pliku):
        try:
            shutil.move(sciezka_pliku, sciezka_kwarantanny)
            print(f"KWARANTANNA: Przeniesiono uszkodzony plik '{sciezka_pliku}' do '{sciezka_kwarantanny}'.")
        except OSError as e:
            print(f"Błąd podczas przenoszenia pliku do kwarantanny: {e}")

    stem = Path(sciezka_pliku).stem
    istniejace_kopie = [
        os.path.join(katalog_kopii, f) for f in os.listdir(katalog_kopii)
        if f.startswith(stem) and f.endswith(".bak")
    ]

    if istniejace_kopie:
        istniejace_kopie.sort(key=os.path.getmtime, reverse=True)
        najnowsza_kopia = istniejace_kopie[0]
        shutil.copy2(najnowsza_kopia, sciezka_pliku)
        print(f"AUTO-NAPRAWA: Pomyślnie przywrócono plik '{sciezka_pliku}' z kopii '{najnowsza_kopia}'.")
    else:
        print(f"BRAK KOPII: Nie znaleziono kopii zapasowej .bak. Utworzono pusty/domyślny plik.")


def zapisz_cwiczenie(cwiczenie):
    pola = [
        "id", "data", "cwiczenie", "serie",
        "powtorzenia", "ciezar_kg"
    ]
    dotychczasowe_treningi = wczytaj_treningi()
    dotychczasowe_treningi.append(cwiczenie)

    _zapisz_atomowo_csv(trening, pola, dotychczasowe_treningi)
    print("Ćwiczenie zapisane!")


def zapisz_posilek(posilek):
    pola = [
        "id", "data", "nazwa_posilku", "bialko_g",
        "weglowodany_g", "tluszcz_g", "kcal"
    ]
    dotychczasowe_posilki = wczytaj_posilki()
    dotychczasowe_posilki.append(posilek)

    _zapisz_atomowo_csv(makro, pola, dotychczasowe_posilki)
    print("Posiłek zapisany!")


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
        print(f"Wykryto uszkodzenie pliku {trening}: {e}")
        przenies_do_kwarantanny_i_napraw(trening)
        return wczytaj_treningi()

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
        print(f" Wykryto uszkodzenie pliku {makro}: {e}")
        przenies_do_kwarantanny_i_napraw(makro)
        return wczytaj_posilki()

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
        # FIX: Jeśli plik nie istnieje, zapisujemy domyślny atomowo
        zapisz_profil_json(domyslny_profil)
        return domyslny_profil

    try:
        with open(profil, "r", encoding="utf-8") as plik:
            return json.load(plik)

    except (json.JSONDecodeError, OSError) as e:
        print(f"Wykryto uszkodzenie profilu JSON: {e}")
        przenies_do_kwarantanny_i_napraw(profil)
        return wczytaj_profil_json()