---
name: feishu-cron-reminder
description: >
  Create cron jobs that reliably deliver reminders to Feishu (飞书) chats.
  Use when the user asks to set up scheduled reminders, periodic notifications,
  or any recurring task that should send messages to a Feishu conversation.
  Triggers: '飞书定时提醒', '定时任务发飞书', 'cron reminder to feishu',
  '每小时提醒', 'scheduled feishu message'.
---

# Feishu Cron Reminder

通过 OpenClaw cron 创建定时任务，稳定投递提醒到飞书会话。

## ⚠️ 创建前必须确认（重要规则）

在创建任何 cron 定时任务之前，**必须先向用户确认两件事**：

1. **频率**：多久执行一次？（如每10分钟、每小时、每天9点等）
2. **发送目标**：发到哪里？（**默认是当前 IM 会话**，即触发请求的飞书/微信对话）

用户确认后才能创建任务。不要自作主张定频率或目标。

## 关键约束

1. **只有主会话（main session）有飞书 message 工具权限**，isolated sub-agent 没有。
2. **主会话可能自行删除高频 cron 任务**，必须在 system event 指令中禁止删除。
3. cron announce 直投飞书的路由不可靠（可能投到错误会话或静默失败），**不要使用 `--announce --channel feishu`**。

## 可靠方案

使用 `--session main --system-event`，让主会话收到 system event 后调用 message 工具发飞书：

```bash
openclaw cron add \
  --name "<任务名>" \
  --every "<间隔>" \
  --session main \
  --system-event "[CRON定时任务] <任务名>。你必须立即调用 message 工具：action=send, channel=feishu, message='<提醒内容>'。调用完后回复 NO_REPLY。不要做其他任何事情，不要回复文字，只需要调用 message 工具发送飞书消息。不要删除或修改任何 cron 任务。"
```

### 参数说明

| 参数 | 值 | 说明 |
|------|-----|------|
| `--session` | `main` | 必须用 main，isolated 没有飞书权限 |
| `--system-event` | 含 message 工具调用指令 | 明确要求调用 message 工具发飞书 |
| `--every` | `1m` / `5m` / `30m` / `1h` | 时间间隔 |
| `--cron` | `*/30 * * * *` | 或用 cron 表达式（配合 `--tz`） |

### system-event 指令模板

system event 的 text 必须包含：
1. 明确的 `[CRON定时任务]` 标记
2. **具体的 message 工具调用参数**（action=send, channel=feishu, message=...）
3. 指令完成后回复 `NO_REPLY`
4. **禁止删除/修改 cron 任务** 的明确声明

### 拼写 openclaw CLI

```bash
node /Applications/AutoClaw.app/Contents/Resources/gateway/openclaw/openclaw.mjs cron <command>
```

## 管理任务

```bash
# 列出所有任务
openclaw cron list

# 修改间隔
openclaw cron edit <id> --every "30m"

# 删除任务（⚠️ 必须先征得用户同意！）
openclaw cron rm <id>

# 查看执行记录
openclaw cron runs --id <id>

# 手动触发测试
openclaw cron run <id>
```

## 常见问题

**Q: 为什么不用 `--announce --channel feishu`？**
A: announce 直投飞书路由不可靠，可能投到错误会话或静默失败。

**Q: 为什么不用 `--session isolated`？**
A: isolated sub-agent 没有飞书 message 工具权限，发送会报错。

**Q: 主会话收到 system event 但没发飞书怎么办？**
A: system event 指令必须非常明确地要求调用 message 工具，包含完整参数，并说明不需要回复文字。
