from sqlalchemy import create_engine
import os
from app.db_models import *
from dotenv import load_dotenv
from contextlib import asynccontextmanager
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()