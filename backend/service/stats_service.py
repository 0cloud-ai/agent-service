"""
Stats Service — 目录树统计，委托 Repository 层查询 DuckDB。
"""

from __future__ import annotations

from model.dto import ChildStatsDTO, CountsDTO, StatsResponseDTO
from repository import stats_repo


def _normalize(path: str) -> str:
    if not path or path == "/":
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/")


def get_stats(path: str) -> StatsResponseDTO | None:
    path = _normalize(path)

    # 根路径始终存在
    if path != "/" and not stats_repo.path_exists(path):
        return None

    direct = CountsDTO(**stats_repo.direct_counts(path))
    total = CountsDTO(**stats_repo.total_counts(path))

    children = [
        ChildStatsDTO(name=c["name"], total=CountsDTO(**c["total"]))
        for c in stats_repo.child_stats(path)
    ]

    return StatsResponseDTO(
        path=path,
        direct=direct,
        total=total,
        children=children,
    )
