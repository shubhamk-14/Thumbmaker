import base64
import io
import os
from openai import AsyncOpenAI
from config import OPENAI_API_KEY, MOCK_MODE

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

def generate_mock_thumbnail(prompt: str, style_prompt: str, headshot_url: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont
    
    # 1. Create a 1280x720 canvas
    img = Image.new("RGB", (1280, 720), color=(20, 20, 30))
    draw = ImageDraw.Draw(img)
    
    # Draw simple background gradient (dark blue to purple)
    for y in range(720):
        r = int(20 + (y / 720) * 40)
        g = int(20 + (y / 720) * 10)
        b = int(30 + (y / 720) * 50)
        draw.line([(0, y), (1280, y)], fill=(r, g, b))
        
    # Draw style-specific color accents
    style_lower = style_prompt.lower()
    if "bold_dramatic" in style_lower or "dramatic" in style_lower:
        # Bold orange/red diagonal split
        draw.polygon([(0, 0), (600, 0), (400, 720), (0, 720)], fill=(210, 70, 30))
    elif "clean_minimal" in style_lower or "clean" in style_lower:
        # Clean white/light gray background accent
        draw.polygon([(0, 0), (700, 0), (550, 720), (0, 720)], fill=(240, 240, 250))
    else:
        # Vibrant energetic purple
        draw.polygon([(0, 0), (650, 0), (450, 720), (0, 720)], fill=(138, 43, 226))

    # 2. Try to fetch and paste the headshot on the right side
    try:
        headshot_img = None
        if headshot_url.startswith("http://127.0.0.1:8000/static/"):
            # Load from local disk since it's a local static URL
            local_path = headshot_url.replace("http://127.0.0.1:8000/static/", "static/")
            if os.path.exists(local_path):
                headshot_img = Image.open(local_path)
        elif headshot_url:
            import httpx
            resp = httpx.get(headshot_url, timeout=5)
            headshot_img = Image.open(io.BytesIO(resp.content))

        if headshot_img:
            # Resize headshot to fit nicely on the right
            headshot_img.thumbnail((450, 600))
            # Paste it
            mask = headshot_img if headshot_img.mode in ('RGBA', 'LA') else None
            img.paste(headshot_img, (780, 720 - headshot_img.height - 20), mask=mask)
    except Exception as e:
        print(f"Mock headshot paste failed: {e}")

    # 3. Draw UI labels
    badge_bg = (255, 255, 255) if "clean" in style_lower else (0, 0, 0)
    badge_fg = (0, 0, 0) if "clean" in style_lower else (255, 255, 255)
    draw.rounded_rectangle([(80, 80), (240, 130)], radius=5, fill=badge_bg)

    # Load font or fallback
    try:
        font_title = ImageFont.truetype("arial.ttf", 60)
        font_badge = ImageFont.truetype("arial.ttf", 22)
    except IOError:
        font_title = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    draw.text((95, 95), "NEW VIDEO", fill=badge_fg, font=font_badge)

    # 4. Wrap and draw the title text (prompt)
    words = prompt.split()
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(" ".join(current_line)) > 18:
            lines.append(" ".join(current_line[:-1]))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))

    y_text = 180
    for line in lines[:5]:
        text_color = (20, 20, 20) if "clean" in style_lower else (255, 255, 255)
        draw.text((80, y_text), line.upper(), fill=text_color, font=font_title)
        y_text += 75

    # 5. Export to PNG bytes
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

async def generate_thumbnail(prompt: str, style_prompt: str, headshot_url: str) -> bytes:
    """
    Use the Response API with gpt-image-2 as a built-in image_generation
    tool.
    pass the headshot URL directly as an input_image.
    Returns raw PNG bytes.
    """
    if MOCK_MODE:
        return generate_mock_thumbnail(prompt, style_prompt, headshot_url)

    full_prompt = (
        f"{style_prompt}\n\n"
        f"User request: {prompt}\n\n"
        "IMPORTANT: The generated thumbnail MUST prominently feature the person"
        "show in the provided reference headshot photo. Keep their likeness accurate."
    )

    response = await client.responses.create(
        model="gpt-4o",
        input=[
            {
                "role":"user",
                "content": [
                    {"type": "input_text", "text": full_prompt},
                    {"type": "input_image", "image_url": headshot_url},
                ]
            }
        ],
        tools=[
            {"type":"image_generation",
             "model": "gpt-image-1",
             "size": "1536x1024",
             "quality": "high",
             "output_format": "png",
             "input_fidelity": "high",
            },
          ],
    )

    for item in response.output:
        if item.type == "image_generation_call" and item.result:
            return base64.b64decode(item.result)
        
    raise RuntimeError("No image generation result found in the response")
