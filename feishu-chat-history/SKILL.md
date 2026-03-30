---
name: feishu-chat-history
description: >
  Fetch and summarize Feishu group chat history. Use when the user asks
  to read, review, or summarize messages from a Feishu group chat.
  Triggers: "看群聊记录", "群里聊了啥", "帮我看看这个群", "群消息历史",
  "chat history", "what did the group discuss".
  NOT for: sending messages (use message tool), reading documents
  (use feishu-doc skill), or wiki operations (use feishu-wiki skill).
---

# Feishu Chat History

Fetch message history from a Feishu group chat and summarize or present it to the user.

## When to Use

- User asks what was discussed in a group
- User wants a summary or review of recent messages
- User provides a chat_id or is in a group and asks about its history

## How to Fetch Messages

Use the Feishu IM API directly via Python. See `references/api.md` for full details.

**Quick summary:**
1. Read credentials from config → `channels.feishu.appId` / `appSecret`
2. Get `tenant_access_token` via `POST /auth/v3/tenant_access_token/internal`
3. Fetch messages via `GET /im/v1/messages?container_id_type=chat&container_id={chat_id}&page_size=50`

## Identifying the chat_id

- If the user is asking about the **current group chat**, use the `chat_id` from the inbound metadata (`chat:oc_xxxxx` → strip the `chat:` prefix to get the raw ID)
- If the user provides a different group, ask for the chat_id

## Presenting Results

Parse each message and present a clean summary:
- Filter out `msg_type=system` (join/leave events) unless relevant
- For `msg_type=text`: extract `.body.content` as JSON, get the `text` field
- For `msg_type=interactive`: extract text nodes from the `elements` array
- For `msg_type=image`: note as `[图片]`
- Include sender name (from `mentions` or known bot app_ids), timestamp, and content
- Group by thread if `root_id` is present
- End with a human-readable summary of topics discussed

## Pagination

If `has_more=true`, fetch more pages using `page_token`. Default: fetch 1 page (50 messages). Ask user if they want more.
