import os
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("database_url") or "postgresql://postgres:azmal123@localhost:5432/eduguardian"
secret_key = os.getenv("secret_key") or "eduguardian-super-secret-key-2024"