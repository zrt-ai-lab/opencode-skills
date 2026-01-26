---
name: smart-query
description: 智能数据库查询技能。通过SSH隧道连接线上数据库，支持自然语言转SQL、执行查询、表结构探索。当用户需要查询数据库、问数据、看表结构时使用此技能。
---

# Smart Query - 智能问数

通过 SSH 隧道安全连接线上数据库，支持自然语言查询和 SQL 执行。

## 触发场景

- 用户问"查一下xxx数据"、"帮我看看xxx表"
- 用户需要查询线上数据库
- 用户问"有哪些表"、"表结构是什么"

## 快速使用

### 1. 测试连接

```bash
python .opencode/skills/smart-query/scripts/db_connector.py
```

### 2. 执行SQL查询

```bash
python .opencode/skills/smart-query/scripts/query.py "SELECT * FROM table_name LIMIT 10"
python .opencode/skills/smart-query/scripts/query.py "SHOW TABLES"
python .opencode/skills/smart-query/scripts/query.py "DESC table_name"
```

参数：
- `-n 50`：限制返回行数
- `-f json`：JSON格式输出
- `--raw`：输出原始结果（含元信息）

### 3. 生成表结构文档

```bash
python .opencode/skills/smart-query/scripts/schema_loader.py
```

生成 `references/schema.md`，包含所有表结构信息。

## 自然语言查询流程

1. **理解用户意图**：分析用户想查什么数据
2. **查阅表结构**：读取 `references/schema.md` 了解表结构
3. **生成SQL**：根据表结构编写正确的SQL
4. **执行查询**：使用 `query.py` 执行
5. **解读结果**：用通俗语言解释查询结果

## 配置说明

配置文件：`config/settings.json`

```json
{
  "ssh": {
    "host": "SSH跳板机地址",
    "port": 22,
    "username": "用户名",
    "password": "密码",
    "key_file": null
  },
  "database": {
    "type": "mysql",
    "host": "数据库内网地址",
    "port": 3306,
    "database": "库名",
    "username": "数据库用户",
    "password": "数据库密码"
  }
}
```

## 分享给同事

1. 复制整个 `smart-query/` 目录
2. 同事复制 `config/settings.json.example` 为 `settings.json`
3. 填入自己的 SSH 和数据库连接信息
4. 安装依赖：`pip install paramiko sshtunnel pymysql`

## 安全提示

- `config/settings.json` 包含敏感信息，**不要提交到 Git**
- 建议将 `config/settings.json` 加入 `.gitignore`
- 只执行 SELECT 查询，避免 UPDATE/DELETE 操作

## 依赖安装

```bash
pip install paramiko sshtunnel pymysql
```

## 脚本清单

| 脚本 | 用途 |
|------|------|
| `scripts/db_connector.py` | SSH隧道+数据库连接，可单独运行测试连接 |
| `scripts/query.py` | 执行SQL查询，支持表格/JSON输出 |
| `scripts/schema_loader.py` | 加载表结构，生成 schema.md |

## 参考文档

| 文档 | 说明 |
|------|------|
| `references/schema.md` | 数据库表结构（运行 schema_loader.py 生成） |
