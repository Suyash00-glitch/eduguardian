import os
from dotenv import load_dotenv

load_dotenv()

database_url = os.getenv("database_url")
secret_key = os.getenv("secret_key")