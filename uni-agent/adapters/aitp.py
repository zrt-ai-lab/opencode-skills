"""
AITP (Agent Interaction & Transaction Protocol) 适配器
NEAR 基金会提出的 Agent 交互与交易协议

参考: https://aitp.dev
"""

import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from .base import ProtocolAdapter, Connection, AgentInfo


class AITPAdapter(ProtocolAdapter):
    """AITP 协议适配器"""
    
    protocol_name = "aitp"
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self._threads: Dict[str, dict] = {}
    
    async def connect(self, agent_config: dict) -> Connection:
        """建立连接 - 创建 Thread"""
        endpoint = agent_config.get("endpoint")
        if not endpoint:
            raise ValueError("AITP Agent 配置必须包含 endpoint")
        
        thread_id = str(uuid.uuid4())
        
        self._threads[thread_id] = {
            "id": thread_id,
            "messages": [],
            "status": "open",
        }
        
        return Connection(
            agent_id=agent_config.get("id", ""),
            protocol=self.protocol_name,
            endpoint=endpoint,
            session=thread_id,
            metadata={
                "thread_id": thread_id,
                "wallet": agent_config.get("wallet", {}),
            }
        )
    
    async def call(
        self, 
        connection: Connection, 
        method: str, 
        params: dict,
        timeout: float = 30.0
    ) -> dict:
        """调用 AITP Agent"""
        endpoint = connection.endpoint
        thread_id = connection.session
        wallet_config = connection.metadata.get("wallet", {})
        
        headers = {
            "Content-Type": "application/json",
        }
        
        if method == "message":
            payload = {
                "thread_id": thread_id,
                "message": {
                    "role": "user",
                    "content": params.get("content", ""),
                    "parts": params.get("parts", []),
                }
            }
        elif method == "payment":
            payload = {
                "thread_id": thread_id,
                "capability": "aitp-01",
                "payment_request": {
                    "amount": params.get("amount"),
                    "currency": params.get("currency", "NEAR"),
                    "recipient": params.get("recipient"),
                    "memo": params.get("memo", ""),
                }
            }
            
            if wallet_config.get("type") == "near":
                payload["wallet"] = {
                    "type": "near",
                    "account_id": wallet_config.get("account_id"),
                }
        elif method == "decision":
            payload = {
                "thread_id": thread_id,
                "capability": "aitp-02",
                "decision_request": {
                    "question": params.get("question"),
                    "options": params.get("options", []),
                    "allow_custom": params.get("allow_custom", False),
                }
            }
        elif method == "data_request":
            payload = {
                "thread_id": thread_id,
                "capability": "aitp-03",
                "data_request": {
                    "schema": params.get("schema", {}),
                    "description": params.get("description", ""),
                }
            }
        else:
            payload = {
                "thread_id": thread_id,
                "method": method,
                "params": params,
            }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{endpoint}/threads/{thread_id}/messages",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    
                    if thread_id in self._threads:
                        self._threads[thread_id]["messages"].append(payload)
                        self._threads[thread_id]["messages"].append(result)
                    
                    return {
                        "success": True,
                        "result": result,
                        "thread_id": thread_id,
                    }
                else:
                    error_text = await resp.text()
                    return {
                        "success": False,
                        "error": f"HTTP {resp.status}: {error_text}",
                    }
    
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
            if agent.get("protocol") != "aitp":
                continue
            
            if capability and capability.lower() not in agent.get("id", "").lower():
                continue
            
            agents.append(AgentInfo(
                id=f"{agent['id']}@aitp",
                protocol="aitp",
                name=agent.get("name", agent["id"]),
                endpoint=agent.get("endpoint", ""),
                metadata=agent
            ))
        
        return agents
    
    async def close(self, connection: Connection):
        """关闭连接 - 关闭 Thread"""
        thread_id = connection.session
        if thread_id in self._threads:
            self._threads[thread_id]["status"] = "closed"
    
    async def get_methods(self, connection: Connection) -> List[dict]:
        """获取支持的方法（AITP 能力）"""
        return [
            {
                "name": "message",
                "description": "发送对话消息",
                "inputSchema": {"content": "string"},
            },
            {
                "name": "payment",
                "description": "AITP-01: 发起支付请求",
                "inputSchema": {
                    "amount": "number",
                    "currency": "string",
                    "recipient": "string",
                },
            },
            {
                "name": "decision",
                "description": "AITP-02: 请求用户决策",
                "inputSchema": {
                    "question": "string",
                    "options": "array",
                },
            },
            {
                "name": "data_request",
                "description": "AITP-03: 请求结构化数据",
                "inputSchema": {
                    "schema": "object",
                    "description": "string",
                },
            },
        ]
    
    def validate_config(self, agent_config: dict) -> bool:
        """验证配置"""
        return "endpoint" in agent_config
