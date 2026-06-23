from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1)
    category: Optional[str] = Field(default=None, max_length=64)


class TicketOut(BaseModel):
    id: int
    title: str
    sentiment: str
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True
