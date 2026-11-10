import csv
import json
import os

trening = "data/workouts.csv"
makro = "data/nutrition.csv"
profil = "data/user_profile.json"


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