# Architecture (WIP)

## 三层拆分

- `skills/werewolf-judge`
  - 流程编排、协议校验、公开播报
- `skills/werewolf-player`
  - 玩家回包生成（PlayerReply）
- `packages/werewolf_core`（正式 import path: `werewolf_core`）
  - 状态机、协议、通道、模板编译、正式 runner、批量回归入口

## 目标原则

1. Flow by FSM, not by free-form prompt.
2. Parse JSON protocol only.
3. ACL-enforced channels for info isolation.
4. Judge/player prompt text generated from deterministic templates.
5. Runtime flow lives in `werewolf_core.runner`; `tools/` only contains thin wrappers.
