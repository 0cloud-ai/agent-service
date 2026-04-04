import pytest
from pathlib import Path

from teamagent.tests.conftest import make_client


@pytest.fixture
def client(request, tmp_path):
    """自动从当前测试文件所在目录读取 teamagent.json 创建 client。"""
    test_dir = Path(request.fspath).parent
    config_path = test_dir / "teamagent.json"
    assert config_path.exists(), f"Missing {config_path}"
    return make_client(config_path, tmp_path)
