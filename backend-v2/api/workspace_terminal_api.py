import asyncio
from fastapi import APIRouter, HTTPException
from pathlib import Path

router = APIRouter(prefix="/api/v1/workspace/sessions/{session_id}/terminal", tags=["workspace-terminal"])


@router.post("")
async def execute_command(session_id: str, path: str, body: dict):
    command = body.get("command")
    if not command:
        raise HTTPException(status_code=400, detail="command is required")
    timeout = min(body.get("timeout", 120), 600)
    cwd = Path(path)
    if not cwd.is_dir():
        raise HTTPException(status_code=404, detail="Path not found")
    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return {
            "stdout": stdout.decode(errors="replace"),
            "stderr": stderr.decode(errors="replace"),
            "code": proc.returncode,
        }
    except asyncio.TimeoutError:
        proc.kill()
        raise HTTPException(status_code=408, detail="Command timed out")
