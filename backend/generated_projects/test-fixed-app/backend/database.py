# database.py
# In-memory data store for the application.

from typing import Dict
from .models import Task
from datetime import datetime, timezone

# 
# SECURITY NOTE: This is an in-memory "database" for demonstration purposes.
# - Data is not persistent and will be lost on application restart.
# - This implementation is not thread-safe for high-concurrency scenarios.
# For production use, replace this with a proper database connection
# (e.g., PostgreSQL with SQLAlchemy or MongoDB with Motor).
# 

# We use a dictionary to simulate a database collection.
# The key is the task ID (str), and the value is the Task object.
DB: Dict[str, Task] = {}

def initialize_db():
    """
    Clears and populates the in-memory database with some sample data.
    This function is called on application startup.
    """
    DB.clear()
    
    # Add some realistic sample tasks
    sample_tasks = [
        Task(
            title="Complete FastAPI project proposal",
            description="Draft the initial proposal document and outline the project milestones.",
            created_at=datetime(2023, 8, 20, 10, 0, 0, tzinfo=timezone.utc)
        ),
        Task(
            title="Review team pull requests",
            description="Check the latest PRs on GitHub for the 'feature-auth' branch.",
            completed=True,
            created_at=datetime(2023, 8, 21, 15, 30, 0, tzinfo=timezone.utc)
        ),
        Task(
            title="Prepare for weekly sync meeting",
            description="Gather updates and prepare agenda items for the Wednesday meeting.",
            created_at=datetime(2023, 8, 22, 9, 0, 0, tzinfo=timezone.utc)
        ),
    ]
    
    for task in sample_tasks:
        DB[task.id] = task

    print(f"Initialized in-memory database with {len(DB)} sample tasks.")