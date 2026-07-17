from collections.abc import Generator

from sqlmodel import Session, create_engine

from backend.app.core.config import settings
from backend.app.db.base import SQLModel

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
