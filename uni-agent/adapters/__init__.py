"""
UniAgent 协议适配器

支持的协议:
- ANP: Agent Network Protocol (去中心化身份 + Agent 网络)
- MCP: Model Context Protocol (LLM 工具调用)
- A2A: Agent-to-Agent (Google Agent 间协作)
- AITP: Agent Interaction & Transaction Protocol (交互 + 交易)
- Agent Protocol: 统一 REST API
- LMOS: Language Model OS (企业级 Agent 平台)
"""

from .base import ProtocolAdapter, Connection, AgentInfo
from .anp import ANPAdapter
from .mcp import MCPAdapter
from .a2a import A2AAdapter
from .aitp import AITPAdapter
from .agent_protocol import AgentProtocolAdapter
from .lmos import LMOSAdapter

ADAPTERS = {
    "anp": ANPAdapter,
    "mcp": MCPAdapter,
    "a2a": A2AAdapter,
    "aitp": AITPAdapter,
    "agent_protocol": AgentProtocolAdapter,
    "ap": AgentProtocolAdapter,
    "lmos": LMOSAdapter,
}

def get_adapter(protocol: str) -> ProtocolAdapter:
    """获取协议适配器"""
    adapter_class = ADAPTERS.get(protocol)
    if not adapter_class:
        raise ValueError(f"不支持的协议: {protocol}，可用协议: {list(ADAPTERS.keys())}")
    return adapter_class()

def register_adapter(protocol: str, adapter_class: type):
    """注册新的协议适配器"""
    ADAPTERS[protocol] = adapter_class

def list_protocols() -> list:
    """列出所有支持的协议"""
    return list(set(ADAPTERS.keys()))

__all__ = [
    "ProtocolAdapter",
    "Connection",
    "AgentInfo",
    "ANPAdapter",
    "MCPAdapter",
    "A2AAdapter",
    "AITPAdapter",
    "AgentProtocolAdapter",
    "LMOSAdapter",
    "get_adapter",
    "register_adapter",
    "list_protocols",
    "ADAPTERS",
]
