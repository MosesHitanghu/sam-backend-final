from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_NAME = "sam_db"
DB_USER = "postgres"
DB_PASS = "Goodness"
DB_HOST = "localhost"
DB_PORT = "5432"

SQLALCHEMY_DATABASE_URL = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
