from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import httpx
import os
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from pathlib import Path
from urllib.parse import quote
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI(title="Bestelerim Media Player")

GITHUB_REPO = "SaitGunes/bestelerim"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

# MongoDB
MONGO_URL = os.environ.get("MONGO_URL", "")
client = None
db = None

@app.on_event("startup")
async def startup_db():
    global client, db
    if MONGO_URL:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client.bestelerim

@app.on_event("shutdown")
async def shutdown_db():
    global client
    if client:
        client.close()

class MediaFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    display_name: str
    url: str
    type: str
    size: Optional[int] = None
    likes: int = 0

class MediaResponse(BaseModel):
    files: List[MediaFile]
    repo: str
    total: int

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

PLAYER_HTML = '''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sait Gunes - Bestelerim</title>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Inter:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%); color: #fff; min-height: 100vh; }
        .container { max-width: 900px; margin: 0 auto; padding: 40px 20px 140px; }
        .artist-section { display: flex; align-items: center; gap: 24px; margin-bottom: 40px; padding: 30px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 20px; }
        .artist-photo { width: 120px; height: 120px; border-radius: 50%; object-fit: cover; border: 3px solid #6366f1; box-shadow: 0 0 30px rgba(99, 102, 241, 0.4); }
        .artist-info h1 { font-family: 'Manrope', sans-serif; font-size: 2.2rem; font-weight: 800; background: linear-gradient(90deg, #fff, #a5b4fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }
        .artist-info .tagline { color: #a5b4fc; font-size: 1.1rem; margin-bottom: 4px; }
        .song-list { display: flex; flex-direction: column; gap: 12px; }
        .song-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 16px 20px; cursor: pointer; transition: all 0.3s ease; display: flex; align-items: center; gap: 16px; }
        .song-card:hover { background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.3); transform: translateX(8px); }
        .song-card.active { background: rgba(99, 102, 241, 0.2); border-color: #6366f1; }
        .song-icon { width: 48px; height: 48px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; }
        .song-info { flex: 1; }
        .song-title { font-weight: 600; font-size: 1.1rem; }
        .song-type { color: #888; font-size: 0.85rem; margin-top: 2px; }
        .like-btn { background: none; border: none; cursor: pointer; font-size: 1.2rem; padding: 8px 12px; border-radius: 8px; transition: all 0.2s; display: flex; align-items: center; gap: 6px; color: #888; }
        .like-btn:hover { background: rgba(255,255,255,0.1); color: #f87171; }
        .like-btn.liked { color: #f87171; }
        .like-count { font-size: 0.9rem; }
        .player-bar { position: fixed; bottom: 0; left: 0; right: 0; background: rgba(10, 10, 10, 0.95); backdrop-filter: blur(20px); border-top: 1px solid rgba(255,255,255,0.1); padding: 16px 20px; }
        .player-content { max-width: 900px; margin: 0 auto; }
        .now-playing { font-size: 0.9rem; color: #a5b4fc; margin-bottom: 12px; text-align: center; }
        audio { width: 100%; height: 40px; border-radius: 8px; }
        .controls { display: flex; gap: 12px; justify-content: center; margin-top: 12px; }
        .btn { background: rgba(255,255,255,0.1); border: none; color: #fff; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 1rem; transition: all 0.2s; }
        .btn:hover { background: rgba(99, 102, 241, 0.3); }
        .btn-play { background: #6366f1; padding: 10px 30px; }
        .btn-play:hover { background: #5558e3; }
        .loading { text-align: center; padding: 60px; color: #888; }
        @media (max-width: 600px) { .artist-section { flex-direction: column; text-align: center; padding: 24px; } .artist-photo { width: 100px; height: 100px; } .artist-info h1 { font-size: 1.8rem; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="artist-section">
            <img src="https://customer-assets.emergentagent.com/job_audio-hub-583/artifacts/7w97rm3o_AFEECBE7-E628-4369-9F8D-C39F9A7EA4A3.png" alt="Sait Gunes" class="artist-photo">
            <div class="artist-info"><h1>Sait Gunes</h1><p class="tagline">Bestelerim</p></div>
        </div>
        <div id="songs" class="song-list"><div class="loading">Sarkilar yukleniyor...</div></div>
    </div>
    <div class="player-bar">
        <div class="player-content">
            <div class="now-playing" id="nowPlaying">Sarki secin</div>
            <audio id="audio" controls></audio>
            <div class="controls"><button class="btn" onclick="playPrev()">Onceki</button><button class="btn btn-play" onclick="togglePlay()">Oynat</button><button class="btn" onclick="playNext()">Sonraki</button></div>
        </div>
    </div>
    <script>
        let songs = [], currentIndex = -1;
        const audio = document.getElementById('audio'), nowPlaying = document.getElementById('nowPlaying');
        let likedSongs = JSON.parse(localStorage.getItem('likedSongs') || '[]');
        
        async function loadSongs() { 
            try { 
                const res = await fetch('/api/media'); 
                const data = await res.json(); 
                songs = data.files; 
                renderSongs(); 
            } catch (e) { 
                document.getElementById('songs').innerHTML = '<div class="loading">Yukleme hatasi</div>'; 
            } 
        }
        
        function renderSongs() { 
            const container = document.getElementById('songs'); 
            if (songs.length === 0) { 
                container.innerHTML = '<div class="loading">Henuz sarki yok</div>'; 
                return; 
            } 
            container.innerHTML = songs.map((song, i) => {
                const isLiked = likedSongs.includes(song.name);
                return '<div class="song-card" id="song-'+i+'"><div class="song-icon" onclick="playSong('+i+')">'+(song.type === 'audio' ? '🎵' : '🎬')+'</div><div class="song-info" onclick="playSong('+i+')"><div class="song-title">'+song.display_name+'</div><div class="song-type">'+(song.type === 'audio' ? 'Ses Dosyasi' : 'Video')+'</div></div><button class="like-btn '+(isLiked ? 'liked' : '')+'" onclick="toggleLike(\''+song.name+'\', '+i+')"><span>❤</span><span class="like-count" id="likes-'+i+'">'+song.likes+'</span></button></div>';
            }).join(''); 
        }
        
        async function toggleLike(songName, index) {
            const isLiked = likedSongs.includes(songName);
            try {
                const res = await fetch('/api/like/'+encodeURIComponent(songName), { 
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({action: isLiked ? 'unlike' : 'like'})
                });
                const data = await res.json();
                document.getElementById('likes-'+index).textContent = data.likes;
                
                if (isLiked) {
                    likedSongs = likedSongs.filter(n => n !== songName);
                } else {
                    likedSongs.push(songName);
                }
                localStorage.setItem('likedSongs', JSON.stringify(likedSongs));
                
                const btn = document.querySelectorAll('.like-btn')[index];
                btn.classList.toggle('liked');
            } catch(e) { console.error(e); }
        }
        
        function playSong(index) { 
            document.querySelectorAll('.song-card').forEach(c => c.classList.remove('active')); 
            document.getElementById('song-'+index).classList.add('active'); 
            currentIndex = index; 
            const song = songs[index]; 
            audio.src = song.url; 
            audio.play(); 
            nowPlaying.textContent = song.display_name; 
        }
        
        function togglePlay() { 
            if (currentIndex === -1 && songs.length > 0) playSong(0); 
            else if (audio.paused) audio.play(); 
            else audio.pause(); 
        }
        
        function playNext() { 
            if (songs.length === 0) return; 
            playSong((currentIndex + 1) % songs.length); 
        }
        
        function playPrev() { 
            if (songs.length === 0) return; 
            playSong(currentIndex <= 0 ? songs.length - 1 : currentIndex - 1); 
        }
        
        audio.addEventListener('ended', playNext); 
        loadSongs();
    </script>
</body>
</html>'''

