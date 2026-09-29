import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import config
import db
from scheduling.router import router as scheduling_router
from trips.router import router as trips_router

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="TripSync", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(scheduling_router)
app.include_router(trips_router)

app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=config.PORT)