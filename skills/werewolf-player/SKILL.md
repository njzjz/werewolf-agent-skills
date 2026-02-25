---
name: werewolf-player
description: |
  狼人杀玩家技能（协议响应版）。
  只负责根据法官给的可见上下文，输出结构化 PlayerReply。
---

# werewolf-player

这是狼人杀玩家专用 skill，定位是**受限执行器**。

## 职责边界

- ✅ 负责：
  - 基于 `visible_context` 给出发言/投票/夜间动作
  - 严格输出 PlayerReply JSON
- ❌ 不负责：
  - 读取全局状态文件
  - 推测或请求不该看到的私密信息
  - 返回不结构化自由文本作为最终动作

## 输出协议（简化）

```json
{
  "game_id": "g-001",
  "player_id": "player_3",
  "schema_version": "v1",
  "intent": "speak",
  "content": {
    "speech": "我先听后置位，再决定站边。",
    "target": "player_6",
    "confidence": 0.72
  }
}
```

## 强制约束

1. 必须先满足 `player_reply.schema.json`。
2. 不得包含 schema 未定义字段。
3. 任何越权信息都应忽略并在 speech 中声明“仅基于公开信息判断”。
