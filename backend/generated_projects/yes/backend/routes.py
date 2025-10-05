import uuid
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any
from datetime import date, datetime, timedelta

# In a real application, these models would be in a separate 'models.py' file.
# To fulfill the request of providing a single file, they are defined here.
from pydantic import BaseModel, Field

# --- Models ---

class MilestoneBase(BaseModel):
    title: str
    description: str | None = None

class MilestoneCreate(MilestoneBase):
    pass

class MilestoneOut(MilestoneBase):
    id: int
    is_complete: bool

    class Config:
        from_attributes = True

class GoalBase(BaseModel):
    title: str
    description: str | None = None
    target_date: date

class GoalCreate(GoalBase):
    # When creating a goal, users can optionally provide initial milestones
    milestones: List[MilestoneCreate] = []

class GoalOut(GoalBase):
    id: int
    created_at: datetime
    milestones: List[MilestoneOut]

    class Config:
        from_attributes = True

class HabitCompletion(BaseModel):
    date: date
    is_complete: bool

    class Config:
        from_attributes = True

class HabitOut(BaseModel):
    id: int
    title: str
    completions_this_week: List[HabitCompletion]

    class Config:
        from_attributes = True


# --- In-Memory Storage (acting as a mock database) ---

# A mock user for authentication purposes
MOCK_USER = {"id": 1, "username": "testuser"}

db: Dict[str, List[Dict[str, Any]]] = {
    "goals": [
        {
            "id": 1, "user_id": 1, "title": "Learn FastAPI",
            "description": "Master the framework by building a project.",
            "target_date": date(2024, 12, 31), "created_at": datetime.utcnow()
        },
        {
            "id": 2, "user_id": 1, "title": "Run a 5k",
            "description": "Train and complete a 5k race.",
            "target_date": date(2024, 9, 30), "created_at": datetime.utcnow()
        },
        # This goal belongs to another user and should not be returned
        {
            "id": 3, "user_id": 2, "title": "Another User's Goal",
            "description": "This should not be visible to user 1.",
            "target_date": date(2024, 8, 1), "created_at": datetime.utcnow()
        }
    ],
    "milestones": [
        {"id": 101, "goal_id": 1, "title": "Complete the official tutorial", "description": None, "is_complete": True},
        {"id": 102, "goal_id": 1, "title": "Build a simple CRUD app", "description": None, "is_complete": False},
        {"id": 103, "goal_id": 2, "title": "Run 1k without stopping", "description": None, "is_complete": True},
        {"id": 104, "goal_id": 2, "title": "Run 3k without stopping", "description": None, "is_complete": False},
    ],
    "habits": [
        {"id": 201, "user_id": 1, "title": "Drink 8 glasses of water"},
        {"id": 202, "user_id": 1, "title": "Read for 15 minutes"},
        {"id": 203, "user_id": 2, "title": "Another User's Habit"}
    ],
    "habit_completions": [
        {"id": 301, "habit_id": 201, "date": date.today() - timedelta(days=1), "is_complete": True},
        {"id": 302, "habit_id": 201, "date": date.today(), "is_complete": False},
        {"id": 303, "habit_id": 202, "date": date.today() - timedelta(days=2), "is_complete": True},
        {"id": 304, "habit_id": 202, "date": date.today() - timedelta(days=1), "is_complete": True},
        # A completion from last week that should be filtered out
        {"id": 305, "habit_id": 201, "date": date.today() - timedelta(days=8), "is_complete": True},
    ]
}

# --- Dependency for Authentication ---

async def get_current_user() -> Dict[str, Any]:
    """A mock dependency to simulate retrieving an authenticated user."""
    return MOCK_USER

# --- APIRouter Setup ---

router = APIRouter(
    prefix="/api/v1",
    tags=["Productivity"],
)

# --- Helper Functions ---

def get_next_id(table_name: str) -> int:
    """Generates a new unique ID for a given table."""
    if not db[table_name]:
        return 1
    return max(item["id"] for item in db[table_name]) + 1

# --- Routes ---

@router.get("/goals", response_model=List[GoalOut], summary="Get All Goals")
async def get_goals(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve all goals and their associated milestones for the authenticated user.
    """
    user_id = current_user["id"]
    user_goals = [goal for goal in db["goals"] if goal["user_id"] == user_id]

    result = []
    for goal in user_goals:
        goal_milestones = [ms for ms in db["milestones"] if ms["goal_id"] == goal["id"]]
        goal_with_milestones = {**goal, "milestones": goal_milestones}
        result.append(goal_with_milestones)

    return result

@router.post("/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED, summary="Create a New Goal")
async def create_goal(goal_in: GoalCreate, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Create a new goal for the user. Request body includes title, description,
    target_date, and an optional list of initial milestones.
    """
    new_goal_id = get_next_id("goals")
    new_goal = {
        "id": new_goal_id,
        "user_id": current_user["id"],
        "title": goal_in.title,
        "description": goal_in.description,
        "target_date": goal_in.target_date,
        "created_at": datetime.utcnow()
    }
    db["goals"].append(new_goal)

    created_milestones = []
    for milestone_in in goal_in.milestones:
        new_milestone = {
            "id": get_next_id("milestones"),
            "goal_id": new_goal_id,
            "title": milestone_in.title,
            "description": milestone_in.description,
            "is_complete": False
        }
        db["milestones"].append(new_milestone)
        created_milestones.append(new_milestone)

    return {**new_goal, "milestones": created_milestones}

@router.put("/milestones/{milestone_id}/toggle", response_model=MilestoneOut, summary="Toggle Milestone Completion")
async def toggle_milestone_completion(milestone_id: int, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Mark a specific milestone as complete or incomplete.
    This operation is idempotent.
    """
    milestone = next((ms for ms in db["milestones"] if ms["id"] == milestone_id), None)
    if not milestone:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Milestone not found")

    # Authorization check: ensure the milestone belongs to a goal owned by the current user
    goal = next((g for g in db["goals"] if g["id"] == milestone["goal_id"]), None)
    if not goal or goal["user_id"] != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this milestone")

    milestone["is_complete"] = not milestone["is_complete"]
    return milestone

@router.get("/habits", response_model=List[HabitOut], summary="Get All Habits for the Week")
async def get_habits(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve all habits and their completion status for the current week
    for the authenticated user.
    """
    user_id = current_user["id"]
    user_habits = [habit for habit in db["habits"] if habit["user_id"] == user_id]

    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    result = []
    for habit in user_habits:
        completions = [
            comp for comp in db["habit_completions"]
            if comp["habit_id"] == habit["id"] and start_of_week <= comp["date"] <= end_of_week
        ]
        habit_with_completions = {**habit, "completions_this_week": completions}
        result.append(habit_with_completions)

    return result