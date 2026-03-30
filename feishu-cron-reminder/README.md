# feishu-cron-reminder

通过 OpenClaw cron 创建定时任务，稳定投递提醒消息到飞书会话。

## 能力

- 创建周期性飞书提醒（每 N 分钟 / 每小时 / 每天定时）
- 通过 main session 的 message 工具可靠投递
- 支持 `--every` 简写和 `--cron` 标准表达式
- 管理已有任务：列出、修改、删除、手动触发

## 触发场景

- "飞书定时提醒"、"定时任务发飞书"
- "每小时提醒"、"cron reminder to feishu"
- "scheduled feishu message"

## 使用方式

```bash
# 创建定时提醒（每 30 分钟）
openclaw cron add \
  --name "站会提醒" \
  --every "30m" \
  --session main \
  --system-event "[CRON定时任务] 站会提醒。你必须立即调用 message 工具..."

# 列出所有任务
openclaw cron list

# 手动触发测试
openclaw cron run <id>

# 删除任务
openclaw cron rm <id>
```

## 关键约束

- 必须使用 `--session main`（isolated 子 agent 无飞书权限）
- 不要使用 `--announce --channel feishu`（路由不可靠）
- 创建前必须向用户确认频率和发送目标

## License

MIT
