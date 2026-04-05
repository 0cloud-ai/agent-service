from __future__ import annotations

from teamagent.harness.types import (
    FileWatcher,
    AsyncWatcher,
    ProviderInfo,
    Record,
)


class HarnessEngine:
    """Harness 插件必须实现的接口。"""

    id: str
    name: str
    api_formats: list[str]

    def submit(
        self, path: str, message: str, provider: ProviderInfo | None = None
    ) -> FileWatcher | AsyncWatcher:
        raise NotImplementedError

    def watch(self, event) -> list[Record] | None:
        """统一的格式转换方法，两种 Watcher 模式都会调用。

        FileWatcher 模式：event 是 FileChangeEvent（文件增量数据）
        AsyncWatcher 模式：event 是迭代器 yield 的原始引擎事件
        """
        raise NotImplementedError
