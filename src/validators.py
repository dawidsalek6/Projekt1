"Pobiera int z walidacją."


def getIntInput(
        prompt: str,
        min_val: int = 1,
        max_val: int = 5
) -> int:
    while True:
        raw = input(prompt).strip()
        if not raw:
            print("Błąd: Pusta wartość.")
            continue
        try:
            val = int(raw)
            if min_val is not None and val < min_val:
                print(f"Błąd: Wartość < {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"Błąd: Wartość > {max_val}")
                continue
            return val
        except ValueError:
            print(f"Błąd: '{raw}' to nie int!")


"Pobiera float z walidacją."


def getFloatInput(
        prompt: str,
        min_val: float = 1.0,
        max_val: float = 5.0
) -> float:
    while True:
        raw = input(prompt).strip().replace(",", ".")
        if not raw:
            print("Błąd: Pusta wartość.")
            continue
        try:
            val = float(raw)
            if min_val is not None and val < min_val:
                print(f"Błąd: Wartość < {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"Błąd: Wartość > {max_val}")
                continue
            return val
        except ValueError:
            print(f"Błąd: '{raw}' to nie float!")


"Pobiera niepusty napis z walidacją."


def getNonEmptyString(prompt: str) -> str:
    while True:
        raw = input(prompt).strip()
        if not raw:
            print("Błąd: Pusta wartość.")
            continue
        return raw
