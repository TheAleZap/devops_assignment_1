from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from trips import service

router = APIRouter(prefix="/api/trips", tags=["trips"])


class TripCreate(BaseModel):
    name: str = Field(min_length=1)
    destination: str | None = None
    members: list[str] = []


class MemberAdd(BaseModel):
    name: str = Field(min_length=1)


@router.post("", status_code=201)
def create_trip(body: TripCreate):
    try:
        return service.create_trip(body.name, body.destination, body.members)
    except service.TripsError as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/{trip_id}")
def get_trip(trip_id: int):
    try:
        return service.get_trip(trip_id)
    except service.TripNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.post("/{trip_id}/members", status_code=201)
def add_member(trip_id: int, body: MemberAdd):
    try:
        return service.add_member(trip_id, body.name)
    except service.TripNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except service.TripsError as error:
        raise HTTPException(status_code=400, detail=str(error))
