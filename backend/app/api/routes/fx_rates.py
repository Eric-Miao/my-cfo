from fastapi import APIRouter

from backend.app.api.deps import SessionDep
from backend.app.schemas.fx import FxRateSetRead
from backend.app.services import fx

router = APIRouter(tags=["fx-rates"])


@router.get("/fx-rate-sets/{rate_set_id}")
def get_fx_rate_set(rate_set_id: str, session: SessionDep) -> FxRateSetRead:
    rate_set = fx.get_rate_set(session, rate_set_id)
    return FxRateSetRead.from_model(rate_set, fx.rate_set_rates(session, rate_set.id))
