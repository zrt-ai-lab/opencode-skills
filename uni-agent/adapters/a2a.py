"""
A2A (Agent-to-Agent) 适配器
Google 提出的 Agent 间协作协议

参考: https://github.com/google/a2a
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from .base import ProtocolAdapter, Connection, AgentInfo


class A2AAdapter(ProtocolAdapter):
    """A2A 协议适配器"""
    
    protocol_name = "a2a"
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self._agent_cards: Dict[str, dict] = {}
    
    async def _fetch_agent_card(self, endpoint: str) -> dict:
        """获取 Agent Card"""
        if endpoint in self._agent_cards:
            return self._agent_cards[endpoint]
        
        agent_json_url = endpoint.rstrip("/")
        if not agent_json_url.endswith("agent.json"):
            agent_json_url = f"{agent_json_url}/.well-known/agent.json"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(agent_json_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    card = await resp.json()
                    self._agent_cards[endpoint] = card
                    return card
                raise Exception(f"获取 Agent Card 失败: HTTP {resp.status}")
    
    async def connect(self, agent_config: dict) -> Connection:
        """建立连接"""
        endpoint = agent_config.get("endpoint")
        if not endpoint:
            raise ValueError("A2A Agent 配置必须包含 endpoint")
        
        agent_card = await self._fetch_agent_card(endpoint)
        
        rpc_url = None
        if "url" in agent_card:
            rpc_url = agent_card["url"]
        elif "capabilities" in agent_card:
            caps = agent_card.get("capabilities", {})
            if "streaming" in caps:
                rpc_url = caps.get("streaming", {}).get("streamingUrl")
        
        if not rpc_url:
            rpc_url = endpoint.rstrip("/") + "/rpc"
        
        return Connection(
            agent_id=agent_config.get("id", ""),
            protocol=self.protocol_name,
            endpoint=rpc_url,
            session=None,
            metadata={
                "agent_card": agent_card,
                "original_endpoint": endpoint,
                "auth": agent_config.get("auth", {}),
            }
        )
    
    async def call(
        self, 
        connection: Connection, 
        method: str, 
        params: dict,
        timeout: float = 30.0
    ) -> dict:
        """调用 A2A Agent 方法"""
        rpc_url = connection.endpoint
        auth_config = connection.metadata.get("auth", {})
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if auth_config.get("type") == "api_key":
            headers["Authorization"] = f"Bearer {auth_config.get('api_key', '')}"
        elif auth_config.get("type") == "oauth2":
            token = await self._get_oauth_token(auth_config)
            headers["Authorization"] = f"Bearer {token}"
        
        task_id = str(uuid.uuid4())
        
        if method == "tasks/send":
            payload = {
                "jsonrpc": "2.0",
                "id": task_id,
                "method": "tasks/send",
                "params": {
                    "id": task_id,
                    "message": params.get("message", {}),
                }
            }
        elif method == "tasks/get":
            payload = {
                "jsonrpc": "2.0",
                "id": task_id,
                "method": "tasks/get",
                "params": {
                    "id": params.get("task_id", task_id),
                }
            }
        else:
            payload = {
                "jsonrpc": "2.0",
                "id": task_id,
                "method": method,
                "params": params,
            }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                rpc_url,
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return {
                        "success": True,
                        "result": result.get("result", result),
                        "task_id": task_id,
                    }
                else:
                    error_text = await resp.text()
                    return {
                        "success": False,
                        "error": f"HTTP {resp.status}: {error_text}",
                    }
    
    async def _get_oauth_token(self, auth_config: dict) -> str:
        """获取 OAuth2 令牌"""
        token_url = auth_config.get("token_url")
        client_id = auth_config.get("client_id")
        client_secret = auth_config.get("client_secret")
        
        if not all([token_url, client_id, client_secret]):
            raise ValueError("OAuth2 配置不完整")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                }
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    return result.get("access_token", "")
                raise Exception(f"获取 OAuth2 令牌失败: HTTP {resp.status}")
    
    async def discover(self, capability: str = "") -> List[AgentInfo]:
        """发现 Agent"""
        agents_file = self.config_dir / "agents.yaml"
        if not agents_file.exists():
            return []
        
        import yaml
        with open(agents_file) as f:
            config = yaml.safe_load(f)
        
        agents = []
        for agent in config.get("agents", []):
            if agent.get("protocol") != "a2a":
                continue
            
            if capability and capability.lower() not in agent.get("id", "").lower():
                continue
            
            agents.append(AgentInfo(
                id=f"{agent['id']}@a2a",
                protocol="a2a",
                name=agent.get("name", agent["id"]),
                endpoint=agent.get("endpoint", ""),
                metadata=agent
            ))
        
        return agents
    
    async def close(self, connection: Connection):
        """关闭连接"""
        pass
    
    async def get_methods(self, connection: Connection) -> List[dict]:
        """获取 Agent 支持的方法（从 Agent Card 的 skills）"""
        agent_card = connection.metadata.get("agent_card", {})
        skills = agent_card.get("skills", [])
        
        methods = []
        for skill in skills:
            methods.append({
                "name": skill.get("id", skill.get("name", "unknown")),
                "description": skill.get("description", ""),
                "inputSchema": skill.get("inputSchema", {}),
                "outputSchema": skill.get("outputSchema", {}),
            })
        
        methods.extend([
            {"name": "tasks/send", "description": "发送任务消息"},
            {"name": "tasks/get", "description": "获取任务状态"},
            {"name": "tasks/cancel", "description": "取消任务"},
        ])
        
        return methods
    
    def validate_config(self, agent_config: dict) -> bool:
        """验证配置"""
        return "endpoint" in agent_config
