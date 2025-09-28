import os
from datetime import datetime
from typing import Generator

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Database Configuration ---
# Use an environment variable for the database URL for production readiness.
# Default to a SQLite database for local development if not set.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todo.db")

# Create a SQLAlchemy engine
# `connect_args={"check_same_thread": False}` is needed for SQLite when
# multiple threads might access the database, common in web applications.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create a SessionLocal class
# `autocommit=False` means changes are not automatically saved.
# `autoflush=False` means objects are not automatically flushed to the session.
# `bind=engine` connects the session to our database engine.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare a base class for our declarative models
Base = declarative_base()

# --- Database Models ---

class Task(Base):
    """
    Represents a single task in the todo application.
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', completed={self.completed})>"

# --- Database Initialization Functions ---

def init_db():
    """
    Initializes the database by creating all tables defined in Base.
    This function should be called once when the application starts.
    """
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialization complete.")

def get_db() -> Generator:
    """
    Dependency function to get a database session.
    This function yields a database session and ensures it's closed after use.
    It's designed to be used with frameworks like FastAPI.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Example of how to run init_db if this file is executed directly
if __name__ == "__main__":
    # This block will only run when the script is executed directly,
    # not when imported as a module.
    print(f"Using database: {DATABASE_URL}")
    init_db()

    # Example of adding a task
    with SessionLocal() as db:
        print("\nAdding a sample task...")
        new_task = Task(title="Learn SQLAlchemy", completed=False)
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        print(f"Added task: {new_task}")

        # Example of querying tasks
        print("\nQuerying all tasks...")
        tasks = db.query(Task).all()
        for task in tasks:
            print(task)

        # Example of updating a task
        if tasks: