from __future__ import annotations


def _category(bmi: float) -> str:
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25:
        return "Normal weight"
    if bmi < 30:
        return "Overweight"
    return "Obesity"


def execute(arguments: dict) -> str:
    try:
        weight = float(arguments.get("weight_kg", arguments.get("weight")))
        height_cm = arguments.get("height_cm")
        height_m = arguments.get("height_m")

        if height_m is not None:
            height = float(height_m)
        elif height_cm is not None:
            height = float(height_cm) / 100.0
        else:
            raise ValueError("Missing height. Provide height_cm or height_m.")

        if weight <= 0:
            raise ValueError("Weight must be greater than zero.")
        if height <= 0:
            raise ValueError("Height must be greater than zero.")

        bmi = weight / (height * height)
        return f"BMI: {bmi:.2f} ({_category(bmi)})"
    except Exception as error:
        return f"BMI Calculator Error: {error}"


if __name__ == "__main__":
    print(execute({"weight_kg": 72, "height_cm": 170}))