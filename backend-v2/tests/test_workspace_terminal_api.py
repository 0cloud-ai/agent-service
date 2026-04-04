def test_execute_command(client, teamagent_dir):
    project = teamagent_dir.parent / "project"
    project.mkdir()
    r = client.post(f"/api/v1/workspace/sessions/fake/terminal?path={project}", json={"command": "echo hello"})
    assert r.status_code == 200
    assert "hello" in r.json()["stdout"]
    assert r.json()["code"] == 0


def test_execute_command_failure(client, teamagent_dir):
    project = teamagent_dir.parent / "project"
    project.mkdir()
    r = client.post(f"/api/v1/workspace/sessions/fake/terminal?path={project}", json={"command": "false"})
    assert r.status_code == 200
    assert r.json()["code"] != 0


def test_execute_empty_command(client, teamagent_dir):
    project = teamagent_dir.parent / "project"
    project.mkdir()
    r = client.post(f"/api/v1/workspace/sessions/fake/terminal?path={project}", json={"command": ""})
    assert r.status_code == 400
