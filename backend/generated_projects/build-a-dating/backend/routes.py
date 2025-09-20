```python
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from typing import List

from .models import Profile, SwipeRequest, SwipeResponse, Match

#  In-Memory Data Store (No Database) 
# This dictionary will act as our database for this demonstration.
# In a real application, you would use a proper database like PostgreSQL or MongoDB.
db = {
    "profiles": {},
    "swipes": {}, # E.g., {swiper_id: {swiped_id: action}}
    "matches": {}, # E.g., {user_id: {matched_user_id, ...}}
}

#  Mock Data 
# Let's pre-populate our "database" with some mock profiles.
def setup_mock_data():
    """Initializes the in-memory database with mock profiles."""
    profiles_data = [
        {"name": "Alice", "age": 28, "bio": "Lover of hiking and sunny days.", "interests": ["hiking", "reading", "coffee"], "profile_picture_url": "https://images.unsplash.com/photo-1520466809213-7b9a56adcd45"},
        {"name": "Bob", "age": 32, "bio": "Software engineer and aspiring chef.", "interests": ["coding", "cooking", "movies"], "profile_picture_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d"},
        {"name": "Charlie", "age": 25, "bio": "Musician looking for someone to jam with.", "interests": ["guitar", "live music", "dogs"], "profile_picture_url": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6"},
        {"name": "Diana", "age": 30, "bio": "Art enthusiast and travel addict.", "interests": ["art", "travel", "photography"], "profile_picture_url": "https://images.unsplash.com/photo-1517841905240-472988babdf9"},
    ]
    for p_data in profiles_data:
        profile_id = uuid.uuid4()
        db["profiles"][profile_id] = Profile(id=profile_id, **p_data)
    
    # Create a "current user" for the simulation. In a real app, this would come from an auth system.
    global CURRENT_USER_ID
    CURRENT_USER_ID = uuid.uuid4()
    current_user_profile = Profile(
        id=CURRENT_USER_ID,
        name="User (You)",
        age=29,
        bio="This is your simulated profile.",
        interests=["fastapi", "python", "testing"],
        profile_picture_url="https://images.unsplash.com/photo-1554151228-14d9def656e4"
    )
    db["profiles"][CURRENT_USER_ID] = current_user_profile
    print(f"
✅ Mock data initialized. Current simulated user ID: {CURRENT_USER_ID}")

# Call setup function to populate data on module load
setup_mock_data()

#  API Router 
router = APIRouter()

@router.get(
    "/profiles/queue",
    response_model=List[Profile],
    summary="Get Dating Profile Queue",
    description="Fetches a list of profiles for the current user to swipe on. Excludes profiles already swiped on and the user's own profile."
)
def get_profile_queue():
    """
    Retrieves a list of potential matches for the current user.
    
    Logic:
    1. Gets the set of profile IDs the current user has already swiped on.
    2. Filters the main profile list to exclude the current user and those already swiped.
    3. Returns the filtered list.
    """
    swiped_ids = set(db["swipes"].get(CURRENT_USER_ID, {}).keys())
    
    queue = [
        profile for profile_id, profile in db["profiles"].items()
        if profile_id != CURRENT_USER_ID and profile_id not in swiped_ids
    ]
    return queue

@router.post(
    "/profiles/{profile_id}/swipe",
    response_model=SwipeResponse,
    summary="Swipe on a Profile",
    description="Allows the current user to 'like' or 'pass' on another profile. Checks for a mutual match."
)
def swipe_on_profile(profile_id: uuid.UUID, swipe_request: SwipeRequest):
    """
    Records a swipe action from the current user to another profile.

    Logic:
    1. Validate that the target profile exists and is not the current user.
    2. Record the swipe action (like/pass) in our in-memory store.
    3. If the action is a 'like', check if the other user has also 'liked' the current user.
    4. If it's a mutual 'like', a match is created and stored for both users.
    5. Return a response indicating success and whether a match was made.
    """
    if profile_id == CURRENT_USER_ID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot swipe on your own profile."
        )

    target_profile = db["profiles"].get(profile_id)
    if not target_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Profile with ID {profile_id} not found."
        )

    # Record the swipe
    if CURRENT_USER_ID not in db["swipes"]:
        db["swipes"][CURRENT_USER_ID] = {}
    db["swipes"][CURRENT_USER_ID][profile_id] = swipe_request.action

    # Check for a match if the action was a 'like'
    if swipe_request.action == "like":
        # Check if the other user has liked us back
        other_user_swipes = db["swipes"].get(profile_id, {})
        if other_user_swipes.get(CURRENT_USER_ID) == "like":
            # It's a match!
            if CURRENT_USER_ID not in db["matches"]:
                db["matches"][CURRENT_USER_ID] = set()
            if profile_id not in db["matches"]:
                db["matches"][profile_id] = set()
            
            db["matches"][CURRENT_USER_ID].add(profile_id)
            db["matches"][profile_id].add(CURRENT_USER_ID)
            
            match_details = Match(
                matched_profile=target_profile,
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            return SwipeResponse(is_match=True, match_details=match_details)

    return SwipeResponse(is_match=False)

@router.get(
    "/matches",
    response_model=List[Match],
    summary="Get My Matches",
    description="Retrieves a list of all profiles that the current user has successfully matched with."
)
def get_my_matches():
    """
    Returns a list of all successful matches for the current user.
    """
    user_match_ids = db["matches"].get(CURRENT_USER_ID, set())
    
    matches_list = []
    for match_id in user_match_ids:
        matched_profile = db["profiles"].get(match_id)
        if matched_profile:
            matches_list.append(Match(
                matched_profile=matched_profile,
                timestamp=datetime.now(timezone.utc).isoformat() # Note: Timestamp is not stored in this demo
            ))
            
    return matches_list
```