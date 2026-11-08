from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401  (registers the tables)
from app.config import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _database_url(url: str) -> str:
    """Keep a relative SQLite file inside backend/, whichever folder you run from."""
    prefix = "sqlite:///"
    if url.startswith(prefix) and not url.startswith(prefix + "/"):
        path = Path(url[len(prefix):])
        if not path.is_absolute():
            return prefix + str(BACKEND_DIR / path)
    return url


engine = create_engine(_database_url(settings.database_url), connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
