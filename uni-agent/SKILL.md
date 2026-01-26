---
name: uni-agent
description: 统一智能体协议适配层。一套 API 调用所有 Agent 协议（ANP/MCP/A2A/AITP 等）。当用户需要调用 Agent、跨协议通信、连接工具时触发此技能。
---

# UniAgent - 统一智能体协议适配层

"Connect Any Agent, Any Protocol"

## 设计理念

### 问题
当前 Agent 协议生态割裂：
- **MCP**：Anthropic 的工具调用协议
- **A2A**：Google 的 Agent 间协作协议
- **ANP**：去中心化身份 + Agent 网络协议
- **AITP**：NEAR 的交互交易协议
- ...

开发者需要为每个协议学习不同的 SDK、实现不同的调用逻辑。

### 解决方案
UniAgent 提供统一抽象层，一套 API 适配所有协议：

```python
from uni_agent import UniAgent

agent = UniAgent()

# 调用 ANP Agent
agent.call("amap@anp", "maps_weather", {"city": "北京"})

# 调用 MCP Server
agent.call("filesystem@mcp", "read_file", {"path": "/tmp/a.txt"})

# 调用 A2A Agent
agent.call("assistant@a2a", "chat", {"message": "hello"})

# 调用 AITP Agent（带支付）
agent.call("shop@aitp", "purchase", {"item": "coffee", "amount": 10})
```

## 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                      UniAgent                           │
│                   统一调用接口                            │
├─────────────────────────────────────────────────────────┤
│  call(agent_id, method, params) -> result               │
│  discover(capability) -> List[Agent]                    │
│  connect(agent_id) -> Connection                        │
└────────────────────────┬────────────────────────────────┘
                         │
              ┌──────────┴──────────┐
              │   Protocol Router   │
              │   协议路由 & 适配    │
              └──────────┬──────────┘
                         │
   ┌─────────┬───────────┼───────────┬─────────┐
   ▼         ▼           ▼           ▼         ▼
┌──────┐ ┌──────┐   ┌──────┐   ┌──────┐  ┌──────┐
│ ANP  │ │ MCP  │   │ A2A  │   │ AITP │  │ ...  │
│Adapter│ │Adapter│  │Adapter│  │Adapter│ │Adapter│
└──────┘ └──────┘   └──────┘   └──────┘  └──────┘
```

## 核心概念

### 1. Agent ID 格式
```
<agent_name>@<protocol>

示例：
- amap@anp          # ANP 协议的高德地图 Agent
- filesystem@mcp   # MCP 协议的文件系统 Server
- gemini@a2a       # A2A 协议的 Gemini Agent
- shop@aitp        # AITP 协议的商店 Agent
```

### 2. 统一调用接口
```python
result = agent.call(
    agent_id="amap@anp",      # Agent 标识
    method="maps_weather",     # 方法名
    params={"city": "北京"},   # 参数
    timeout=30                 # 可选超时
)
```

### 3. 能力发现
```python
# 发现所有能提供天气服务的 Agent
agents = agent.discover("weather")
# 返回: [
#   {"id": "amap@anp", "protocol": "anp", "methods": [...]},
#   {"id": "weather@mcp", "protocol": "mcp", "methods": [...]}
# ]
```

### 4. 协议适配器接口
```python
class ProtocolAdapter(ABC):
    """协议适配器基类"""
    
    @abstractmethod
    def connect(self, agent_config: dict) -> Connection:
        """建立连接"""
        pass
    
    @abstractmethod
    def call(self, connection: Connection, method: str, params: dict) -> dict:
        """调用方法"""
        pass
    
    @abstractmethod
    def discover(self, capability: str) -> List[AgentInfo]:
        """发现 Agent"""
        pass
    
    @abstractmethod
    def close(self, connection: Connection):
        """关闭连接"""
        pass
