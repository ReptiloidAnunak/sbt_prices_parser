
from pathlib import Path

CLIENT_ID = 3691711881415562
CLIENT_SECRET = 'ncX52tIJNGVjwIwvo12aAAT34aBiA7k2'
REDIRECT_URI = 'https://magsbt.com'
TOKEN_FILE = 'ml_token.json'
SELLERS_FILE = 'sellers.json'


BASE_DIR = Path(__file__).resolve().parent

DATA_FOLDER = BASE_DIR / "data"

JSON_FILE = 'ml_concurents.json'

DB_DIR = BASE_DIR / 'data_base'

DB_URL = f"sqlite:///{DB_DIR}/ml_parser.db"