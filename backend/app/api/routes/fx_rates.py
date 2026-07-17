from fastapi import APIRouter

from backend.app.api.deps import SessionDep
from backend.app.schemas.fx import FxQuoteRequest, FxRateSetRead
from backend.app.services import fx

router = APIRouter(tags=["fx-rates"])


@router.post("/fx-rates/quote")
def quote_fx_rates(payload: FxQuoteRequest) -> dict[str, object]:
    return {
        "base_currency": payload.base_currency,
        "rates": fx.quote_rates(
            fx.get_fx_provider(),
            base_currency=payload.base_currency,
            currencies=payload.currencies,
        ),
    }


@router.get("/fx-rate-sets/{rate_set_id}")
def get_fx_rate_set(rate_set_id: str, session: SessionDep) -> FxRateSetRead:
    rate_set = fx.get_rate_set(session, rate_set_id)
    return FxRateSetRead.from_model(rate_set, fx.rate_set_rates(session, rate_set.id))
