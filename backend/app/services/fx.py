from decimal import Decimal, InvalidOperation
from typing import TypedDict

from sqlmodel import Session, select

from backend.app.api.errors import ApiError
from backend.app.models.fx import FxRate, FxRateSet
from backend.app.schemas.ids import parse_public_id


class ManualRateInput(TypedDict):
    currency: str
    rate_to_base: str


def validate_rate_string(value: str) -> str:
    try:
        rate = Decimal(value)
    except InvalidOperation as exc:
        raise ApiError(
            422,
            "validation_error",
            "FX rate must be a valid decimal string.",
            [{"field": "rate_to_base", "reason": "Invalid decimal."}],
        ) from exc

    if rate <= 0:
        raise ApiError(
            422,
            "validation_error",
            "FX rate must be greater than zero.",
            [{"field": "rate_to_base", "reason": "Rate must be positive."}],
        )
    if -rate.as_tuple().exponent > 8:
        raise ApiError(
            422,
            "validation_error",
            "FX rate supports up to 8 decimal places.",
            [{"field": "rate_to_base", "reason": "Too many decimal places."}],
        )
    return value


def freeze_manual_rate_set(
    session: Session,
    *,
    base_currency: str,
    manual_rates: list[ManualRateInput],
    rate_timestamp: str,
) -> FxRateSet:
    rate_set = FxRateSet(
        base_currency=base_currency,
        rate_source="manual",
        rate_timestamp=rate_timestamp,
    )
    session.add(rate_set)
    session.commit()
    session.refresh(rate_set)

    for rate in manual_rates:
        currency = rate["currency"].upper()
        if currency == base_currency:
            continue
        session.add(
            FxRate(
                fx_rate_set_id=rate_set.id,
                currency=currency,
                rate_to_base=validate_rate_string(rate["rate_to_base"]),
            )
        )
    session.commit()
    session.refresh(rate_set)
    return rate_set


def get_rate_set(session: Session, rate_set_public_id: str) -> FxRateSet:
    rate_set = session.get(FxRateSet, parse_public_id("fxset", rate_set_public_id))
    if rate_set is None:
        raise ApiError(404, "not_found", "FX rate set was not found.")
    return rate_set


def rate_set_rates(session: Session, rate_set_id: int | None) -> list[FxRate]:
    return list(
        session.exec(
            select(FxRate)
            .where(FxRate.fx_rate_set_id == rate_set_id)
            .order_by(FxRate.currency, FxRate.id)
        )
    )
