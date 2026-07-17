from pydantic import BaseModel, Field

from backend.app.models.fx import FxRate, FxRateSet
from backend.app.schemas.ids import public_id


class ManualFxRateInput(BaseModel):
    currency: str
    rate_to_base: str


class FxFinalizeRequest(BaseModel):
    mode: str
    manual_rates: list[ManualFxRateInput] = Field(default_factory=list)


class FxQuoteRequest(BaseModel):
    base_currency: str
    currencies: list[str]


class FxRateRead(BaseModel):
    currency: str
    rate_to_base: str

    @classmethod
    def from_model(cls, rate: FxRate) -> "FxRateRead":
        return cls(currency=rate.currency, rate_to_base=rate.rate_to_base)


class FxRateSetRead(BaseModel):
    id: str
    base_currency: str
    rate_source: str
    rate_timestamp: str
    rates: list[FxRateRead]

    @classmethod
    def from_model(cls, rate_set: FxRateSet, rates: list[FxRate]) -> "FxRateSetRead":
        return cls(
            id=public_id("fxset", rate_set.id),
            base_currency=rate_set.base_currency,
            rate_source=rate_set.rate_source,
            rate_timestamp=rate_set.rate_timestamp,
            rates=[FxRateRead.from_model(rate) for rate in rates],
        )
