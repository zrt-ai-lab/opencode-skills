"""
LMOS (Language Model Operating System) 适配器
Eclipse 基金会孵化的企业级多 Agent 平台

参考: https://eclipse.dev/lmos/
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from .base import ProtocolAdapter, Connection, AgentInfo


class LMOSAdapter(ProtocolAdapter):
    """LMOS 协议适配器"""
    
    protocol_name = "lmos"
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self._registry_cache: Dict[str, List[dict]] = {}
    
    async def _discover_via_mdns(self) -> List[dict]:
        """通过 mDNS 发现本地 Agent（简化实现）"""
        return []
    
    async def _query_registry(self, registry_url: str, capability: str = "") -> List[dict]:
        """查询 Agent 注册中心"""
        if registry_url in self._registry_cache:
            return self._registry_cache[registry_url]
        
        async with aiohttp.ClientSession() as session:
            params = {}
            if capability:
                params["capability"] = capability
            
            async with session.get(
                f"{registry_url}/agents",
                params=params,
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    agents = result.get("agents", [])
                    self._registry_cache[registry_url] = agents
                    return agents
                return []
    
    async def connect(self, agent_config: dict) -> Connection:
        """建立连接"""
        endpoint = agent_config.get("endpoint")
        registry_url = agent_config.get("registry_url")
        
        if not endpoint and not registry_url:
            raise ValueError("LMOS Agent 配置必须包含 endpoint 或 registry_url")
        
        if registry_url and not endpoint:
            agent_id = agent_config.get("id")
            agents = await self._query_registry(registry_url)
            for agent in agents:
                if agent.get("id") == agent_id:
                    endpoint = agent.get("endpoint")
                    break
            
            if not endpoint:
                raise ValueError(f"在注册中心未找到 Agent: {agent_id}")
        
        return Connection(
            agent_id=agent_config.get("id", ""),
            protocol=self.protocol_name,
            endpoint=endpoint,
            session=None,
            metadata={
                "registry_url": registry_url,
                "group": agent_config.get("group"),
            }
        )
    
    async def call(
        self, 
        connection: Connection, 
        method: str, 
        params: dict,
        timeout: float = 30.0
    ) -> dict:
        """调用 LMOS Agent"""
        endpoint = connection.endpoint
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if method == "invoke":
            payload = {
                "capability": params.get("capability"),
                "input": params.get("input", {}),
                "context": params.get("context", {}),
            }
        elif method == "route":
            payload = {
                "query": params.get("query"),
                "context": params.get("context", {}),
            }
        elif method == "describe":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{endpoint}/capabilities",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return {"success": True, "result": result}
                    else:
                        return {"success": False, "error": f"HTTP {resp.status}"}
        else:
            payload = {
                "method": method,
                "params": params,
            }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{endpoint}/invoke",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return {"success": True, "result": result}
                else:
                    error_text = await resp.text()
                    return {"success": False, "error": f"HTTP {resp.status}: {error_text}"}
    
    async def discover(self, capability: str = "") -> List[AgentInfo]:
        """发现 Agent"""
        agents_file = self.config_dir / "agents.yaml"
        if not agents_file.exists():
            return []
        
        import yaml
        with open(agents_file) as f:
            config = yaml.safe_load(f)
        
        all_agents = []
        
        for agent in config.get("agents", []):
            if agent.get("protocol") != "lmos":
                continue
            
            if capability and capability.lower() not in agent.get("id", "").lower():
                continue
            
            all_agents.append(AgentInfo(
                id=f"{agent['id']}@lmos",
                protocol="lmos",
                name=agent.get("name", agent["id"]),
                endpoint=agent.get("endpoint", ""),
                metadata=agent
            ))
        
        for agent in config.get("agents", []):
            if agent.get("protocol") != "lmos":
                continue
            
            registry_url = agent.get("registry_url")
            if registry_url:
                try:
                    remote_agents = await self._query_registry(registry_url, capability)
                    for ra in remote_agents:
                        all_agents.append(AgentInfo(
                            id=f"{ra['id']}@lmos",
                            protocol="lmos",
                            name=ra.get("name", ra["id"]),
                            endpoint=ra.get("endpoint", ""),
                            metadata=ra
                        ))
                except Exception:
                    pass
        
        return all_agents
    
    async def close(self, connection: Connection):
        """关闭连接"""
        pass
    
    async def get_methods(self, connection: Connection) -> List[dict]:
        """获取支持的方法"""
        result = await self.call(connection, "describe", {})
        
        if result.get("success"):
            capabilities = result.get("result", {}).get("capabilities", [])
            return [
                {
                    "name": cap.get("id", cap.get("name")),
                    "description": cap.get("description", ""),
                    "inputSchema": cap.get("inputSchema", {}),
                }
                for cap in capabilities
            ]
        
        return [
            {"name": "invoke", "description": "调用 Agent 能力"},
            {"name": "route", "description": "智能路由到最佳 Agent"},
            {"name": "describe", "description": "获取 Agent 能力描述"},
        ]
    
    def validate_config(self, agent_config: dict) -> bool:
        """验证配置"""
        return "endpoint" in agent_config or "registry_url" in agent_config
