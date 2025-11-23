# app/db/init_db.py
from app.db.session import engine
from app.db.base_class import Base

# Import models so they are registered with Base.metadata
import app.models  # noqa


def init_db() -> None:
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)