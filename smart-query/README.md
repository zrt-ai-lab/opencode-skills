# Smart Query

数据库智能查询技能，支持 SSH 隧道连接。

## 依赖

```bash
pip install pymysql paramiko sshtunnel
```

## 配置

编辑 `config/settings.json`，填写数据库连接信息：

```json
{
  "ssh": {
    "host": "跳板机地址",
    "port": 22,
    "user": "用户名",
    "key_path": "~/.ssh/id_rsa"
  },
  "database": {
    "host": "数据库地址",
    "port": 3306,
    "user": "数据库用户",
    "password": "密码",
    "database": "数据库名"
  }
}
```

## 功能

- 执行 SQL 查询
- 自然语言转 SQL
- 生成表结构文档
