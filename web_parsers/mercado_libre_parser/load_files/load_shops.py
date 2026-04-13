import enum
import pandas as pd
from sqlalchemy.orm import Session
from data_base.models import Shop, SpecializationEnum
from data_base.init_db import SessionLocal


def safe_enum(value: str):
    try:
        return SpecializationEnum(value)
    except ValueError:
        raise ValueError(f"Unknown specialization: {value}")


def load_shops_from_csv(session: Session, csv_path: str):
    df = pd.read_csv(csv_path)

    shops = [
        Shop(
            title=row["Title"],
            url=row["URL"],
            specialization=safe_enum(row["Category"])
        )
        for _, row in df.iterrows()
    ]

    session.add_all(shops)
    session.commit()


session = SessionLocal()
load_shops_from_csv(session, "load_files/shops.csv")
session.close()

