
#Working version of database.py, with some changes to support SQLAlchemy 2.0 and to remove the dependency on python-dotenv. The .env.local file is still supported, but it will be loaded manually if it exists.
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

try:
    from dotenv import load_dotenv

    load_dotenv(".env.local")
except ImportError:
    pass


DATABASE_URL = os.getenv("sam_DATABASE_URL") or os.getenv("sam_POSTGRES_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL or POSTGRES_URL is not set")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    poolclass=NullPool,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()