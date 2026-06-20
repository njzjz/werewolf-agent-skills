# Migration guide (WIP)

## 背景

仓库已从单技能 `skills/werewolf` 迁移到“法官 / 玩家 / 核心库”三层结构，目标是把流程控制、协议校验和信息隔离从 prompt 习惯迁到可测试代码里。

## 目录迁移

旧结构：

```text
skills/
  werewolf/
```

新结构：

```text
skills/
  werewolf-judge/
  werewolf-player/
packages/
  werewolf_core/
```

## 迁移要点

- 旧的 `skills/werewolf` 已删除，不再维护兼容层。
- 法官侧逻辑迁移到 `skills/werewolf-judge` + `packages/werewolf_core.orchestrator`。
- 玩家回包逻辑迁移到 `skills/werewolf-player/responder.py`。
- 游戏状态、协议校验、FSM、通道 ACL 等通用逻辑迁移到 `packages/werewolf_core/`。

## 对调用方的影响

- 不再假设单个 skill 同时扮演法官和玩家。
- Judge 与 Player 间通信应走结构化 JSON：`JudgeTask` / `PlayerReply`。
- 新代码应优先依赖正式 import 包 `werewolf_core`，而不是复制旧脚本实现；源码仍位于 `packages/werewolf_core/`。

## 建议替换路径

- `skills/werewolf/scripts/game_engine.py` → `packages/werewolf_core/game.py`
- `skills/werewolf/scripts/judge_prompt.py` → `packages/werewolf_core/prompting.py`
- `skills/werewolf/scripts/player_prompts.py` → `skills/werewolf-player/responder.py`
- 旧的临时 e2e 主流程 → `packages/werewolf_core/runner.py`

## 当前状态

本文档当前覆盖目录、职责和正式 package 入口。CI 会运行 `ruff check .`、`pytest -q` 和 `tools/run_batch.py` 批量 smoke，避免核心流程重新散落回脚本。更细的协议字段和 FSM 阶段流转说明，后续会继续补充。
