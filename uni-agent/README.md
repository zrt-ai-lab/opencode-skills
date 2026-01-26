# UniAgent - 统一智能体协议适配层

"Connect Any Agent, Any Protocol"

一套 API 调用所有 Agent 协议（ANP/MCP/A2A/AITP/LMOS/Agent Protocol）。

## 一键部署

```bash
# 1. 运行安装脚本
./setup.sh

# 2. 开始使用
python scripts/uni_cli.py list
```

## 使用方式

### 调用 Agent

```bash
# Agent ID 格式: <name>@<protocol>

# ANP - 去中心化 Agent 网络
python scripts/uni_cli.py call amap@anp maps_weather '{"city":"北京"}'
python scripts/uni_cli.py call amap@anp maps_text_search '{"keywords":"咖啡厅","city":"上海"}'

# MCP - LLM 工具调用 (需配置)
python scripts/uni_cli.py call filesystem@mcp read_file '{"path":"/tmp/a.txt"}'

# A2A - Google Agent 协作 (需配置)
python scripts/uni_cli.py call assistant@a2a tasks/send '{"message":{"role":"user","content":"hello"}}'

# AITP - NEAR 交互交易 (需配置)
python scripts/uni_cli.py call shop@aitp message '{"content":"我要买咖啡"}'

# Agent Protocol - REST API (需配置)
python scripts/uni_cli.py call autogpt@ap create_task '{"input":"写一个hello world"}'

# LMOS - 企业级 Agent (需配置)
python scripts/uni_cli.py call sales@lmos invoke '{"capability":"sales","input":{}}'
```

### 查看 Agent 方法

```bash
python scripts/uni_cli.py methods amap@anp
```

### 发现 Agent

```bash
python scripts/uni_cli.py discover weather
```

### 列出已注册 Agent

```bash
python scripts/uni_cli.py list
```

## 支持的协议

| 协议 | 状态 | 说明 |
|------|------|------|
| **ANP** | ✅ 已实现 | Agent Network Protocol - 去中心化身份 + Agent 网络 |
| **MCP** | ✅ 已实现 | Model Context Protocol - LLM 工具调用 |
| **A2A** | ✅ 已实现 | Agent-to-Agent - Google 的 Agent 间协作协议 |
| **AITP** | ✅ 已实现 | Agent Interaction & Transaction - 交互 + 交易 |
| **Agent Protocol** | ✅ 已实现 | AI Engineer Foundation REST API 标准 |
| **LMOS** | ✅ 已实现 | Language Model OS - Eclipse 企业级 Agent 平台 |

## 内置 ANP Agent

| ID | 名称 | 功能 |
|----|------|------|
| amap@anp | 高德地图 | 地点搜索、路线规划、天气查询 |
| kuaidi@anp | 快递查询 | 快递单号追踪 |
| hotel@anp | 酒店预订 | 搜索酒店、查询房价 |
| juhe@anp | 聚合查询 | 多种生活服务 |
| navigation@anp | Agent导航 | 发现更多 Agent |

## 添加自定义 Agent

编辑 `config/agents.yaml`:

```yaml
agents:
  # ANP Agent
  - id: my_agent
    protocol: anp
    name: 我的 Agent
    ad_url: https://example.com/ad.json

  # MCP Server
  - id: filesystem
    protocol: mcp
    name: 文件系统
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

  # A2A Agent
  - id: assistant
    protocol: a2a
    name: AI Assistant
    endpoint: https://example.com/.well-known/agent.json
    auth:
      type: api_key
      api_key: "${A2A_API_KEY}"

  # AITP Agent
  - id: shop
    protocol: aitp
    name: NEAR Shop
    endpoint: https://shop.near.ai/api
    wallet:
      type: near
      account_id: "${NEAR_ACCOUNT_ID}"

  # Agent Protocol
  - id: autogpt
    protocol: agent_protocol  # 或 ap
    name: AutoGPT
    endpoint: http://localhost:8000

  # LMOS Agent
  - id: sales
    protocol: lmos
    name: 销售 Agent
    endpoint: http://sales.internal:8080
```

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                      UniAgent                           │
│                   统一调用接口                            │
├─────────────────────────────────────────────────────────┤
│  call(agent_id, method, params) -> result               │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │   Protocol Router   │
              └──────────┬──────────┘
                         │
   ┌─────────┬───────────┼───────────┬─────────┬─────────┐
   ▼         ▼           ▼           ▼         ▼         ▼
┌──────┐ ┌──────┐   ┌──────┐   ┌──────┐  ┌──────┐  ┌──────┐
│ ANP  │ │ MCP  │   │ A2A  │   │ AITP │  │  AP  │  │ LMOS │
└──────┘ └──────┘   └──────┘   └──────┘  └──────┘  └──────┘
```

## 目录结构

```
uni-agent/
├── README.md
├── SKILL.md             # AI 助手技能描述
├── setup.sh             # 一键安装
├── requirements.txt
├── config/
│   ├── agents.yaml      # Agent 注册表
│   └── .gitignore
├── adapters/
│   ├── __init__.py      # 适配器注册
│   ├── base.py          # 适配器基类
│   ├── anp.py           # ANP 适配器
│   ├── mcp.py           # MCP 适配器
│   ├── a2a.py           # A2A 适配器
│   ├── aitp.py          # AITP 适配器
│   ├── agent_protocol.py # Agent Protocol 适配器
│   └── lmos.py          # LMOS 适配器
└── scripts/
    └── uni_cli.py       # CLI 工具
```

## 扩展新协议

1. 创建 `adapters/new_protocol.py`
2. 继承 `ProtocolAdapter` 基类
3. 实现 `connect`、`call`、`discover`、`close` 方法
4. 在 `adapters/__init__.py` 注册

详见 [SKILL.md](SKILL.md)

## License

MIT
