"""
MCP (Model Context Protocol) 适配器
"""

import asyncio
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import ProtocolAdapter, Connection, AgentInfo

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    HAS_MCP = True
except ImportError:
    HAS_MCP = False


class MCPAdapter(ProtocolAdapter):
    """MCP 协议适配器"""
    
    protocol_name = "mcp"
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self._sessions: Dict[str, Any] = {}
    
    async def connect(self, agent_config: dict) -> Connection:
        """建立连接"""
        if not HAS_MCP:
            raise ImportError("请安装 mcp 库: pip install mcp")
        
        command = agent_config.get("command")
        args = agent_config.get("args", [])
        env = agent_config.get("env", {})
        
        if not command:
            raise ValueError("MCP Agent 配置必须包含 command")
        
        full_env = os.environ.copy()
        for k, v in env.items():
            if v.startswith("${") and v.endswith("}"):
                env_var = v[2:-1]
                full_env[k] = os.environ.get(env_var, "")
            else:
                full_env[k] = v
        
        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=full_env
        )
        
        read, write = await stdio_client(server_params).__aenter__()
        session = ClientSession(read, write)
        await session.__aenter__()
        await session.initialize()
        
        agent_id = agent_config.get("id", "")
        self._sessions[agent_id] = {
            "session": session,
            "read": read,
            "write": write,
        }
        
        return Connection(
            agent_id=agent_id,
            protocol=self.protocol_name,
            endpoint=f"{command} {' '.join(args)}",
            session=session,
            metadata=agent_config
        )
    
    async def call(
        self, 
        connection: Connection, 
        method: str, 
        params: dict,
        timeout: float = 30.0
    ) -> dict:
        """调用 MCP 工具"""
        session: ClientSession = connection.session
        
        result = await asyncio.wait_for(
            session.call_tool(method, params),
            timeout=timeout
        )
        
        if hasattr(result, "content"):
            content = result.content
            if isinstance(content, list) and len(content) > 0:
                first = content[0]
                if hasattr(first, "text"):
                    return {"success": True, "result": first.text}
                return {"success": True, "result": str(first)}
            return {"success": True, "result": content}
        
        return {"success": True, "result": result}
    
    async def discover(self, capability: str = "") -> List[AgentInfo]:
        """发现 Agent（从本地配置）"""
        agents_file = self.config_dir / "agents.yaml"
        if not agents_file.exists():
            return []
        
        import yaml
        with open(agents_file) as f:
            config = yaml.safe_load(f)
        
        agents = []
        for agent in config.get("agents", []):
            if agent.get("protocol") != "mcp":
                continue
            
            if capability and capability.lower() not in agent.get("id", "").lower():
                continue
            
            agents.append(AgentInfo(
                id=f"{agent['id']}@mcp",
                protocol="mcp",
                name=agent.get("name", agent["id"]),
                endpoint=f"{agent.get('command', '')} {' '.join(agent.get('args', []))}",
                metadata=agent
            ))
        
        return agents
    
    async def close(self, connection: Connection):
        """关闭连接"""
        agent_id = connection.agent_id
        if agent_id in self._sessions:
            session_info = self._sessions.pop(agent_id)
            session = session_info.get("session")
            if session:
                await session.__aexit__(None, None, None)
    
    async def get_methods(self, connection: Connection) -> List[dict]:
        """获取 MCP Server 支持的工具"""
        session: ClientSession = connection.session
        
        result = await session.list_tools()
        
        tools = []
        if hasattr(result, "tools"):
            for tool in result.tools:
                tools.append({
                    "name": tool.name,
                    "description": getattr(tool, "description", ""),
                    "inputSchema": getattr(tool, "inputSchema", {}),
                })
        
        return tools
    
    def validate_config(self, agent_config: dict) -> bool:
        """验证配置"""
        return "command" in agent_config
