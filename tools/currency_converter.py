from __future__ import annotations

from decimal import Decimal, InvalidOperation

import requests


API_URL = "https://api.frankfurter.app/latest"


def _normalize_currency(value: str | None, label: str) -> str:
    if not value:
        raise ValueError(f"Missing {label} currency code.")

    code = value.strip().upper()
    if len(code) != 3 or not code.isalpha():
        raise ValueError(f"Invalid {label} currency code: {value}")

    return code


def _format_amount(amount: Decimal) -> str:
    display = format(amount.normalize(), "f")

    if "." in display:
        display = display.rstrip("0").rstrip(".")

    return display


def execute(arguments: dict) -> str:
    try:
        amount_raw = arguments.get("amount", 1)
        from_currency = _normalize_currency(arguments.get("from_currency") or arguments.get("from"), "source")
        to_currency = _normalize_currency(arguments.get("to_currency") or arguments.get("to"), "target")

        try:
            amount = Decimal(str(amount_raw))
        except (InvalidOperation, TypeError) as error:
            raise ValueError(f"Invalid amount: {amount_raw}") from error

        response = requests.get(
            API_URL,
            params={
                "amount": str(amount),
                "from": from_currency,
                "to": to_currency,
            },
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        result = data.get("rates", {}).get(to_currency)

        if result is None:
            raise ValueError("Currency conversion result was not returned.")

        return f"{_format_amount(amount)} {from_currency} = {result} {to_currency}"
    except Exception as error:
        return f"Currency Converter Error: {error}"


if __name__ == "__main__":
    print(execute({"amount": 100, "from_currency": "USD", "to_currency": "INR"}))