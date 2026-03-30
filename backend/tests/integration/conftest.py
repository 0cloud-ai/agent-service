"""
Integration-test fixtures — spin up a real uvicorn server.

Usage:
    pytest tests/integration/ -v
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx
import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
_STARTUP_TIMEOUT = 15  # seconds


def _free_port() -> int:
    """Find a free TCP port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(base_url: str, timeout: float = _STARTUP_TIMEOUT) -> None:
    """Block until the server responds to GET /docs or timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            r = httpx.get(f"{base_url}/api/v1/service/info", timeout=2)
            if r.status_code < 500:
                return
        except httpx.ConnectError:
            pass
        time.sleep(0.3)
    raise RuntimeError(f"Server at {base_url} did not start within {timeout}s")


@pytest.fixture(scope="session")
def _tmp_dirs():
    """Create temp directories for DB and CLAUDE_HOME; clean up after suite."""
    tmp = tempfile.mkdtemp(prefix="agent_integ_")
    db_dir = Path(tmp) / "data"
    db_dir.mkdir()
    claude_home = Path(tmp) / "claude_home"
    claude_home.mkdir()
    yield {
        "root": tmp,
        "db_path": str(db_dir / "test.duckdb"),
        "claude_home": str(claude_home),
    }
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture(scope="session")
def server(_tmp_dirs) -> dict:
    """
    Start a real uvicorn server in a subprocess.

    Yields {"base_url": "http://127.0.0.1:<port>", "process": <Popen>}.
    """
    port = _free_port()
    env = {
        **os.environ,
        "DB_PATH": _tmp_dirs["db_path"],
        "CLAUDE_HOME": _tmp_dirs["claude_home"],
        "SESSION_ROOT": _tmp_dirs["root"],
        "SKIP_SYNC": "1",
    }

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "127.0.0.1",
            "--port", str(port),
        ],
        cwd=str(_BACKEND_DIR),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    base_url = f"http://127.0.0.1:{port}"

    try:
        _wait_for_server(base_url)
    except RuntimeError:
        proc.terminate()
        proc.wait(timeout=5)
        stdout = proc.stdout.read().decode() if proc.stdout else ""
        stderr = proc.stderr.read().decode() if proc.stderr else ""
        raise RuntimeError(
            f"Server failed to start.\nstdout:\n{stdout}\nstderr:\n{stderr}"
        )

    yield {"base_url": base_url, "process": proc}

    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@pytest.fixture()
def api(server) -> httpx.Client:
    """An httpx client pre-configured with the server's base URL."""
    with httpx.Client(base_url=server["base_url"], timeout=10) as client:
        yield client
