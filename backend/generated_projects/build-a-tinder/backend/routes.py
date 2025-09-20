```python
import uuid
from fastapi import APIRouter, HTTPException, status, Query, Body
from typing import List
from datetime import datetime

from . import models

#  Application Router Setup 
router = APIRouter(
    prefix="/api/v1",
    tags=["Dating App"]
)

#  In-Memory Database (for demonstration purposes) 

# 
🛡️ SECURITY NOTE: This is a simple in-memory store for demonstration.
# In a production environment, this MUST be replaced with a robust database system
# like PostgreSQL with an ORM like SQLAlchemy to ensure data persistence,
# scalability, and security. Sensitive data should be encrypted at rest.

db = {
    "profiles": {},
    "swipes": [],
    "matches": []
}

# Pre-populate with some dummy data for easier testing
def create_dummy_data():
    dummy_profiles = [
        models.UserProfileCreate(name="Alice", age=28, gender=models.Gender.WOMAN, bio="Software engineer and dog lover.", interests=["coding", "hiking", "dogs"], profile_picture_urls=["http://example.com/alice.jpg"]),
        models.UserProfileCreate(name="Bob", age=30, gender=models.Gender.MAN, bio="Adventurous soul seeking new experiences.", interests=["travel", "photography", "cooking"], profile_picture_urls=["http://example.com/bob.jpg"]),
        models.UserProfileCreate(name="Charlie", age=25, gender=models.Gender.NON_BINARY, bio="Artist and musician.", interests=["painting", "guitar", "concerts"], profile_picture_urls=["http://example.com/charlie.jpg"]),
        models.UserProfileCreate(name="Diana", age=32, gender=models.Gender.WOMAN, bio="Fitness enthusiast and bookworm.", interests=["running", "yoga", "reading"], profile_picture_urls=["http://example.com/diana.jpg"])
    ]
    for profile_data in dummy_profiles:
        profile_id = uuid.uuid4()
        profile = models.UserProfile(
            id=profile_id,
            created_at=datetime.utcnow(),
            **profile_data.model_dump()
        )
        db["profiles"][profile_id] = profile

# Call this function to populate the DB when the module is loaded
create_dummy_data()

#  API Endpoints 

@router.post("/profiles", response_model=models.UserProfile, status_code=status.HTTP_201_CREATED)
async def create_user_profile(profile_data: models.UserProfileCreate):
    """
    Creates a new user profile.

    This endpoint takes user profile data, validates it, assigns a unique ID
    and a creation timestamp, and stores it.
    """
    profile_id = uuid.uuid4()
    new_profile = models.UserProfile(
        id=profile_id,
        created_at=datetime.utcnow(),
        **profile_data.model_dump()
    )
    db["profiles"][profile_id] = new_profile
    return new_profile

@router.get("/profiles", response_model=List[models.UserProfile])
async def get_potential_matches(current_user_id: uuid.UUID):
    """
    Retrieves a list of potential matches for the current user.

    It filters out the current user's own profile and any profiles they have
    already swiped on to create a "swipe deck".
    """
    if current_user_id not in db["profiles"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Current user profile not found")

    swiped_ids = {s['swiped_id'] for s in db['swipes'] if s['swiper_id'] == current_user_id}
    
    potential_matches = [
        profile for profile_id, profile in db["profiles"].items()
        if profile_id != current_user_id and profile_id not in swiped_ids
    ]
    
    return potential_matches

@router.get("/profiles/{profile_id}", response_model=models.UserProfile)
async def get_profile_by_id(profile_id: uuid.UUID):
    """
    Retrieves a single user profile by its unique ID.
    """
    profile = db["profiles"].get(profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile

@router.post("/swipes", response_model=models.SwipeResponse)
async def swipe_on_profile(swipe_action: models.SwipeAction):
    """
    Records a swipe action (left or right) and checks for a mutual match.

    - Validates that users exist and are not swiping on themselves.
    - Records the swipe action.
    - If the swipe is 'right', it checks if the other user has also swiped right.
    - If a mutual 'right' swipe exists, a match is created.
    """
    swiper_id = swipe_action.swiper_id
    swiped_id = swipe_action.swiped_id

    if swiper_id == swiped_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot swipe on your own profile")

    if swiper_id not in db["profiles"] or swiped_id not in db["profiles"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or both user profiles not found")

    # Record the swipe
    db["swipes"].append(swipe_action.model_dump())

    # Check for a match if it was a right swipe
    if swipe_action.direction == models.SwipeDirection.RIGHT:
        # Check if the other person has swiped right on the current user
        reciprocal_swipe = any(
            s['swiper_id'] == swiped_id and 
            s['swiped_id'] == swiper_id and 
            s['direction'] == models.SwipeDirection.RIGHT 
            for s in db['swipes']
        )
        
        if reciprocal_swipe:
            # Check if a match doesn't already exist
            match_exists = any(
                (m['user1_id'] == swiper_id and m['user2_id'] == swiped_id) or
                (m['user1_id'] == swiped_id and m['user2_id'] == swiper_id)
                for m in db['matches']
            )
            if not match_exists:
                new_match = {
                    "match_id": uuid.uuid4(),
                    "user1_id": swiper_id,
                    "user2_id": swiped_id,
                    "matched_at": datetime.utcnow()
                }
                db["matches"].append(new_match)
                return models.SwipeResponse(is_match=True, match_id=new_match["match_id"])

    return models.SwipeResponse(is_match=False)

@router.get("/matches/{user_id}", response_model=List[models.Match])
async def get_user_matches(user_id: uuid.UUID):
    """
    Retrieves a list of all matches for a given user.
    """
    if user_id not in db["profiles"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User profile not found")

    user_matches = []
    for match in db["matches"]:
        if match["user1_id"] == user_id or match["user2_id"] == user_id:
            # Determine the other user's ID
            other_user_id = match["user2_id"] if match["user1_id"] == user_id else match["user1_id"]
            
            # Get the other user's full profile
            matched_profile = db["profiles"].get(other_user_id)
            if matched_profile:
                # Construct the full Match object for the response
                match_response = models.Match(
                    match_id=match["match_id"],
                    user1_id=match["user1_id"],
                    user2_id=match["user2_id"],
                    matched_at=match["matched_at"],
                    matched_profile=matched_profile
                )
                user_matches.append(match_response)

    return user_matches
```