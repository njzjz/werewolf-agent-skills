# werewolf-agent-skills
让OpenClaw学会组织狼人杀游戏

> [!WARNING]
> 经过测试，没有模型能够完全不出错地组织游戏。
>
> 当前改造方向：把“会出错的自由推理”收缩为“脚本化流程 + 协议化输入输出 + 权限隔离”。

## 当前状态（重构进行中）

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
  werewolf_core/
docs/
  architecture.md
  migration.md
tests/
```

## Why this refactor

- 法官不再“自由发挥”，只执行状态机。
- 玩家不再“自然语言裸回”，必须回结构化 JSON。
- 私有信息隔离由程序 ACL 保障，不靠“自觉”。

## 开发说明

当前仓库处于重构中间态，legacy `skills/werewolf` 暂时保留，后续会给出兼容 wrapper 与迁移步骤。
