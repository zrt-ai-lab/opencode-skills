"""
协议适配器基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentInfo:
    """Agent 信息"""
    id: str
    protocol: str
    name: str = ""
    description: str = ""
    methods: List[str] = field(default_factory=list)
    endpoint: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Connection:
    """连接对象"""
    agent_id: str
    protocol: str
    endpoint: str = ""
    session: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_active(self) -> bool:
        return self.session is not None


class ProtocolAdapter(ABC):
    """协议适配器基类"""
    
    protocol_name: str = "base"
    
    @abstractmethod
    async def connect(self, agent_config: dict) -> Connection:
        """
        建立与 Agent 的连接
        
        Args:
            agent_config: Agent 配置信息
            
        Returns:
            Connection 对象
        """
        pass
    
    @abstractmethod
    async def call(
        self, 
        connection: Connection, 
        method: str, 
        params: dict,
        timeout: float = 30.0
    ) -> dict:
        """
        调用 Agent 方法
        
        Args:
            connection: 连接对象
            method: 方法名
            params: 参数
            timeout: 超时时间（秒）
            
        Returns:
            调用结果
        """
        pass
    
    @abstractmethod
    async def discover(self, capability: str = "") -> List[AgentInfo]:
        """
        发现 Agent
        
        Args:
            capability: 能力关键词（可选）
            
        Returns:
            Agent 信息列表
        """
        pass
    
    @abstractmethod
    async def close(self, connection: Connection):
        """
        关闭连接
        
        Args:
            connection: 连接对象
        """
        pass
    
    async def get_methods(self, connection: Connection) -> List[dict]:
        """
        获取 Agent 支持的方法列表
        
        Args:
            connection: 连接对象
            
        Returns:
            方法列表
        """
        return []
    
    def validate_config(self, agent_config: dict) -> bool:
        """
        验证 Agent 配置
        
        Args:
            agent_config: Agent 配置
            
        Returns:
            是否有效
        """
        return True
