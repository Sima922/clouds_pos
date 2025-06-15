import os
from dotenv import load_dotenv

load_dotenv()
print("Loaded password:", os.getenv("DB_PASSWORD"))
