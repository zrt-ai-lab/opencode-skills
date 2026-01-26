#!/usr/bin/env python3
"""
UniAgent CLI - 统一智能体协议调用工具

用法：
    # 调用 Agent
    python uni_cli.py call amap@anp maps_weather '{"city":"北京"}'
    python uni_cli.py call filesystem@mcp read_file '{"path":"/tmp/a.txt"}'
    
    # 发现 Agent
    python uni_cli.py discover weather
    
    # 列出已注册 Agent
    python uni_cli.py list
    
    # 查看 Agent 方法
    python uni_cli.py methods amap@anp
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from adapters import get_adapter, ADAPTERS


CONFIG_DIR = Path(__file__).parent.parent / "config"


def load_agents_config():
    """加载 Agent 配置"""
    agents_file = CONFIG_DIR / "agents.yaml"
    if not agents_file.exists():
        return {"agents": []}
    
    with open(agents_file) as f:
        return yaml.safe_load(f) or {"agents": []}


def parse_agent_id(agent_id: str) -> tuple:
    """解析 Agent ID，返回 (name, protocol)"""
    if "@" not in agent_id:
        return agent_id, "anp"
    
    parts = agent_id.rsplit("@", 1)
    return parts[0], parts[1]


def get_agent_config(agent_name: str, protocol: str) -> dict:
    """获取 Agent 配置"""
    config = load_agents_config()
    
    for agent in config.get("agents", []):
        if agent.get("id") == agent_name and agent.get("protocol") == protocol:
            return agent
    
    raise ValueError(f"未找到 Agent: {agent_name}@{protocol}")


async def call_agent(agent_id: str, method: str, params: dict):
    """调用 Agent"""
    agent_name, protocol = parse_agent_id(agent_id)
    
    print(f"协议: {protocol}")
    print(f"Agent: {agent_name}")
    print(f"方法: {method}")
    print(f"参数: {json.dumps(params, ensure_ascii=False)}")
    print()
    
    agent_config = get_agent_config(agent_name, protocol)
    adapter = get_adapter(protocol)
    
    connection = await adapter.connect(agent_config)
    
    try:
        result = await adapter.call(connection, method, params)
        print("=== 结果 ===")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        await adapter.close(connection)


async def discover_agents(capability: str = ""):
    """发现 Agent"""
    print(f"搜索能力: {capability or '全部'}\n")
    
    all_agents = []
    
    for protocol, adapter_class in ADAPTERS.items():
        adapter = adapter_class()
        agents = await adapter.discover(capability)
        all_agents.extend(agents)
    
    if not all_agents:
        print("未找到匹配的 Agent")
        return
    
    print(f"找到 {len(all_agents)} 个 Agent:\n")
    for agent in all_agents:
        print(f"  {agent.id}")
        print(f"      名称: {agent.name}")
        print(f"      协议: {agent.protocol}")
        if agent.endpoint:
            print(f"      端点: {agent.endpoint[:60]}...")
        print()


async def list_agents():
    """列出所有已注册 Agent"""
    config = load_agents_config()
    agents = config.get("agents", [])
    
    if not agents:
        print("暂无已注册的 Agent")
        print("请编辑 config/agents.yaml 添加 Agent")
        return
    
    print(f"\n已注册的 Agent ({len(agents)} 个):\n")
    
    by_protocol = {}
    for agent in agents:
        protocol = agent.get("protocol", "unknown")
        if protocol not in by_protocol:
            by_protocol[protocol] = []
        by_protocol[protocol].append(agent)
    
    for protocol, protocol_agents in by_protocol.items():
        print(f"[{protocol.upper()}]")
        for agent in protocol_agents:
            agent_id = f"{agent['id']}@{protocol}"
            name = agent.get("name", agent["id"])
            print(f"  {agent_id}: {name}")
        print()


async def show_methods(agent_id: str):
    """显示 Agent 支持的方法"""
    agent_name, protocol = parse_agent_id(agent_id)
    
    print(f"获取 {agent_name}@{protocol} 的方法列表...\n")
    
    agent_config = get_agent_config(agent_name, protocol)
    adapter = get_adapter(protocol)
    
    connection = await adapter.connect(agent_config)
    
    try:
        methods = await adapter.get_methods(connection)
        
        if not methods:
            print("未获取到方法列表")
            return
        
        print(f"可用方法 ({len(methods)} 个):\n")
        for m in methods[:30]:
            name = m.get("name", "unknown")
            desc = m.get("description", "")[:50]
            print(f"  - {name}: {desc}")
        
        if len(methods) > 30:
            print(f"  ... 还有 {len(methods) - 30} 个方法")
    finally:
        await adapter.close(connection)


def show_help():
    print("""
UniAgent - 统一智能体协议调用工具

用法:
    python uni_cli.py <命令> [参数...]

命令:
    call <agent_id> <method> <params>   调用 Agent 方法
    discover [capability]               发现 Agent
    list                                列出已注册 Agent
    methods <agent_id>                  查看 Agent 方法

Agent ID 格式:
    <name>@<protocol>
    
    示例:
    - amap@anp          ANP 协议的高德地图
    - filesystem@mcp   MCP 协议的文件系统

支持的协议:
    - anp             ANP (Agent Network Protocol) - 去中心化 Agent 网络
    - mcp             MCP (Model Context Protocol) - LLM 工具调用
    - a2a             A2A (Agent-to-Agent) - Google Agent 协作
    - aitp            AITP (Agent Interaction & Transaction) - 交互交易
    - agent_protocol  Agent Protocol - REST API 标准 (别名: ap)
    - lmos            LMOS (Language Model OS) - 企业级 Agent 平台

示例:
    # ANP - 查天气
    python uni_cli.py call amap@anp maps_weather '{"city":"北京"}'
    
    # MCP - 读文件
    python uni_cli.py call filesystem@mcp read_file '{"path":"/tmp/a.txt"}'
    
    # A2A - 发送任务
    python uni_cli.py call assistant@a2a tasks/send '{"message":{"content":"hello"}}'
    
    # AITP - 对话
    python uni_cli.py call shop@aitp message '{"content":"我要买咖啡"}'
    
    # Agent Protocol - 创建任务
    python uni_cli.py call autogpt@ap create_task '{"input":"写代码"}'
    
    # 发现 Agent
    python uni_cli.py discover weather
""")


async def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    cmd = sys.argv[1]
    
    if cmd in ["help", "-h", "--help"]:
        show_help()
    
    elif cmd == "call":
        if len(sys.argv) < 5:
            print("用法: python uni_cli.py call <agent_id> <method> '<params_json>'")
            return
        agent_id = sys.argv[2]
        method = sys.argv[3]
        params = json.loads(sys.argv[4])
        await call_agent(agent_id, method, params)
    
    elif cmd == "discover":
        capability = sys.argv[2] if len(sys.argv) > 2 else ""
        await discover_agents(capability)
    
    elif cmd == "list":
        await list_agents()
    
    elif cmd == "methods":
        if len(sys.argv) < 3:
            print("用法: python uni_cli.py methods <agent_id>")
            return
        await show_methods(sys.argv[2])
    
    else:
        print(f"未知命令: {cmd}")
        show_help()


if __name__ == "__main__":
    asyncio.run(main())
