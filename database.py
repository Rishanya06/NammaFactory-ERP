
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from models import Base


# Store the database in the main NammaFactory project folder.
DATABASE_PATH = Path(__file__).resolve().parent / "nammafactory.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


# Enable foreign-key enforcement in SQLite.
@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def initialize_database():
    """Create all database tables if they do not already exist."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Provide a database session and close it safely."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
