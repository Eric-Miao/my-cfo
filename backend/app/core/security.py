from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

SESSION_COOKIE_NAME = "my_cfo_session"
SESSION_MAX_AGE_SECONDS = 7 * 24 * 60 * 60

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


def create_session_token(secret: str) -> str:
    serializer = URLSafeTimedSerializer(secret_key=secret, salt="my-cfo-session")
    issued_at = datetime.now(UTC).isoformat()
    return serializer.dumps({"principal": "admin", "issued_at": issued_at})


def verify_session_token(secret: str, token: str) -> bool:
    serializer = URLSafeTimedSerializer(secret_key=secret, salt="my-cfo-session")
    try:
        payload = serializer.loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return False
    return payload.get("principal") == "admin"


def session_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(seconds=SESSION_MAX_AGE_SECONDS)
