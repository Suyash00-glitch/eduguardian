import os
from dotenv import load_dotenv

load_dotenv()

database_url = (
    os.getenv("database_url")
    or os.getenv("DATABASE_URL")
    or "postgresql://postgres:postgres@localhost:5432/eduguardian"
)
secret_key = (
    os.getenv("secret_key")
    or os.getenv("SECRET_KEY")
    or os.getenv("JWT_SECRET_KEY")
    or "eduguardian-dev-secret-key-2024"
    or "eduguardian-dev-secret-key-2026"
)