from http import HTTPStatus

from fastapi import APIRouter

from backend.app.api.deps import SessionDep
from backend.app.schemas.ids import parse_public_id
from backend.app.schemas.template import TemplateCreate, TemplatePatch, TemplateRead
from backend.app.services import templates

router = APIRouter(tags=["templates"])


def _read_template(session: SessionDep, template) -> TemplateRead:
    model, tag_reads = templates.serialize_template(session, template)
    return TemplateRead.from_model(model, tag_reads)


@router.get("/templates")
def list_templates(session: SessionDep) -> dict[str, object]:
    return {
        "items": [
            _read_template(session, template).model_dump(mode="json")
            for template in templates.list_templates(session)
        ],
        "page": {"limit": 50, "next_cursor": None},
    }


@router.post("/templates", status_code=HTTPStatus.CREATED)
def create_template(
    payload: TemplateCreate,
    session: SessionDep,
) -> TemplateRead:
    return _read_template(session, templates.create_template(session, payload))


@router.patch("/templates/{template_id}")
def patch_template(
    template_id: str,
    payload: TemplatePatch,
    session: SessionDep,
) -> TemplateRead:
    return _read_template(
        session,
        templates.patch_template(session, parse_public_id("tpl", template_id), payload),
    )


@router.post("/templates/{template_id}/deactivate")
def deactivate_template(template_id: str, session: SessionDep) -> TemplateRead:
    return _read_template(
        session,
        templates.set_template_active(
            session,
            parse_public_id("tpl", template_id),
            False,
        ),
    )


@router.post("/templates/{template_id}/recover")
def recover_template(template_id: str, session: SessionDep) -> TemplateRead:
    return _read_template(
        session,
        templates.set_template_active(
            session,
            parse_public_id("tpl", template_id),
            True,
        ),
    )


@router.get("/institution-suggestions")
def institution_suggestions(query: str, session: SessionDep) -> dict[str, list[str]]:
    return {"items": templates.institution_suggestions(session, query)}
