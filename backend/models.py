from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List
from uuid import uuid4

from sqlmodel import SQLModel, Field, Relationship


def _uuid() -> str:
    return str(uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Thumbnail(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)
    job_id: str = Field(foreign_key="job.id")

    style_name: str = ""
    imagekit_url: Optional[str] = None
    status: str = "pending"
    error_message: Optional[str] = None

    created_at: datetime = Field(default_factory=_now)

    job: Optional["Job"] = Relationship(back_populates="thumbnails")


class Job(SQLModel, table=True):
    id: str = Field(default_factory=_uuid, primary_key=True)

    prompt: str = ""
    num_thumbnails: int = Field(default=1, ge=1, le=3)
    headshot_url: str = ""
    status: str = "pending"

    created_at: datetime = Field(default_factory=_now)

    thumbnails: List["Thumbnail"] = Relationship(back_populates="job")