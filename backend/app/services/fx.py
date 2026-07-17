import json
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Protocol, TypedDict
from urllib.parse import urlencode
from urllib.request import urlopen

from sqlmodel import Session, select

from backend.app.api.errors import ApiError
from backend.app.core.config import settings
from backend.app.models.fx import FxRate, FxRateSet
from backend.app.schemas.ids import parse_public_id


class FxRateProvider(Protocol):
    def quote(
        self,
        base_currency: str,
        currencies: list[str],
        rate_timestamp: datetime,
    ) -> dict[str, Decimal]: ...


class ManualRateInput(TypedDict):
    currency: str
    rate_to_base: str


class FrankfurterFxProvider:
    def quote(
        self,
        base_currency: str,
        currencies: list[str],
        rate_timestamp: datetime,
    ) -> dict[str, Decimal]:
        if not currencies:
            return {}
        query = urlencode(
            {
                "base": base_currency,
                "symbols": ",".join(sorted(set(currencies))),
            }
        )
        url = f"{settings.frankfurter_base_url}/latest?{query}"
        with urlopen(url, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        rates = payload.get("rates", {})
        return {
            currency: Decimal(str(rates[currency]))
            for currency in currencies
            if currency in rates
        }


def get_fx_provider() -> FxRateProvider:
    return FrankfurterFxProvider()


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


def format_rate(rate: Decimal) -> str:
    return f"{rate.quantize(Decimal('0.00000001'))}"


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


def freeze_api_rate_set(
    session: Session,
    *,
    provider: FxRateProvider,
    base_currency: str,
    currencies: list[str],
    rate_timestamp: datetime | None = None,
) -> FxRateSet:
    timestamp = rate_timestamp or datetime.now(UTC)
    unique_currencies = sorted({currency.upper() for currency in currencies})
    quoted_rates = provider.quote(base_currency, unique_currencies, timestamp)
    missing = [
        currency
        for currency in unique_currencies
        if currency != base_currency and currency not in quoted_rates
    ]
    if missing:
        raise ApiError(
            422,
            "validation_error",
            "FX provider did not return every required currency.",
            [{"field": "currencies", "reason": f"Missing: {', '.join(missing)}"}],
        )

    rate_set = FxRateSet(
        base_currency=base_currency,
        rate_source="api",
        rate_timestamp=timestamp.isoformat().replace("+00:00", "Z"),
    )
    session.add(rate_set)
    session.commit()
    session.refresh(rate_set)

    for currency in unique_currencies:
        if currency == base_currency:
            continue
        session.add(
            FxRate(
                fx_rate_set_id=rate_set.id,
                currency=currency,
                rate_to_base=validate_rate_string(format_rate(quoted_rates[currency])),
            )
        )
    session.commit()
    session.refresh(rate_set)
    return rate_set


def quote_rates(
    provider: FxRateProvider,
    *,
    base_currency: str,
    currencies: list[str],
    rate_timestamp: datetime | None = None,
) -> dict[str, str]:
    timestamp = rate_timestamp or datetime.now(UTC)
    rates = provider.quote(
        base_currency,
        sorted({currency.upper() for currency in currencies}),
        timestamp,
    )
    return {
        currency: validate_rate_string(format_rate(rate))
        for currency, rate in rates.items()
    }


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
