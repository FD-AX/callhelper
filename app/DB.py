from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
from app.db_models import *
from dotenv import load_dotenv
from contextlib import asynccontextmanager
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

#@asynccontextmanager
async def get_db():
    async with SessionLocal() as session:
        yield session