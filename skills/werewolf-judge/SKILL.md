---
name: werewolf-judge
description: |
  狼人杀法官技能（流程执行版）。
  只负责状态机推进、协议校验、公开播报，不负责玩家扮演策略。
---

# werewolf-judge

这是狼人杀法官专用 skill，定位是**编排器（orchestrator）**，不是“会自己推理一切的大脑”。

## 职责边界

- ✅ 负责：
  - 游戏状态机（FSM）推进
  - 给玩家分发结构化任务包（JudgeTask）
  - 校验玩家回复包（PlayerReply）
  - 公开信息播报（天亮/平安夜/发言顺序/投票结果）
- ❌ 不负责：
  - 编写玩家角色行为策略
  - 让自由文本直接驱动关键动作
  - 泄露任何夜间私有信息

## 使用方式

```bash
python skills/werewolf-judge/engine.py init
python skills/werewolf-judge/engine.py next --to night_seer
python skills/werewolf-judge/engine.py snapshot
```

## 强制约束

1. 任何状态迁移必须经过 `werewolf_core.fsm.WerewolfFSM`。
2. 任何玩家回复必须经过 `werewolf_core.protocol.validate_player_reply`。
3. 对主会话只输出公开信息；身份与夜间动作仅在游戏结束复盘披露。

## 依赖

- `packages/werewolf_core/fsm.py`
- `packages/werewolf_core/protocol.py`
- `packages/werewolf_core/orchestrator.py`
- `packages/werewolf_core/channels.py`
