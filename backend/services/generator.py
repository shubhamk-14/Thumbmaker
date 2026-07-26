import asyncio
import logging

from sqlmodel import Session, select
from database import engine
from models import Job, Thumbnail
from services.openai_service import generate_thumbnail
from services.imagekit_service import upload_file

logger = logging.getLogger(__name__)

STYLES = {
    "bold_dramatic": (
        "Create a bold, dramatic YouTube thumbnail with high contrast, "
        "cinematic lighting, dark moody background, and powerful composition. "
        "The person's face should be prominent with a dramatic expression."
    ),
    "clean_minimal": (
        "Create a clean, minimal YouTube thumbnail with bright lighting, "
        "white/light background, modern professional aesthetic, plenty of "
        "whitespace, and sharp clean composition. The person should look "
        "approachable and professional."
    ),
    "vibrant_energetic": (
        "Create a vibrant, energetic YouTube thumbnail with colorful gradients, "
        "dynamic angles, eye-catching pop-art style colors, and energetic "
        "composition. The person should have an excited or engaging expression."
    ),
}

STYLE_ORDER = [
    "bold_dramatic",
    "clean_minimal",
    "vibrant_energetic",
]


async def generate_single_thumbnail(
    thumbnail_id: str,
    prompt: str,
    headshot_url: str,
):
    # DB mark -> generating
    with Session(engine) as session:
        thumb = session.get(Thumbnail, thumbnail_id)

        if not thumb:
            logger.error(f"Thumbnail {thumbnail_id} not found")
            return

        thumb.status = "generating"
        style_name = thumb.style_name

        session.add(thumb)
        session.commit()

        style_prompt = STYLES[style_name]

    try:
        # AI call
        image_byte = await generate_thumbnail(
            prompt,
            style_prompt,
            headshot_url,
        )

        with Session(engine) as session:
            thumb = session.get(Thumbnail, thumbnail_id)

            if not thumb:
                raise ValueError(
                    f"Thumbnail {thumbnail_id} not found"
                )

            job_id = thumb.job_id

        # Upload image
        url = upload_file(
            file_bytes=image_byte,
            file_name=f"{thumbnail_id}.png",
            folder=f"thumbnails/{job_id}",
            content_type="image/png",
        )

        # Save URL and mark uploaded
        with Session(engine) as session:
            thumb = session.get(Thumbnail, thumbnail_id)

            if not thumb:
                raise ValueError(
                    f"Thumbnail {thumbnail_id} not found"
                )

            thumb.imagekit_url = url
            thumb.status = "uploaded"

            session.add(thumb)
            session.commit()

            logger.info(
                f"Thumbnail {thumbnail_id} generated and uploaded successfully."
            )

    except Exception as e:
        logger.exception(
            f"Error generating thumbnail {thumbnail_id}"
        )

        with Session(engine) as session:
            thumb = session.get(Thumbnail, thumbnail_id)

            if thumb:
                thumb.status = "failed"
                thumb.error_message = str(e)

                session.add(thumb)
                session.commit()


async def process_job(job_id: str):
    # Mark job as processing
    with Session(engine) as session:
        job = session.get(Job, job_id)

        if not job:
            return

        job.status = "processing"
        prompt = job.prompt
        headshot_url = job.headshot_url

        session.add(job)
        session.commit()

        thumbnails = session.exec(
            select(Thumbnail).where(
                Thumbnail.job_id == job_id
            )
        ).all()

        thumbnail_ids = [t.id for t in thumbnails]

    # Start workers
    tasks = [
        generate_single_thumbnail(
            tid,
            prompt,
            headshot_url,
        )
        for tid in thumbnail_ids
    ]

    await asyncio.gather(
        *tasks,
        return_exceptions=True,
    )

    # Final job status
    with Session(engine) as session:
        thumbnails = session.exec(
            select(Thumbnail).where(
                Thumbnail.job_id == job_id
            )
        ).all()

        all_failed = all(
            t.status == "failed"
            for t in thumbnails
        )

        job = session.get(Job, job_id)

        if job:
            job.status = (
                "failed"
                if all_failed
                else "completed"
            )

            session.add(job)
            session.commit()