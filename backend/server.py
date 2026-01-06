from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import httpx
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from pathlib import Path
from urllib.parse import quote

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

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bestelerim - Müzik Oynatıcı</title>
    <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&family=Inter:wght@400;500&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
            color: #fff;
            min-height: 100vh;
        }
        .container { max-width: 900px; margin: 0 auto; padding: 40px 20px 140px; }
        h1 {
            font-family: 'Manrope', sans-serif;
            font-size: 2.5rem;
            margin-bottom: 8px;
            background: linear-gradient(90deg, #fff, #a5b4fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .subtitle { color: #888; margin-bottom: 40px; }
        .song-list { display: flex; flex-direction: column; gap: 12px; }
        .song-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 16px 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .song-card:hover {
            background: rgba(99, 102, 241, 0.15);
            border-color: rgba(99, 102, 241, 0.3);
            transform: translateX(8px);
        }
        .song-card.active {
            background: rgba(99, 102, 241, 0.2);
            border-color: #6366f1;
        }
        .song-icon {
            width: 48px; height: 48px;
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 20px;
        }
        .song-info { flex: 1; }
        .song-title { font-weight: 600; font-size: 1.1rem; }
        .song-type { color: #888; font-size: 0.85rem; margin-top: 2px; }
        .player-bar {
            position: fixed;
            bottom: 0; left: 0; right: 0;
            background: rgba(10, 10, 10, 0.95);
            backdrop-filter: blur(20px);
            border-top: 1px solid rgba(255,255,255,0.1);
            padding: 16px 20px;
        }
        .player-content { max-width: 900px; margin: 0 auto; }
        .now-playing { font-size: 0.9rem; color: #a5b4fc; margin-bottom: 12px; text-align: center; }
        audio { width: 100%; height: 40px; border-radius: 8px; }
        audio::-webkit-media-controls-panel { background: #1a1a2e; }
        .controls { display: flex; gap: 12px; justify-content: center; margin-top: 12px; }
        .btn {
            background: rgba(255,255,255,0.1);
            border: none;
            color: #fff;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            transition: all 0.2s;
        }
        .btn:hover { background: rgba(99, 102, 241, 0.3); }
        .btn-play {
            background: #6366f1;
            padding: 10px 30px;
        }
        .btn-play:hover { background: #5558e3; }
        .loading { text-align: center; padding: 60px; color: #888; }
        @media (max-width: 600px) {
            h1 { font-size: 1.8rem; }
            .song-card { padding: 12px 16px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎵 Bestelerim</h1>
        <p class="subtitle">Kendi bestelerimi dinleyin</p>
        <div id="songs" class="song-list">
            <div class="loading">Şarkılar yükleniyor...</div>
        </div>
    </div>
    
    <div class="player-bar">
        <div class="player-content">
            <div class="now-playing" id="nowPlaying">Şarkı seçin</div>
            <audio id="audio" controls></audio>
            <div class="controls">
                <button class="btn" onclick="playPrev()">⏮ Önceki</button>
                <button class="btn btn-play" onclick="togglePlay()">▶ Oynat</button>
                <button class="btn" onclick="playNext()">Sonraki ⏭</button>
            </div>
        </div>
    </div>

    <script>
        let songs = [];
        let currentIndex = -1;
        const audio = document.getElementById('audio');
        const nowPlaying = document.getElementById('nowPlaying');

        async function loadSongs() {
            try {
                const res = await fetch('/api/media');
                const data = await res.json();
                songs = data.files;
                renderSongs();
            } catch (e) {
                document.getElementById('songs').innerHTML = '<div class="loading">Yükleme hatası</div>';
            }
        }

        function renderSongs() {
            const container = document.getElementById('songs');
            container.innerHTML = songs.map((song, i) => `
                <div class="song-card" id="song-${i}" onclick="playSong(${i})">
                    <div class="song-icon">${song.type === 'audio' ? '🎵' : '🎬'}</div>
                    <div class="song-info">
                        <div class="song-title">${song.display_name}</div>
                        <div class="song-type">${song.type === 'audio' ? 'Ses Dosyası' : 'Video'}</div>
                    </div>
                </div>
            `).join('');
        }

        function playSong(index) {
            document.querySelectorAll('.song-card').forEach(c => c.classList.remove('active'));
            document.getElementById(`song-${index}`).classList.add('active');
            currentIndex = index;
            const song = songs[index];
            audio.src = song.url;
            audio.play();
            nowPlaying.textContent = '🎵 ' + song.display_name;
        }

        function togglePlay() {
            if (currentIndex === -1 && songs.length > 0) {
                playSong(0);
            } else if (audio.paused) {
                audio.play();
            } else {
                audio.pause();
            }
        }

        function playNext() {
            if (songs.length === 0) return;
            const next = (currentIndex + 1) % songs.length;
            playSong(next);
        }

        function playPrev() {
            if (songs.length === 0) return;
            const prev = currentIndex <= 0 ? songs.length - 1 : currentIndex - 1;
            playSong(prev);
        }

        audio.addEventListener('ended', playNext);
        loadSongs();
    </script>
</body>
</html>
'''

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_TEMPLATE

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
