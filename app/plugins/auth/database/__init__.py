import os

from typing import Generator
from sqlalchemy.orm import Session

from ...utils.database import DatabaseAsync


database = DatabaseAsync(
    "sqlite+aiosqlite:///",
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "auth_database.sqlite"
    )
)

def get_db() -> Generator[Session]:
    db = database.Session()
    try:
        yield db
    finally:
        db.close()
