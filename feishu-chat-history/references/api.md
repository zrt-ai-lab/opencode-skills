# Feishu IM API Reference

## Auth

```
POST https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal
Content-Type: application/json

{"app_id": "...", "app_secret": "..."}
```

Response: `{"tenant_access_token": "...", "expire": 7200}`

## Fetch Chat Messages

```
GET https://open.feishu.cn/open-apis/im/v1/messages
  ?container_id_type=chat
  &container_id={chat_id}
  &page_size=50
  [&page_token={token}]      # pagination
  [&start_time={unix_ms}]    # filter by time range
  [&end_time={unix_ms}]
Authorization: Bearer {tenant_access_token}
```

Response fields:
- `data.items[]`: message list (newest first by default)
- `data.has_more`: bool
- `data.page_token`: use for next page

## Message Object Fields

| Field | Description |
|---|---|
| `message_id` | Unique ID |
| `msg_type` | `text`, `interactive`, `image`, `post`, `system` |
| `body.content` | JSON string — parse it |
| `sender.id` | Sender open_id (user) or app_id (bot) |
| `sender.sender_type` | `user` or `app` |
| `mentions[]` | List of @mentioned users with `name` and `id` |
| `create_time` | Unix ms timestamp |
| `root_id` | Thread root message ID (if in a thread) |
| `parent_id` | Direct parent message ID |

## Parsing msg_type

### text
```json
{"text": "hello world @_user_1"}
```
Replace `@_user_X` keys with the corresponding `mentions[].name`.

### interactive (card)
```json
{"title": null, "elements": [[{"tag": "text", "text": "..."}, ...]]}
```
Walk `elements` and concatenate all `tag=text` nodes.

### post
```json
{"title": "", "content": [[{"tag": "text", "text": "...", "style": []}]]}
```
Walk `content` rows and concatenate text nodes.

### image
```json
{"image_key": "img_v3_..."}
```
Render as `[图片]`.

### system
Template messages like join/leave events. Usually skip unless relevant.

## Python Snippet

```python
import json, os, urllib.request

config_path = os.path.expanduser('~/.openclaw-autoclaw/openclaw.json')
with open(config_path) as f:
    cfg = json.load(f)['channels']['feishu']

# Auth
req = urllib.request.Request(
    'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
    data=json.dumps({'app_id': cfg['appId'], 'app_secret': cfg['appSecret']}).encode(),
    headers={'Content-Type': 'application/json'}
)
token = json.loads(urllib.request.urlopen(req).read())['tenant_access_token']

# Fetch messages
chat_id = 'oc_xxxxxx'
url = f'https://open.feishu.cn/open-apis/im/v1/messages?container_id_type=chat&container_id={chat_id}&page_size=50'
req2 = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
data = json.loads(urllib.request.urlopen(req2).read())
messages = data['data']['items']
has_more = data['data'].get('has_more', False)
page_token = data['data'].get('page_token')
```
