# Migration Guide (WIP)

## from legacy `skills/werewolf`

- 旧：`skills/werewolf/SKILL.md`
- 新：
  - 法官：`skills/werewolf-judge/SKILL.md`
  - 玩家：`skills/werewolf-player/SKILL.md`

## 建议迁移顺序

1. 先切法官入口到 `werewolf-judge/engine.py`
2. 玩家交互切到 `PlayerReply` JSON 输出
3. 去除法官内置角色策略，改为调用 player skill

## 兼容策略

短期保留 legacy `skills/werewolf`，标记 deprecated。