```

## 支持的协议

| 协议 | 状态 | 适配器 | 说明 |
|------|------|--------|------|
| ANP | ✅ 已实现 | `adapters/anp.py` | 去中心化身份 + Agent 网络 |
| MCP | ✅ 已实现 | `adapters/mcp.py` | LLM 工具调用 |
| A2A | 🚧 开发中 | `adapters/a2a.py` | Agent 间协作 |
| AITP | 📋 计划中 | `adapters/aitp.py` | 交互 + 交易 |
| Agent Protocol | 📋 计划中 | `adapters/agent_protocol.py` | REST API |
| LMOS | 📋 计划中 | `adapters/lmos.py` | 企业级平台 |

## 使用方式

### CLI 调用

```bash
# 调用 ANP Agent
python scripts/uni_cli.py call amap@anp maps_weather '{"city":"北京"}'

# 调用 MCP Server
python scripts/uni_cli.py call filesystem@mcp read_file '{"path":"/tmp/a.txt"}'

# 发现 Agent
python scripts/uni_cli.py discover weather

# 列出已注册 Agent
python scripts/uni_cli.py list
```

### Python SDK

```python
from uni_agent import UniAgent

# 初始化
agent = UniAgent(config_path="config/agents.yaml")

# 调用
result = agent.call("amap@anp", "maps_weather", {"city": "北京"})
print(result)

# 批量调用
results = agent.batch_call([
    ("amap@anp", "maps_weather", {"city": "北京"}),
    ("amap@anp", "maps_weather", {"city": "上海"}),
])
```

## 配置文件

### config/agents.yaml
```yaml
agents:
  # ANP Agents
  - id: amap
    protocol: anp
    ad_url: https://agent-connect.ai/mcp/agents/amap/ad.json
    
  - id: hotel
    protocol: anp
    ad_url: https://agent-connect.ai/agents/hotel-assistant/ad.json

  # MCP Servers
  - id: filesystem
    protocol: mcp
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    
  - id: github
    protocol: mcp
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"

  # A2A Agents
  - id: assistant
    protocol: a2a
    endpoint: https://example.com/.well-known/agent.json
```

### config/identity.yaml
```yaml
# 身份配置（跨协议通用）
identity:
  # ANP DID 身份
  anp:
    did_document: config/did.json
    private_key: config/private-key.pem
  
  # A2A 认证
  a2a:
    auth_type: oauth2
    client_id: "${A2A_CLIENT_ID}"
    client_secret: "${A2A_CLIENT_SECRET}"
```

## 目录结构

```
uni-agent/
├── SKILL.md                 # 本文件
├── README.md                # 使用文档
├── setup.sh                 # 一键安装
├── requirements.txt         # Python 依赖
├── config/
│   ├── agents.yaml          # Agent 注册表
│   ├── identity.yaml        # 身份配置
│   └── .gitignore
├── adapters/
│   ├── __init__.py
│   ├── base.py              # 适配器基类
│   ├── anp.py               # ANP 适配器
│   ├── mcp.py               # MCP 适配器
│   ├── a2a.py               # A2A 适配器
│   └── aitp.py              # AITP 适配器
├── scripts/
│   └── uni_cli.py           # CLI 工具
└── docs/
    ├── architecture.md      # 架构文档
    └── adapters.md          # 适配器开发指南
```

## 扩展新协议

1. 创建适配器文件 `adapters/new_protocol.py`
2. 继承 `ProtocolAdapter` 基类
3. 实现 `connect`、`call`、`discover`、`close` 方法
4. 在 `adapters/__init__.py` 注册

```python
# adapters/new_protocol.py
from .base import ProtocolAdapter

class NewProtocolAdapter(ProtocolAdapter):
    protocol_name = "new_protocol"
    
    def connect(self, agent_config):
        # 实现连接逻辑
        pass
    
    def call(self, connection, method, params):
        # 实现调用逻辑
        pass
    
    # ...
```

## 依赖

```bash
pip install anp aiohttp mcp pyyaml
```
