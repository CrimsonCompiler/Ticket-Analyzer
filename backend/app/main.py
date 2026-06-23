import logging

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, sentiment, schemas
from .db import Base, engine, get_db

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ticket-analyzer")

# Create the tickets table on startup. With a fresh Postgres volume this
# means no manual migrations are needed (PRD requirement).
Base.metadata.create_all(bind=engine)

# Eagerly load the model so the first POST /tickets is fast.
sentiment.load_model_once()

app = FastAPI(title="Ticket Analyzer", version="1.0.0")

# Optional CORS support. The default deployment uses the Nginx reverse
# proxy in the frontend container, so CORS is not required. If a
# cross-origin setup is used instead, this middleware allows it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post(
    "/tickets",
    response_model=schemas.TicketOut,
    status_code=status.HTTP_201_CREATED,
)
def create_ticket(
    payload: schemas.TicketCreate, db: Session = Depends(get_db)
):
    label, conf = sentiment.analyze(payload.message)
    ticket = models.Ticket(
        title=payload.title,
        message=payload.message,
        category=payload.category,
        sentiment=label,
        confidence=conf,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    log.info("ticket created id=%s sentiment=%s", ticket.id, ticket.sentiment)
    return ticket


@app.get("/tickets", response_model=list[schemas.TicketOut])
def list_tickets(db: Session = Depends(get_db)):
    return (
        db.query(models.Ticket)
        .order_by(models.Ticket.created_at.desc(), models.Ticket.id.desc())
        .all()
    )
