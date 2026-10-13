import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base  # <-- Add declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

engine = create_engine(DATABASE_URL)

# Add Base here
Base = declarative_base()

SessionLocal = sessionmaker(
    autocommit=False,   
    autoflush=False,
    bind=engine
)

def get_db():
    db=SessionLocal()
    try:
        yield db
    finally:
        db.close()