from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

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


class CsvImportPreviewRequest(BaseModel):
    reporting_at: str
    csv_text: str


class CsvImportCommitRequest(BaseModel):
    preview_token: str


@router.post("/owner-snapshots/import/preview")
def preview_owner_snapshot_import(
    payload: CsvImportPreviewRequest,
    session: SessionDep,
) -> dict:
    return csv_import.preview_import(
        session,
        reporting_at=payload.reporting_at,
        csv_text=payload.csv_text,
    )


@router.post("/owner-snapshots/import/commit", status_code=201)
def commit_owner_snapshot_import(
    payload: CsvImportCommitRequest,
    session: SessionDep,
) -> dict:
    return csv_import.commit_import(session, preview_token=payload.preview_token)
