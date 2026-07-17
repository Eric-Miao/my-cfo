from fastapi import APIRouter
from fastapi.responses import Response

from backend.app.api.deps import SessionDep
from backend.app.services import csv_import

router = APIRouter(prefix="/csv", tags=["csv-import"])


@router.get("/templates/export")
def export_templates(session: SessionDep) -> Response:
    return Response(
        content=csv_import.export_template_csv(session),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="templates.csv"'},
    )
