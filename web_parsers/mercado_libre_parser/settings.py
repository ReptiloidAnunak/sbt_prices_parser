
from pathlib import Path
import random


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

def get_useragents() -> list:
    with open("user_agents.txt") as f:
        user_agents = [line.strip() for line in f if line.strip()]
        return user_agents

USER_AGENTS = get_useragents()


HEADERS = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": random.choice([
                "es-AR,es;q=0.9,en;q=0.8",
                "en-US,en;q=0.9",
                "es-ES,es;q=0.9,en;q=0.8"
            ]),
            "Accept": "text/html,application/xhtml+xml",
            "Connection": "keep-alive",
            }