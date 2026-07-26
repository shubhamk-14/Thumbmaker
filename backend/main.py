import os
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import create_tables
from routes import router

# Absolute path to the static directory (always relative to this file)
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Ensure local storage paths exist for Mock Mode
os.makedirs(STATIC_DIR / "headshots", exist_ok=True)
os.makedirs(STATIC_DIR / "thumbnails", exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="YouTube Thumbnail Generator API",
    lifespan=lifespan
)

@app.get("/")
def root():
    return {"status": "ok", "message": "YouTube Thumbnail Generator API is running"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve local static files (headshots & mock thumbnails)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(router)