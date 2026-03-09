# API 参考文档

## 概述

本技能使用两套 API：
1. **Images API** - 用于图像生成和编辑（文生图、图生图）
2. **Qwen2.5-VL API** - 用于视觉识别（图生文）

---

## 一、Images API（图像生成）

### 1.1 基础配置

| 配置项 | 值 |
|-------|-----|
| Base URL | 配置文件中的 `image_api.base_url` |
| Model | 配置文件中的 `image_api.model` |
| 认证方式 | Bearer Token |

### 1.2 文生图接口

**端点**
```
POST /images/generations
```

**请求头**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer ${IMAGE_API_KEY}"
}
```

**请求体**
```json
{
  "model": "dall-e-3",
  "prompt": "中文图像描述",
  "size": "1792x1024",
  "response_format": "b64_json"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| model | string | 是 | 配置文件中的 `image_api.model` |
| prompt | string | 是 | 中文图像生成提示词 |
| size | string | 否 | 图片尺寸，默认 `1792x1024` |
| response_format | string | 否 | 响应格式，推荐 `b64_json` |

**响应体**
```json
{
  "created": 1641234567,
  "data": [
    {
      "b64_json": "base64编码的图片数据"
    }
  ]
}
```

### 1.3 图生图接口

**端点**
```
POST /images/edits
```

**请求体**
```json
{
  "model": "dall-e-3",
  "prompt": "中文编辑指令",
  "image": "data:image/png;base64,{base64数据}",
  "size": "1792x1024",
  "response_format": "b64_json"
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| model | string | 是 | 配置文件中的 `image_api.model` |
| prompt | string | 是 | 中文图片编辑指令 |
| image | string | 是 | Base64 编码的参考图片（含 data URL 前缀） |
| size | string | 否 | 输出尺寸 |
| response_format | string | 否 | 响应格式 |

**响应体**
```json
{
  "data": [
    {
      "b64_json": "base64编码的生成图片"
    }
  ]
}
```

---

## 二、Qwen2.5-VL API（视觉识别）

### 2.1 基础配置

| 配置项 | 值 |
|-------|-----|
| Base URL | 配置文件中的 `vision_api.base_url` |
| Model | 配置文件中的 `vision_api.model` |
| 认证方式 | Bearer Token |

### 2.2 图生文接口

**端点**
```
POST /chat/completions
```

**请求头**
```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer ${VISION_API_KEY}"
}
```

**请求体**
```json
{
  "model": "qwen2.5-vl-72b-instruct",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "请描述这张图片"
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "data:image/jpeg;base64,{base64数据}"
          }
        }
      ]
    }
  ],
  "max_tokens": 2000,
  "temperature": 0.7
}
```

**参数说明**

| 参数 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| model | string | 是 | 视觉模型名称 |
| messages | array | 是 | 消息列表，包含文本和图片 |
| max_tokens | int | 否 | 最大输出 token 数 |
| temperature | float | 否 | 温度参数（0-1） |

**响应体**
```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1641234567,
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "这是一张..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

---

## 三、错误码说明

| 状态码 | 说明 | 处理建议 |
|-------|------|---------|
| 400 | 请求参数错误 | 检查请求体格式和参数 |
| 401 | API 密钥无效 | 检查 API Key 是否正确 |
| 403 | 权限不足 | 检查 API Key 权限 |
| 429 | 请求频率限制 | 等待后重试 |
| 500 | 服务器内部错误 | 稍后重试 |
| 503 | 服务不可用 | 稍后重试 |

---

## 四、最佳实践

### 4.1 超时设置

- 文生图：建议 120-180 秒
- 图生图：建议 180-300 秒
- 图生文：建议 60-120 秒

### 4.2 重试策略

建议实现指数退避重试：
1. 首次重试：等待 1 秒
2. 第二次重试：等待 2 秒
3. 第三次重试：等待 4 秒

### 4.3 图片格式

- 支持格式：PNG、JPG、JPEG、WebP、GIF
- 推荐格式：PNG（无损）或 JPEG（有损但体积小）
- 最大文件大小：建议不超过 4MB

### 4.4 Base64 编码

图片必须使用完整的 Data URL 格式：
```
data:image/png;base64,iVBORw0KGgo...
```
