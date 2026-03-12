import sqlite3
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./codescope.db"
DB_PATH      = "./codescope.db"

engine       = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base         = declarative_base()


class Analysis(Base):
    __tablename__ = "analysis"

    id       = Column(Integer, primary_key=True, index=True)
    code     = Column(String)
    language = Column(String, default="python")
    result   = Column(JSON)


# Create table if it doesn't exist yet
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# Migration: add `language` column to existing databases that predate it.
# Uses raw sqlite3 (not SQLAlchemy) — works reliably on SQLite.
# ---------------------------------------------------------------------------
def _migrate():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # PRAGMA table_info returns one row per column; check names
    existing = {row[1] for row in cur.execute("PRAGMA table_info(analysis)")}
    if "language" not in existing:
        cur.execute("ALTER TABLE analysis ADD COLUMN language TEXT DEFAULT 'python'")
        con.commit()
        print("DB migration: added 'language' column to analysis table.")
    con.close()

_migrate()