from typing import Any


def error_response(
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        }
    }
