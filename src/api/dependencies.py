from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from src.security.auth import verify_admin_api_key
from src.storage.database import SessionLocal


def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(request: Request) -> None:
    verify_admin_api_key(request)


AdminRequired = Depends(require_admin)
