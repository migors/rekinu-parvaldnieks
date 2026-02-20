import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


def _get_data_dir() -> str:
    """Return the data directory. When running as a frozen EXE, store data in
    %APPDATA%/InvoiceManager/data/ so it persists across updates and works from Program Files."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller EXE (installed via Setup)
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        return os.path.join(appdata, 'InvoiceManager', 'data')
    else:
        # Development mode — use project-level data/ folder
        base_dir = os.path.dirname(os.path.abspath(__file__)) # app/
        root_dir = os.path.dirname(base_dir) # project root
        return os.path.join(root_dir, "data")


DATA_DIR = _get_data_dir()
os.makedirs(DATA_DIR, exist_ok=True)


SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'invoices.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
