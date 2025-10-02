import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Use in-memory SQLite for simplicity, but recommend PostgreSQL for production.
# To use PostgreSQL, set DATABASE_URL in a .env file, e.g.:
# DATABASE_URL="postgresql://user:password@postgresserver/db"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./college_attendance.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # connect_args is needed only for SQLite.
    connect_args={"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()