"""
Agent Protocol 适配器
AI Engineer Foundation 提出的 Agent 统一 REST API

参考: https://agentprotocol.ai
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from .base import ProtocolAdapter, Connection, AgentInfo


class AgentProtocolAdapter(ProtocolAdapter):
    """Agent Protocol 适配器"""
    
    protocol_name = "agent_protocol"
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self._tasks: Dict[str, dict] = {}
    
    async def connect(self, agent_config: dict) -> Connection:
        """建立连接"""
        endpoint = agent_config.get("endpoint")
        if not endpoint:
            raise ValueError("Agent Protocol 配置必须包含 endpoint")
        
        endpoint = endpoint.rstrip("/")
        if not endpoint.endswith("/ap/v1"):
            endpoint = f"{endpoint}/ap/v1"
        
        return Connection(
            agent_id=agent_config.get("id", ""),
            protocol=self.protocol_name,
            endpoint=endpoint,
            session=None,
            metadata=agent_config
        )
    
    async def call(
        self, 
        connection: Connection, 
        method: str, 
        params: dict,
        timeout: float = 30.0
    ) -> dict:
        """调用 Agent Protocol API"""
        endpoint = connection.endpoint
        
        headers = {
            "Content-Type": "application/json",
        }
        
        api_key = connection.metadata.get("api_key")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        if method == "create_task":
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{endpoint}/agent/tasks",
                    json={"input": params.get("input", "")},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status in [200, 201]:
                        result = await resp.json()
                        task_id = result.get("task_id")
                        self._tasks[task_id] = result
                        return {"success": True, "result": result, "task_id": task_id}
                    else:
                        return {"success": False, "error": f"HTTP {resp.status}"}
        
        elif method == "execute_step":
            task_id = params.get("task_id")
            if not task_id:
                return {"success": False, "error": "缺少 task_id"}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{endpoint}/agent/tasks/{task_id}/steps",
                    json={"input": params.get("input", "")},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status in [200, 201]:
                        result = await resp.json()
                        return {"success": True, "result": result}
                    else:
                        return {"success": False, "error": f"HTTP {resp.status}"}
        
        elif method == "get_task":
            task_id = params.get("task_id")
            if not task_id:
                return {"success": False, "error": "缺少 task_id"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{endpoint}/agent/tasks/{task_id}",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return {"success": True, "result": result}
                    else:
                        return {"success": False, "error": f"HTTP {resp.status}"}
        
        elif method == "list_tasks":
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{endpoint}/agent/tasks",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return {"success": True, "result": result}
                    else:
                        return {"success": False, "error": f"HTTP {resp.status}"}
        
        elif method == "get_artifacts":
            task_id = params.get("task_id")
            if not task_id:
                return {"success": False, "error": "缺少 task_id"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{endpoint}/agent/tasks/{task_id}/artifacts",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return {"success": True, "result": result}
                    else:
                        return {"success": False, "error": f"HTTP {resp.status}"}
        
        else:
            return {"success": False, "error": f"未知方法: {method}"}
    
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
            if agent.get("protocol") != "agent_protocol":
                continue
            
            if capability and capability.lower() not in agent.get("id", "").lower():
                continue
            
            agents.append(AgentInfo(
                id=f"{agent['id']}@agent_protocol",
                protocol="agent_protocol",
                name=agent.get("name", agent["id"]),
                endpoint=agent.get("endpoint", ""),
                metadata=agent
            ))
        
        return agents
    
    async def close(self, connection: Connection):
        """关闭连接"""
        pass
    
    async def get_methods(self, connection: Connection) -> List[dict]:
        """获取支持的方法"""
        return [
            {
                "name": "create_task",
                "description": "创建新任务",
                "inputSchema": {"input": "string"},
            },
            {
                "name": "execute_step",
                "description": "执行任务步骤",
                "inputSchema": {"task_id": "string", "input": "string"},
            },
            {
                "name": "get_task",
                "description": "获取任务状态",
                "inputSchema": {"task_id": "string"},
            },
            {
                "name": "list_tasks",
                "description": "列出所有任务",
                "inputSchema": {},
            },
            {
                "name": "get_artifacts",
                "description": "获取任务产物",
                "inputSchema": {"task_id": "string"},
            },
        ]
    
    def validate_config(self, agent_config: dict) -> bool:
        """验证配置"""
        return "endpoint" in agent_config
