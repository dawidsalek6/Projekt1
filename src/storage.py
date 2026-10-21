import json
import os

def zapisz_cwiczenie(cwiczenie):
    plik = "data/user_profile.json"

    if os.path.exists(plik):
        with open(plik, "r", encoding="utf-8") as f:
            try:
                dane = json.load(f)
            except json.JSONDecodeError:
                dane = []
    else:
        dane = []

    dane.append(cwiczenie)

    with open(plik, "w", encoding="utf-8") as f:
        json.dump(dane, f, ensure_ascii=False, indent=4)