# feishu-chat-history

获取并总结飞书群聊消息记录，快速了解群里聊了什么。

## 能力

- 拉取指定飞书群的最近消息（默认 50 条/页）
- 自动解析 text / interactive / image 等消息类型
- 按话题分组、生成人类可读的讨论摘要
- 支持分页加载更多历史消息

## 触发场景

- "看群聊记录"、"群里聊了啥"
- "帮我看看这个群"、"群消息历史"
- "chat history"、"what did the group discuss"

## 工作原理

1. 从配置读取飞书应用凭据（`appId` / `appSecret`）
2. 获取 `tenant_access_token`
3. 调用 `GET /im/v1/messages` 拉取群消息
4. 解析各类型消息内容，过滤系统消息
5. 生成讨论话题摘要

## 消息解析

| 类型 | 处理方式 |
|------|----------|
| `text` | 提取 `body.content` JSON 中的 `text` 字段 |
| `interactive` | 从 `elements` 数组提取文本节点 |
| `image` | 标记为 `[图片]` |
| `system` | 默认过滤（加入/退出事件） |

## 配置

需要飞书应用凭据，通过 `channels.feishu.appId` / `appSecret` 配置。

## License

MIT
