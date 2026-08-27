import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

database_url = (
    os.getenv("database_url")
    or os.getenv("DATABASE_URL")
    or "postgresql://postgres:postgres@localhost:5432/eduguardian"
)

# Convert async scheme to sync for psycopg2 if necessary
if database_url.startswith("postgresql+asyncpg://"):
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://", 1)

engine = create_engine(database_url, pool_pre_ping=True)

sessionlocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()