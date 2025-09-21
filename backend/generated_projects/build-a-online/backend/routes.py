import io
import wave
from typing import List

from fastapi import APIRouter, HTTPException, Path, status
from fastapi.responses import StreamingResponse

from .models import Song

#  Mock Database 
# In a real application, this data would come from a database.
# For this example, we use a simple in-memory list of dictionaries.
# The 'id' is crucial for fetching specific items.

MOCK_SONGS_DATA = [
    {
        "id": 1,
        "title": "Cosmic Drift",
        "artist": "Galaxy Riders",
        "album": "Starlight Echoes",
        "duration_seconds": 245,
        "album_art_url": "https://picsum.photos/seed/1/400",
    },
    {
        "id": 2,
        "title": "Ocean Breathes",
        "artist": "Tidal Wave",
        "album": "Deep Blue",
        "duration_seconds": 182,
        "album_art_url": "https://picsum.photos/seed/2/400",
    },
    {
        "id": 3,
        "title": "Midnight City Run",
        "artist": "Neon Ghosts",
        "album": "Cyber Dreams",
        "duration_seconds": 312,
        "album_art_url": "https://picsum.photos/seed/3/400",
    },
    {
        "id": 4,
        "title": "Forest Lullaby",
        "artist": "Whispering Willows",
        "album": "Ancient Woods",
        "duration_seconds": 220,
        "album_art_url": "https://picsum.photos/seed/4/400",
    },
    {
        "id": 5,
        "title": "Starlight Echoes",
        "artist": "Galaxy Riders",
        "album": "Starlight Echoes",
        "duration_seconds": 198,
        "album_art_url": "https://picsum.photos/seed/1/400",
    },
]

# Convert the raw data into Pydantic models for type safety and validation
songs_db: List[Song] = [Song(**data) for data in MOCK_SONGS_DATA]

#  API Router 
router = APIRouter()

@router.get(
    "/songs",
    response_model=List[Song],
    summary="Get a list of all available songs",
    tags=["Music"],
)
def get_all_songs() -> List[Song]:
    """
    Retrieves a list of all songs available in the mock database.
    This endpoint is useful for populating the main music library view in the frontend.
    """
    return songs_db

@router.get(
    "/songs/{song_id}",
    response_model=Song,
    summary="Get details for a specific song",
    tags=["Music"],
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Song not found"},
    },
)
def get_song_by_id(
    song_id: int = Path(..., description="The ID of the song to retrieve", gt=0)
) -> Song:
    """
    Retrieves detailed information for a single song by its unique ID.
    If the song with the specified ID does not exist, a 404 Not Found error is returned.
    """
    song = next((s for s in songs_db if s.id == song_id), None)
    if song is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Song with ID {song_id} not found.",
        )
    return song

def generate_silent_wav(duration_seconds: int) -> io.BytesIO:
    """
    Dynamically generates a silent WAV audio stream of a given duration.
    This is a placeholder to make the stream endpoint functional without actual audio files.
    """
    sample_rate = 44100  # CD quality
    num_channels = 1  # Mono
    sampwidth = 2  # 16-bit
    num_frames = duration_seconds * sample_rate

    audio_data = b'\x00' * (num_frames * num_channels * sampwidth)
    
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_data)
    
    buffer.seek(0)
    return buffer

@router.get(
    "/stream/{song_id}",
    summary="Stream an audio file for a song",
    tags=["Music"],
    responses={
        status.HTTP_200_OK: {
            "content": {"audio/wav": {}},
            "description": "A streaming audio response.",
        },
        status.HTTP_404_NOT_FOUND: {"description": "Song not found"},
    },
)
def stream_song(
    song_id: int = Path(..., description="The ID of the song to stream", gt=0)
):
    """
    Provides a streaming response for a song's audio content.
    
    This endpoint simulates streaming an audio file. In a real-world scenario,
    this would use `FileResponse` to stream a static file from disk or proxy a
    stream from a cloud storage service like S3.

    For this demonstration, it generates a silent WAV file in memory with the correct
    duration specified in the song's metadata, proving the streaming mechanism works.
    """
    song = next((s for s in songs_db if s.id == song_id), None)
    if song is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Song with ID {song_id} not found.",
        )

    # Generate silent audio for demonstration
    silent_audio_buffer = generate_silent_wav(song.duration_seconds)
    
    return StreamingResponse(
        silent_audio_buffer,
        media_type="audio/wav",
        headers={"Content-Length": str(len(silent_audio_buffer.getbuffer()))}
    )