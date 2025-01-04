import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

db_name = "books.db"
db_path = os.path.join(BASE_DIR, db_name)
