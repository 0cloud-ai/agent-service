from fastapi import APIRouter, HTTPException, Request
from pathlib import Path

router = APIRouter(prefix="/api/v1/workspace/sessions/{session_id}/files", tags=["workspace-files"])


def _check_raw_path(request: Request):
    """Reject requests whose raw URL path contains '..' traversal sequences."""
    raw = request.scope.get("path", "") or str(request.url.path)
    # Also check the raw bytes path from the ASGI scope
    raw_path = request.scope.get("raw_path", b"").decode(errors="replace")
    combined = raw + raw_path
    if ".." in combined:
        raise HTTPException(status_code=400, detail="Path traversal not allowed")


def _resolve_path(path: str, file_path: str) -> Path:
    # Reject any path containing '..' components before normalization
    parts = Path(file_path).parts
    if ".." in parts:
        raise HTTPException(status_code=400, detail="Path traversal not allowed")
    base = Path(path).resolve()
    target = (base / file_path).resolve()
    if not str(target).startswith(str(base)):
        raise HTTPException(status_code=400, detail="Path traversal not allowed")
    return target


@router.get("/{file_path:path}")
def read_file_or_dir(request: Request, session_id: str, file_path: str, path: str):
    _check_raw_path(request)
    target = _resolve_path(path, file_path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="Not found")
    if target.is_dir():
        entries = []
        for entry in sorted(target.iterdir()):
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                entries.append({"name": entry.name, "type": "directory"})
            else:
                stat = entry.stat()
                entries.append({
                    "name": entry.name,
                    "type": "file",
                    "size": stat.st_size,
                    "modified_at": stat.st_mtime,
                })
        return {"path": file_path or "/", "entries": entries}
    else:
        stat = target.stat()
        return {
            "path": file_path,
            "type": "file",
            "size": stat.st_size,
            "modified_at": stat.st_mtime,
            "content": target.read_text(encoding="utf-8"),
        }


@router.put("/{file_path:path}")
def edit_file(session_id: str, file_path: str, path: str, body: dict):
    target = _resolve_path(path, file_path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    target.write_text(body["content"], encoding="utf-8")
    return {"path": file_path, "size": target.stat().st_size, "modified_at": target.stat().st_mtime}


@router.post("/{file_path:path}")
def create_file(session_id: str, file_path: str, path: str, body: dict):
    target = _resolve_path(path, file_path)
    if target.exists():
        raise HTTPException(status_code=409, detail="File already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body.get("content", ""), encoding="utf-8")
    return {"path": file_path, "size": target.stat().st_size, "modified_at": target.stat().st_mtime}


@router.delete("/{file_path:path}")
def delete_file(session_id: str, file_path: str, path: str):
    target = _resolve_path(path, file_path)
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    target.unlink()
    return {"path": file_path}
