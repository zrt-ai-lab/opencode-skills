# feishu-doc

飞书文档读写技能，支持 Wiki、Docs、Sheets、Bitable 四种文档类型的读取、创建、写入和追加。

## 能力

| 操作 | 说明 |
|------|------|
| **Read** | 读取 Docs / Sheets / Bitable / Wiki 内容，自动解析 Wiki URL 为实际实体 |
| **Create** | 创建空白文档，返回 doc_token |
| **Write** | 用 Markdown 覆写整篇文档 |
| **Append** | 向文档末尾追加 Markdown 内容 |
| **Blocks** | 列出、获取、更新、删除指定块 |

## 快速开始

```bash
# 读取文档
node index.js --action read --token <doc_token>

# 创建文档
node index.js --action create --title "My Doc"

# 覆写文档
node index.js --action write --token <doc_token> --content "# Title\nHello world"

# 追加内容
node index.js --action append --token <doc_token> --content "## Section 2\nMore text"
```

## 长文档写入

LLM 单次输出有上限（~2000-4000 tokens），超长文档请使用分段追加：

1. `create` 创建文档，获取 `doc_token`
2. 按逻辑章节拆分内容
3. 逐段 `append`，不要用单次 `write` 写完整长文

## 配置

创建 `config.json` 或设置环境变量：

```json
{
  "app_id": "YOUR_APP_ID",
  "app_secret": "YOUR_APP_SECRET"
}
```

环境变量：`FEISHU_APP_ID` / `FEISHU_APP_SECRET`

## 前置依赖

- 需先安装 `feishu-common`（提供 token 和 API 鉴权）
- Node.js 16+

## License

MIT
