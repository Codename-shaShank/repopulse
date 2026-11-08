from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

_connect_args: dict = {}
_engine_kwargs: dict = {"pool_pre_ping": True, "future": True}

if settings.sqlalchemy_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
else:
    # Hosted Postgres (Supabase) drops idle connections, so keep the pool small
    # and recycle well before the server-side timeout.
    _engine_kwargs |= {"pool_size": 5, "max_overflow": 5, "pool_recycle": 300}

engine = create_engine(
    settings.sqlalchemy_url, connect_args=_connect_args, **_engine_kwargs
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, expire_on_commit=False, future=True
)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