@app.get("/", response_class=HTMLResponse)
async def home():
    return PLAYER_HTML

@app.get("/api/media", response_model=MediaResponse)
async def get_media_files():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents", headers={"Accept": "application/vnd.github.v3+json"}, timeout=30.0)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail="GitHub API error")
            contents = response.json()
            media_files = []
            for item in contents:
                if item.get("type") == "file":
                    filename = item.get("name", "")
                    media_type = get_media_type(filename)
                    if media_type:
                        likes = 0
                        if db:
                            like_doc = await db.likes.find_one({"song": filename})
                            if like_doc:
                                likes = like_doc.get("count", 0)
                        media_files.append(MediaFile(name=filename, display_name=format_display_name(filename), url=f"{GITHUB_RAW_BASE}/{GITHUB_REPO}/main/{quote(filename)}", type=media_type, size=item.get("size"), likes=likes))
            return MediaResponse(files=media_files, repo=GITHUB_REPO, total=len(media_files))
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"GitHub error: {str(e)}")

@app.post("/api/like/{song_name}")
async def toggle_like(song_name: str, body: dict):
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")
    
    action = body.get("action", "like")
    
    if action == "like":
        await db.likes.update_one(
            {"song": song_name},
            {"$inc": {"count": 1}},
            upsert=True
        )
    else:
        await db.likes.update_one(
            {"song": song_name},
            {"$inc": {"count": -1}},
            upsert=True
        )
    
    doc = await db.likes.find_one({"song": song_name})
    count = doc.get("count", 0) if doc else 0
    if count < 0:
        await db.likes.update_one({"song": song_name}, {"$set": {"count": 0}})
        count = 0
    
    return {"likes": count}

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
