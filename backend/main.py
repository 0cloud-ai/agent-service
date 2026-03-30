"""
Agent Service Backend

API 结构:
    /api/v1/user/          → 用户账号
    /api/v1/workspace/     → 工程面板
    /api/v1/service/       → 服务面板
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ── Legacy (保留兼容) ────────────────────────────────────────────────
from api.stats_api import router as legacy_stats_router
from api.session_api import router as legacy_session_router

# ── User ─────────────────────────────────────────────────────────────
from api.user_api import router as user_router

# ── Workspace ────────────────────────────────────────────────────────
from api.workspace_stats_api import router as workspace_stats_router
from api.workspace_sessions_api import router as workspace_sessions_router
from api.workspace_members_api import router as workspace_members_router
from api.workspace_providers_api import router as workspace_providers_router
from api.workspace_harness_api import router as workspace_harness_router
from api.workspace_service_inbox_api import router as workspace_service_inbox_router

# ── Service ──────────────────────────────────────────────────────────
from api.service_info_api import router as service_info_router
from api.service_conversations_api import router as service_conversations_router

from repository.db import get_conn
from repository.sdk_adapter import sync as sync_via_sdk
from repository.claude_cli_adapter import sync as sync_via_cli


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_conn()
    if not os.environ.get("SKIP_SYNC"):
        sync_via_sdk()
        sync_via_cli()
    yield


app = FastAPI(title="Agent Service API", version="0.5.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Legacy
app.include_router(legacy_stats_router)
app.include_router(legacy_session_router)

# User
app.include_router(user_router)

# Workspace
app.include_router(workspace_stats_router)
app.include_router(workspace_sessions_router)
app.include_router(workspace_members_router)
app.include_router(workspace_providers_router)
app.include_router(workspace_harness_router)
app.include_router(workspace_service_inbox_router)

# Service
app.include_router(service_info_router)
app.include_router(service_conversations_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=3000, reload=True)
