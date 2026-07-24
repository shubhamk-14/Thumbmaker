import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY","")
IMAGEKIT_PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY","")
IMAGEKIT_PUBLIC_KEY = os.getenv("IMAGEKIT_PUBLIC_KEY","")
IMAGEKIT_URL_ENDPOINT = os.getenv("IMAGEKIT_URL_ENDPOINT","")


DATABASE_URL = f"sqlite:///{Path(__file__).with_name('thumbnailbuilder.db')}"

MOCK_MODE = (
    OPENAI_API_KEY == "chai" or not OPENAI_API_KEY or
    IMAGEKIT_PRIVATE_KEY == "chai" or not IMAGEKIT_PRIVATE_KEY
)
