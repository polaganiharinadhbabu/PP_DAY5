import os

from celery import Celery

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

celery_app = Celery(
    "notes_api",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    task_track_started=True,
    result_expires=3600,
)


@celery_app.task(
    bind=True,
    name="notes.generate_summary",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_note_summary(
    self,
    note_id: int,
    title: str,
    body: str,
) -> dict:
    text = " ".join((body or title).split())

    summary = (
        text
        if len(text) <= 240
        else text[:237].rstrip() + "..."
    )

    return {
        "note_id": note_id,
        "summary": summary,
    }
