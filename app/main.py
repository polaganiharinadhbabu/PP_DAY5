import hmac
import os
from typing import Literal

from celery.result import AsyncResult
from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Note
from app.rate_limit import enforce_rate_limit
from app.schemas import NoteCreate, NoteOut, NoteUpdate
from app.security import (
    LOCAL_DEVELOPMENT_KEY,
    require_api_key,
)
from app.tasks import celery_app, generate_note_summary

app = FastAPI(
    title="Notes API",
    version="1.0.0",
)

api = APIRouter(
    prefix="/v1",
    dependencies=[
        Depends(require_api_key),
        Depends(enforce_rate_limit),
    ],
)

SORT_FIELDS = {
    "id": Note.id,
    "title": Note.title,
    "status": Note.status,
    "created_at": Note.created_at,
    "updated_at": Note.updated_at,
}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@api.post(
    "/notes",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    payload: NoteCreate,
    db: Session = Depends(get_db),
):
    title = payload.title.strip()

    if not title:
        raise HTTPException(
            status_code=422,
            detail="Title must not be blank.",
        )

    note = Note(
        title=title,
        body=payload.body,
        status=payload.status,
    )

    db.add(note)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "error": "duplicate_title",
                "message": "A note with this title already exists.",
            },
        ) from exc

    db.refresh(note)
    return note


@api.get("/notes", response_model=list[NoteOut])
def list_notes(
    q: str | None = Query(default=None),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        pattern="^(draft|published|archived)$",
    ),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="created_at"),
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
):
    if sort_by not in SORT_FIELDS:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_sort_field",
                "allowed": sorted(SORT_FIELDS),
            },
        )

    statement = select(Note)

    if q:
        pattern = f"%{q}%"
        statement = statement.where(
            Note.title.ilike(pattern)
            | Note.body.ilike(pattern)
        )

    if status_filter:
        statement = statement.where(
            Note.status == status_filter
        )

    column = SORT_FIELDS[sort_by]

    if sort_order == "asc":
        statement = statement.order_by(
            column.asc(),
            Note.id.asc(),
        )
    else:
        statement = statement.order_by(
            column.desc(),
            Note.id.asc(),
        )

    return list(
        db.scalars(
            statement.offset(offset).limit(limit)
        ).all()
    )


@api.get("/notes/{note_id}", response_model=NoteOut)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
):
    note = db.get(Note, note_id)

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found.",
        )

    return note


@api.patch(
    "/notes/{note_id}",
    response_model=NoteOut,
)
def update_note(
    note_id: int,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
):
    note = db.get(Note, note_id)

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found.",
        )

    changes = payload.model_dump(exclude_unset=True)

    if changes.get("title") is not None:
        changes["title"] = changes["title"].strip()

        if not changes["title"]:
            raise HTTPException(
                status_code=422,
                detail="Title must not be blank.",
            )

    for field, value in changes.items():
        if value is not None:
            setattr(note, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "error": "duplicate_title",
                "message": "A note with this title already exists.",
            },
        ) from exc

    db.refresh(note)
    return note


@api.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
):
    note = db.get(Note, note_id)

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found.",
        )

    db.delete(note)
    db.commit()

    return Response(status_code=204)


@api.post(
    "/notes/{note_id}/summary",
    status_code=status.HTTP_202_ACCEPTED,
)
def request_note_summary(
    note_id: int,
    db: Session = Depends(get_db),
):
    note = db.get(Note, note_id)

    if note is None:
        raise HTTPException(
            status_code=404,
            detail="Note not found.",
        )

    try:
        task = generate_note_summary.delay(
            note.id,
            note.title,
            note.body,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "task_queue_unavailable",
                "message": "The background task could not be queued.",
            },
        ) from exc

    return {
        "task_id": task.id,
        "status": "queued",
    }


@api.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    result = AsyncResult(
        task_id,
        app=celery_app,
    )

    response = {
        "task_id": task_id,
        "status": result.status,
    }

    if result.successful():
        response["result"] = result.result
    elif result.failed():
        response["error"] = "Task failed."

    return response


app.include_router(api)


class RoomManager:
    def __init__(self):
        self.rooms: dict[str, set[WebSocket]] = {}

    async def connect(
        self,
        room: str,
        websocket: WebSocket,
    ):
        await websocket.accept()
        self.rooms.setdefault(room, set()).add(websocket)

    def disconnect(
        self,
        room: str,
        websocket: WebSocket,
    ):
        connections = self.rooms.get(room)

        if connections is None:
            return

        connections.discard(websocket)

        if not connections:
            self.rooms.pop(room, None)

    async def broadcast(
        self,
        room: str,
        message: dict,
    ):
        for connection in list(
            self.rooms.get(room, set())
        ):
            await connection.send_json(message)


room_manager = RoomManager()


@app.websocket("/ws/notes")
async def notes_websocket(
    websocket: WebSocket,
    room: str = "general",
    api_key: str | None = None,
):
    expected_key = os.getenv(
        "API_KEY",
        LOCAL_DEVELOPMENT_KEY,
    )

    if (
        not api_key
        or not hmac.compare_digest(
            api_key,
            expected_key,
        )
    ):
        await websocket.close(
            code=1008,
            reason="Invalid API key",
        )
        return

    if not room or len(room) > 80:
        await websocket.close(
            code=1008,
            reason="Invalid room",
        )
        return

    await room_manager.connect(room, websocket)

    try:
        while True:
            payload = await websocket.receive_json()

            message = (
                payload.get("message")
                if isinstance(payload, dict)
                else None
            )

            if (
                not isinstance(message, str)
                or not message.strip()
                or len(message) > 2000
            ):
                await websocket.send_json({
                    "error": "invalid_message",
                    "message": "Message must be a non-empty string of at most 2000 characters.",
                })
                continue

            await room_manager.broadcast(
                room,
                {
                    "room": room,
                    "message": message.strip(),
                },
            )

    except WebSocketDisconnect:
        pass

    finally:
        room_manager.disconnect(room, websocket)
