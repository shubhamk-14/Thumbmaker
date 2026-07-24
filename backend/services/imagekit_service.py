import os
from imagekitio import ImageKit
from config import IMAGEKIT_PRIVATE_KEY, IMAGEKIT_URL_ENDPOINT, MOCK_MODE

imagekit = ImageKit(private_key=IMAGEKIT_PRIVATE_KEY)

def upload_file(file_bytes: bytes, file_name: str, folder: str, content_type: str = "image/png") -> str:
    """Upload a file to ImageKit and return the CDN URL (or local static URL in Mock Mode)."""
    if MOCK_MODE:
        # Save file locally in static directory
        local_dir = os.path.join("static", folder)
        os.makedirs(local_dir, exist_ok=True)
        local_filepath = os.path.join(local_dir, file_name)
        with open(local_filepath, "wb") as f:
            f.write(file_bytes)
        
        # Normalize folder slash for web URL path
        web_folder = folder.replace("\\", "/")
        return f"http://127.0.0.1:8000/static/{web_folder}/{file_name}"

    if not IMAGEKIT_PRIVATE_KEY or not IMAGEKIT_URL_ENDPOINT:
        raise RuntimeError("ImageKit credentials are missing. Check backend/.env.")

    result = imagekit.files.upload(
        file=(file_name, file_bytes, content_type),
        file_name=file_name,
        folder=folder,
        is_private_file=False,
        use_unique_file_name=True,
    )

    if not result.url:
        raise RuntimeError("ImageKit upload did not return a file URL.")

    return result.url

def get_variants(base_url: str) -> dict:
    """Return 3 sizes variant URLs using imagekit transformations."""
    if MOCK_MODE:
        # Return same URL in mock mode
        return {
            "youtube": base_url,
            "shorts": base_url,
            "square": base_url,
        }

    return {
        "youtube": f"{base_url}?tr=w-1280,h-720,c-maintain_ratio,fo-auto",
        "shorts": f"{base_url}?tr=w-1080,h-1920,c-maintain_ratio,fo-auto",
        "square": f"{base_url}?tr=w-1080,h-1080,c-maintain_ratio,fo-auto",
    }
