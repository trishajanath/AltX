import os
from typing import List, Dict, Any

import httpx
from fastapi import APIRouter, HTTPException, status, Path

# In a real application, these models would be in a separate `models.py` file.
# For this self-contained example, they are included here.
# --- Start of models ---
from pydantic import BaseModel, EmailStr, Field


class Video(BaseModel):
    id: int
    title: str
    url: str
    description: str


class Achievement(BaseModel):
    id: int
    name: str
    description: str
    icon_url: str


class ContactMessage(BaseModel):
    name: str = Field(..., min_length=2, description="Sender's name")
    email: EmailStr = Field(..., description="Sender's email address")
    message: str = Field(..., min_length=10, description="The message content")


class ContactResponse(BaseModel):
    status: str
    detail: str


class PlayerStats(BaseModel):
    """
    A simplified model representing the expected structure from the external API.
    This would be adjusted to match the actual external API's response.
    """
    playerName: str
    platform: str
    stats: Dict[str, Any]


# --- End of models ---


# --- In-Memory Storage ---
# This acts as a simple, non-persistent database for the application.
db_videos: List[Video] = [
    Video(id=1, title="Epic Victory Royale #1", url="https://example.com/video/1",
          description="A crazy build battle finish with a clutch snipe."),
    Video(id=2, title="Funny Fails & Bloopers", url="https://example.com/video/2",
          description="A compilation of the most hilarious moments and fails."),
    Video(id=3, title="Advanced Building Techniques", url="https://example.com/video/3",
          description="Learn how to build like a pro with these tips and tricks."),
]

db_achievements: List[Achievement] = [
    Achievement(id=1, name="First Blood", description="Achieve the first elimination in a match.",
                icon_url="https://example.com/icons/first_blood.png"),
    Achievement(id=2, name="Victory Royale", description="Be the last player standing.",
                icon_url="https://example.com/icons/victory_royale.png"),
    Achievement(id=3, name="Sky High", description="Eliminate a player while they are in a vehicle.",
                icon_url="https://example.com/icons/sky_high.png"),
]

db_contact_messages: List[ContactMessage] = []

# --- API Router Setup ---
# All routes defined here will be prefixed with /api/v1.
router = APIRouter(
    prefix="/api/v1",
    tags=["v1"],
)

# --- External API Configuration ---
# In a real app, use environment variables for sensitive data like API keys.
FORTNITE_API_URL = "https://fortnite-api.com/v2/stats/br/v2"
# FORTNITE_API_KEY = os.getenv("FORTNITE_API_KEY", "your_default_api_key_here")
# For this example, we will mock the API call as a key is required.


# --- Route Implementations ---

@router.get(
    "/videos",
    response_model=List[Video],
    summary="Retrieve all gameplay videos",
    description="Provides a list of all curated gameplay videos available.",
)
async def get_videos():
    """
    Retrieve a list of all gameplay videos.
    """
    return db_videos


@router.get(
    "/achievements",
    response_model=List[Achievement],
    summary="Retrieve all achievements",
    description="Provides a list of all possible achievements in the game.",
)
async def get_achievements():
    """
    Retrieve a list of all achievements.
    """
    return db_achievements


@router.get(
    "/stats/{playerName}",
    response_model=PlayerStats,
    summary="Get player stats from Fortnite API",
    description="A proxy endpoint to fetch player stats from an external Fortnite API.",
    responses={
        404: {"description": "Player not found"},
        503: {"description": "External API service is unavailable"},
    },
)
async def get_player_stats(
    playerName: str = Path(..., min_length=3, max_length=16, description="The player's Epic Games name")
):
    """
    Proxy endpoint to fetch player stats from an external Fortnite API.

    This endpoint makes a server-to-server request to an external service
    to retrieve player statistics.
    """
    # NOTE: The public Fortnite API requires an API key in the headers.
    # This example simulates the call and potential errors.
    # In a real implementation, you would uncomment the httpx block.

    # --- Start of Mocked Response ---
    if playerName.lower() == "ninja":
        return PlayerStats(
            playerName=playerName,
            platform="pc",
            stats={
                "kills": 123456,
                "wins": 7890,
                "matchesPlayed": 9999,
                "winRate": 78.9,
            }
        )
    elif playerName.lower() == "unknownplayer":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Player '{playerName}' not found in the external service."
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The external Fortnite API service is currently unavailable. Please try again later."
        )
    # --- End of Mocked Response ---

    # --- Real Implementation Example (requires httpx and a valid API key) ---
    # headers = {"Authorization": FORTNITE_API_KEY}
    # params = {"name": playerName}
    #
    # async with httpx.AsyncClient() as client:
    #     try:
    #         response = await client.get(FORTNITE_API_URL, params=params, headers=headers, timeout=10.0)
    #
    #         if response.status_code == 200:
    #             data = response.json().get("data", {})
    #             # Adapt the following lines to match the actual API response structure
    #             return PlayerStats(
    #                 playerName=data.get("account", {}).get("name"),
    #                 platform="pc", # This might need to be determined or passed as a parameter
    #                 stats=data.get("stats", {}).get("all", {}).get("overall", {})
    #             )
    #         elif response.status_code == 404:
    #             raise HTTPException(
    #                 status_code=status.HTTP_404_NOT_FOUND,
    #                 detail=f"Player '{playerName}' not found in the external service."
    #             )
    #         else:
    #             # Handle other potential errors from the external API (e.g., 401, 403, 500)
    #             raise HTTPException(
    #                 status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    #                 detail=f"External API returned an error: {response.status_code}"
    #             )
    #
    #     except httpx.RequestError as exc:
    #         # Handle network-related errors (e.g., timeout, connection error)
    #         raise HTTPException(
    #             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    #             detail=f"Failed to connect to the external Fortnite API: {exc}"
    #         )
    # --- End of Real Implementation Example ---


@router.post(
    "/contact",
    response_model=ContactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a contact form message",
    description="Accepts a message from the contact form and stores it in-memory.",
)
async def submit_contact_form(message: ContactMessage):
    """
    Submit a message from the contact form.

    - **name**: The name of the person sending the message.
    - **email**: The email address of the sender.
    - **message**: The content of the message.
    """
    # In a real application, you would save this to a database,
    # send an email, or create a ticket in a support system.
    db_contact_messages.append(message)
    print(f"Received new contact message from {message.name} ({message.email})")
    return {
        "status": "success",
        "detail": "Your message has been received successfully."
    }