from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import httpx
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# GitHub config
GITHUB_REPO = "SaitGunes/bestelerim"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

# Models
class MediaFile(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    display_name: str
    url: str
    type: str  # audio or video
    size: Optional[int] = None
    
class MediaResponse(BaseModel):
    files: List[MediaFile]
    repo: str
    total: int

class PlayStats(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_name: str
    play_count: int = 0
    last_played: Optional[str] = None

# Audio/Video file extensions
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'}
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi', '.mkv'}

def get_media_type(filename: str) -> Optional[str]:
    ext = Path(filename).suffix.lower()
    if ext in AUDIO_EXTENSIONS:
        return "audio"
    elif ext in VIDEO_EXTENSIONS:
        return "video"
    return None

def format_display_name(filename: str) -> str:
    """Convert filename to display name"""
    name = Path(filename).stem
    # Replace hyphens and underscores with spaces
    name = name.replace('-', ' ').replace('_', ' ')
    # Capitalize first letter of each word
    name = name.title()
    return name

@api_router.get("/")
async def root():
    return {"message": "Bestelerim Media Player API"}

@api_router.get("/media", response_model=MediaResponse)
async def get_media_files():
    """Fetch media files from GitHub repository"""
    try:
        async with httpx.AsyncClient() as client:
            # Fetch repository contents
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents",
                headers={"Accept": "application/vnd.github.v3+json"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="GitHub API error")
            
            contents = response.json()
            media_files = []
            
            for item in contents:
                if item.get("type") == "file":
                    filename = item.get("name", "")
                    media_type = get_media_type(filename)
                    
                    if media_type:
                        # Create raw URL for streaming
                        encoded_name = quote(filename)
                        raw_url = f"{GITHUB_RAW_BASE}/{GITHUB_REPO}/main/{encoded_name}"
                        
                        media_file = MediaFile(
                            name=filename,
                            display_name=format_display_name(filename),
                            url=raw_url,
                            type=media_type,
                            size=item.get("size")
                        )
                        media_files.append(media_file)
            
            return MediaResponse(
                files=media_files,
                repo=GITHUB_REPO,
                total=len(media_files)
            )
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch from GitHub: {str(e)}")

@api_router.post("/play/{file_name}")
async def record_play(file_name: str):
    """Record a play event for analytics"""
    now = datetime.now(timezone.utc).isoformat()
    
    result = await db.play_stats.find_one_and_update(
        {"file_name": file_name},
        {
            "$inc": {"play_count": 1},
            "$set": {"last_played": now}
        },
        upsert=True,
        return_document=True,
        projection={"_id": 0}
    )
    
    return {"success": True, "stats": result}

@api_router.get("/stats")
async def get_stats():
    """Get play statistics"""
    stats = await db.play_stats.find({}, {"_id": 0}).to_list(100)
    return {"stats": stats}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
