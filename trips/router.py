from datetime import date
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from trips import service

router = APIRouter(prefix="/api/trips", tags=["trips"])

NOT_FOUND_ERRORS = (service.TripNotFoundError, service.TaskNotFoundError)


class TripCreate(BaseModel):
    name: str = Field(min_length=1)
    destination: str | None = None
    members: list[str] = []


class MemberAdd(BaseModel):
    name: str = Field(min_length=1)


class TaskCreate(BaseModel):
    title: str = Field(min_length=1)


class TaskClaim(BaseModel):
    member: str = Field(min_length=1)


def run(action, *args):
    try:
        return action(*args)
    except NOT_FOUND_ERRORS as error:
        raise HTTPException(status_code=404, detail=str(error))
    except service.TripsError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.post("", status_code=201)
def create_trip(body: TripCreate):
    return run(service.create_trip, body.name, body.destination, body.members)


@router.get("/{trip_id}")
def get_trip(trip_id: int):
    return run(service.get_trip, trip_id)


@router.post("/{trip_id}/members", status_code=201)
def add_member(trip_id: int, body: MemberAdd):
    return run(service.add_member, trip_id, body.name)


@router.post("/{trip_id}/tasks", status_code=201)
def add_task(trip_id: int, body: TaskCreate):
    return run(service.add_task, trip_id, body.title)


@router.post("/{trip_id}/tasks/{task_id}/claim")
def claim_task(trip_id: int, task_id: int, body: TaskClaim):
    return run(service.claim_task, trip_id, task_id, body.member)


@router.post("/{trip_id}/tasks/{task_id}/complete")
def complete_task(trip_id: int, task_id: int):
    return run(service.complete_task, trip_id, task_id)


class DatesConfirm(BaseModel):
    date_poll_id: int = Field(ge=1)
    start: date


@router.put("/{trip_id}/dates")
def confirm_dates(trip_id: int, body: DatesConfirm):
    return run(service.confirm_dates, trip_id, body.date_poll_id, body.start)
