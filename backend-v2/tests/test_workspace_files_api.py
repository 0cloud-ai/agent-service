def test_list_directory(client, teamagent_dir):
    project = teamagent_dir.parent / "project"
    project.mkdir()
    (project / "README.md").write_text("hello")
    (project / "src").mkdir()
    r = client.get("/api/v1/workspace/sessions/fake/files/?path=" + str(project))
    assert r.status_code == 200
    names = [e["name"] for e in r.json()["entries"]]
    assert "README.md" in names
    assert "src" in names


def test_read_file(client, teamagent_dir):
    project = teamagent_dir.parent / "project"
    project.mkdir()
    (project / "test.txt").write_text("content here")
    r = client.get(f"/api/v1/workspace/sessions/fake/files/test.txt?path={project}")
    assert r.status_code == 200
    assert r.json()["content"] == "content here"


def test_create_file(client, teamagent_dir):
    project = teamagent_dir.parent / "project"
    project.mkdir()
    r = client.post(f"/api/v1/workspace/sessions/fake/files/new.txt?path={project}", json={"content": "new"})
    assert r.status_code == 200
    assert (project / "new.txt").read_text() == "new"


def test_create_file_conflict(client, teamagent_dir):
    project = teamagent_dir.parent / "project"
    project.mkdir()
    (project / "existing.txt").write_text("x")
    r = client.post(f"/api/v1/workspace/sessions/fake/files/existing.txt?path={project}", json={"content": "y"})
    assert r.status_code == 409


def test_edit_file(client, teamagent_dir):
    project = teamagent_dir.parent / "project"
    project.mkdir()
    (project / "test.txt").write_text("old")
    r = client.put(f"/api/v1/workspace/sessions/fake/files/test.txt?path={project}", json={"content": "new"})
    assert r.status_code == 200
    assert (project / "test.txt").read_text() == "new"


def test_delete_file(client, teamagent_dir):
    project = teamagent_dir.parent / "project"
    project.mkdir()
    (project / "test.txt").write_text("x")
    r = client.delete(f"/api/v1/workspace/sessions/fake/files/test.txt?path={project}")
    assert r.status_code == 200
    assert not (project / "test.txt").exists()


def test_path_traversal_blocked(client, teamagent_dir):
    project = teamagent_dir.parent / "project"
    project.mkdir()
    r = client.get(f"/api/v1/workspace/sessions/fake/files/%2E%2E%2F%2E%2E%2Fetc%2Fpasswd?path={project}")
    assert r.status_code == 400
