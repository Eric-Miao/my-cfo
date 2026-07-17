from decimal import Decimal

MONEY_QUANT = Decimal("0.00000001")


def format_money(value: Decimal) -> str:
    return f"{value.quantize(MONEY_QUANT)}"
