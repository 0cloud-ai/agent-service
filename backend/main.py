"""
Agent Service Backend

分层架构:
    api/        → HTTP 路由 (Controller)
    service/    → 业务逻辑
    repository/ → 数据访问 (DuckDB)
    model/
      do.py     → Domain Objects (内部模型)
      dto.py    → Data Transfer Objects (API 响应)

端点:
    GET /api/v1/stats/{path}     — 目录树统计
    GET /api/v1/sessions/{path}  — 会话列表 (游标分页)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.stats_api import router as stats_router
from api.session_api import router as session_router
from repository.db import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_if_empty()
    yield


app = FastAPI(title="Agent Service API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stats_router)
app.include_router(session_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
