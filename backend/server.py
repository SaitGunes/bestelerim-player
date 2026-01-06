from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from pathlib import Path
from urllib.parse import quote

# Create the main app
app = FastAPI(title="Bestelerim Media Player")

# GitHub config
GITHUB_REPO = "SaitGunes/bestelerim"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

# Models
class MediaFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    display_name: str
    url: str
    type: str
    size: Optional[int] = None

class MediaResponse(BaseModel):
    files: List[MediaFile]
    repo: str
    total: int

# File extensions
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
    name = Path(filename).stem
    name = name.replace('-', ' ').replace('_', ' ')
    return name.title()

@app.get("/")
async def root():
    return {"message": "Bestelerim Media Player API", "status": "ok"}

@app.get("/api/media", response_model=MediaResponse)
async def get_media_files():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents",
                headers={"Accept": "application/vnd.github.v3+json"},
                timeout=30.0
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
                        encoded_name = quote(filename)
                        raw_url = f"{GITHUB_RAW_BASE}/{GITHUB_REPO}/main/{encoded_name}"
                        
                        media_files.append(MediaFile(
                            name=filename,
                            display_name=format_display_name(filename),
                            url=raw_url,
                            type=media_type,
                            size=item.get("size")
                        ))
            
            return MediaResponse(files=media_files, repo=GITHUB_REPO, total=len(media_files))
            
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"GitHub error: {str(e)}")

# CORS - tüm originlere izin ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
