# 目录上下文

## 概述

teamagent.services 在每个工作目录中通过 `.teamagent/` 子目录维护该层级的上下文信息。

```
project/
├── .teamagent/
│   ├── teamagent.json        # 全局配置（仅根目录）
│   └── sessions/             # 当前目录层级的会话
│
├── src/
│   └── .teamagent/
│       └── sessions/         # src/ 层级的会话
│
└── docs/
    └── .teamagent/
        └── sessions/         # docs/ 层级的会话
```

## 设计原则

- 每个目录可以拥有自己的 `.teamagent/`，记录与该层级相关的上下文
- 数据直接存储在文件系统，API 从文件系统读写，无需数据库
- 未来可能扩展更多上下文内容（如目录级别的规则、缓存等）

## 上下文内容

| 路径 | 文档 | 说明 |
|------|------|------|
| `.teamagent/sessions/` | [sessions.md](sessions.md) | 会话记录 |
