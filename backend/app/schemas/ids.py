from backend.app.api.errors import ApiError


def public_id(prefix: str, database_id: int | None) -> str:
    if database_id is None:
        raise ValueError("database_id must be set before serialization")
    return f"{prefix}_{database_id}"


def parse_public_id(prefix: str, value: str) -> int:
    expected = f"{prefix}_"
    if not value.startswith(expected):
        raise ApiError(404, "not_found", "Resource was not found.")
    raw_id = value.removeprefix(expected)
    if not raw_id.isdigit():
        raise ApiError(404, "not_found", "Resource was not found.")
    return int(raw_id)
