from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import os

from config.loader import load_config
from api.user_api import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    base_path = Path(os.environ.get("TEAMAGENT_BASE", ".")) / ".teamagent"
    app.state.base_path = base_path
    app.state.config = load_config(base_path / "teamagent.json")
    app.state.jwt_secret = os.environ.get("JWT_SECRET", "changeme")
    yield


app = FastAPI(title="teamagent.services", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)


@app.get("/health")
def health():
    return {"status": "ok"}
