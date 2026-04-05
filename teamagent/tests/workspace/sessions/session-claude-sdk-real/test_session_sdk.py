import time
from pathlib import Path


def test_session_create_file(client, tmp_path):
    """E2E: 创建 session → 发消息让 agent 创建文件 → 验证文件存在。"""
    work_dir = tmp_path / "workspace"
    work_dir.mkdir()

    # 1. 创建 session
    r = client.post("/api/v1/workspace/sessions", json={
        "path": str(work_dir),
        "title": "test-create-file",
        "harness": "claude-agent-sdk",
        "provider": "minmax",
    })
    assert r.status_code == 200
    session = r.json()
    session_id = session["id"]
    assert session["harness"] == "claude-agent-sdk"
    assert session["provider"] == "minmax"

    # 2. 发消息
    r = client.post(
        f"/api/v1/workspace/sessions/{session_id}/messages",
        params={"path": str(work_dir)},
        json={"content": "在当前工作目录下创建一个文件 abc.txt，内容为 hello"},
    )
    assert r.status_code == 200

    # 3. 轮询 messages 等待 assistant 回复出现（通过 HTTP 请求保持 event loop 活跃）
    target_file = work_dir / "abc.txt"
    for _ in range(120):
        # 通过 API 轮询消息，同时检查文件
        r = client.get(
            f"/api/v1/workspace/sessions/{session_id}/messages",
            params={"path": str(work_dir)},
        )
        if target_file.exists():
            break
        time.sleep(0.5)

    # 4. 验证文件存在
    assert target_file.exists(), f"abc.txt was not created in {work_dir}"
    content = target_file.read_text()
    assert "hello" in content
