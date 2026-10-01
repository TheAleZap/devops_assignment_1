from datetime import date

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from scheduling import service

router = APIRouter(prefix="/api/scheduling", tags=["scheduling"])


class PollCreate(BaseModel):
    title: str = Field(min_length=1)
    range_start: date
    range_end: date
    trip_length: int = Field(ge=1)


class AvailabilityUpdate(BaseModel):
    participant: str = Field(min_length=1)
    days: list[date]


@router.post("/polls", status_code=201)
def create_poll(body: PollCreate):
    try:
        return service.create_poll(
            body.title, body.range_start, body.range_end, body.trip_length
        )
    except service.SchedulingError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/polls/{poll_id}")
def get_poll(poll_id: int):
    try:
        return service.get_poll(poll_id)
    except service.PollNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.put("/polls/{poll_id}/availability")
def set_availability(poll_id: int, body: AvailabilityUpdate):
    try:
        return service.set_availability(poll_id, body.participant, body.days)
    except service.PollNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except service.SchedulingError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/polls/{poll_id}/best-windows")
def get_best_windows(poll_id: int, limit: int = Query(default=5, ge=1, le=20)):
    try:
        return service.get_best_windows(poll_id, limit)
    except service.PollNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))