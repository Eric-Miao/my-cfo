from decimal import Decimal, InvalidOperation

from backend.app.api.errors import ApiError


def validate_money_string(value: str) -> str:
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ApiError(
            422,
            "validation_error",
            "Amount must be a valid decimal string.",
            [{"field": "amount_original", "reason": "Invalid decimal."}],
        ) from exc

    if amount < 0:
        raise ApiError(
            422,
            "validation_error",
            "Amount must be non-negative.",
            [{"field": "amount_original", "reason": "Amount must be non-negative."}],
        )

    if -amount.as_tuple().exponent > 8:
        raise ApiError(
            422,
            "validation_error",
            "Amount supports up to 8 decimal places.",
            [{"field": "amount_original", "reason": "Too many decimal places."}],
        )

    return value
