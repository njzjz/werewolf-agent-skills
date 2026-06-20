# werewolf-agent-skills
让OpenClaw学会组织狼人杀游戏

> [!WARNING]
> 经过测试，没有模型能够完全不出错地组织游戏。
>
> 当前改造方向：把“会出错的自由推理”收缩为“脚本化流程 + 协议化输入输出 + 权限隔离”。

## 当前状态（重构进行中）

本仓库现在按正式 Python package 管理：核心逻辑以 `werewolf_core` 包发布，`tools/` 只保留薄 CLI wrapper，CI 负责 lint、单元测试和批量回归。

重构主线见 issues：
- #7 拆分 `werewolf-judge / werewolf-player / werewolf-core`
- #8 协议层（JudgeTask/PlayerReply）
- #9 法官显式 FSM
- #10 Prompt Compiler
- #11 程序化通信通道（公开/狼人私聊/夜间行动）
- #12 测试与批量回归
- #13 迁移与兼容

## 新目录（WIP）

```text
skills/
  werewolf-judge/
  werewolf-player/
packages/
  werewolf_core/        # import path: werewolf_core
.github/workflows/
  ci.yml
docs/
  architecture.md
  migration.md
tests/
tools/
  run_game.py           # 单局 runner wrapper
  run_batch.py          # 批量回归 wrapper
```

## Development

```bash
python -m pip install -e '.[dev]'
ruff check .
pytest -q
python tools/run_game.py --seed 1 --max-days 6
python tools/run_batch.py --runs 50 --seed-start 1 --max-days 6
```

## Why this refactor

- 法官不再“自由发挥”，只执行状态机。
- 玩家不再“自然语言裸回”，必须回结构化 JSON。
- 私有信息隔离由程序 ACL 保障，不靠“自觉”。

## Breaking change

旧目录 `skills/werewolf` 已删除。请直接使用：
- `skills/werewolf-judge`
- `skills/werewolf-player`

## Migration

迁移说明见 `docs/migration.md`。

## Notes

- 当前代码按 Python 3.10+ 语法编写；为兼容 3.10，时区时间统一使用 `timezone.utc`，不依赖 `datetime.UTC`。
- e2e/batch 回归默认走进程内 player responder，避免批量测试时频繁启动 Python 子进程。
- 审计日志默认采用追加式 JSONL 持久化，避免每条事件都重写完整 snapshot。
