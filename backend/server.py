from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import os
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()

MONGO_URL = os.environ.get("MONGO_URL", "")
client = None
db = None

@app.on_event("startup")
async def startup():
    global client, db
    if MONGO_URL:
        client = AsyncIOMotorClient(MONGO_URL)
        db = client.bestelerim

@app.get("/")
async def home():
    if db:
        try:
            await db.command("ping")
            return {"status": "MongoDB BAGLANDI!"}
        except Exception as e:
            return {"status": "HATA", "error": str(e)}
    return {"status": "MONGO_URL yok"}

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
