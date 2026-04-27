import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

try:
    from dotenv import load_dotenv
    load_dotenv(".env.local")
except ImportError:
    pass


DATABASE_URL = (
    os.getenv("sam_DATABASE_URL")
    or os.getenv("sam_POSTGRES_URL")
    or os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
)

if not DATABASE_URL:
    raise RuntimeError(
        "Database URL is not set. Set DATABASE_URL or POSTGRES_URL in Vercel Environment Variables."
    )

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