from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import os
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")

Base = declarative_base()
 
# Sync engine for initial setup
engine = create_engine(DATABASE_URL)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine for production use
async_engine = create_async_engine(ASYNC_DATABASE_URL)
AsyncSession = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

def create_tables(): 
    Base.metadata.create_all(bind=engine)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()