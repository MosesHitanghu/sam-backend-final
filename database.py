import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

try:
    from dotenv import load_dotenv
    load_dotenv(".env.local")
except ImportError:
    pass

DATABASE_URL = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("POSTGRES_URL or DATABASE_URL is not set")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

parts = urlsplit(DATABASE_URL)
query_params = [
    (k, v)
    for k, v in parse_qsl(parts.query, keep_blank_values=True)
    if k != "supa"
]
DATABASE_URL = urlunsplit(
    (parts.scheme, parts.netloc, parts.path, urlencode(query_params), parts.fragment)
)

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
