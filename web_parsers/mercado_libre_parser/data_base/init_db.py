from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from settings import DB_URL


engine = create_engine(DB_URL, echo=False)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()