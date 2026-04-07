"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes import router
from backend.app.core.data_store import load

app = FastAPI(
    title="STAR Regional Intelligence System",
    description="Decision-support API for STAR capacity-building planning",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
async def startup_event():
    load()


@app.get("/")
def root():
    return {
        "system": "STAR Regional Intelligence System",
        "version": "1.0.0",
        "docs": "/docs",
    }
