
import csv
import os

def zapisz_cwiczenie(cwiczenie):
    plik = "data/workouts.csv"

    istnieje = os.path.exists(plik)

    with open(plik, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["cwiczenie", "serie", "powtorzenia", "ciezar_kg"]
        )

        if not istnieje or os.path.getsize(plik) == 0:
            writer.writeheader()

        writer.writerow(cwiczenie)

    print("Ćwiczenie zapisane")

def dodaj_cwiczenie():
    cwiczenie = input("Nazwa ćwiczenia: ")
    serie = int(input("Liczba serii: "))
    powtorzenia = int(input("Liczba powtórzeń: "))
    ciezar = float(input("Ciężar (kg): "))

    wpis = {
        "cwiczenie": cwiczenie,
        "serie": serie,
        "powtorzenia": powtorzenia,
        "ciezar_kg": ciezar
    }

    zapisz_cwiczenie(wpis)
