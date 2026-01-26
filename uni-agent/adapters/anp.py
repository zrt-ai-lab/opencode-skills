"""
ANP (Agent Network Protocol) 适配器
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from .base import ProtocolAdapter, Connection, AgentInfo

try:
    from anp.anp_crawler import ANPCrawler
    HAS_ANP = True
except ImportError:
    HAS_ANP = False


class ANPAdapter(ProtocolAdapter):
    """ANP 协议适配器"""
    
    protocol_name = "anp"
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self._crawler = None
        self._ad_cache: Dict[str, dict] = {}
        self._endpoint_cache: Dict[str, str] = {}
    
    def _get_crawler(self) -> "ANPCrawler":
        """获取 ANP Crawler 实例"""
        if not HAS_ANP:
            raise ImportError("请安装 anp 库: pip install anp")
        
        if self._crawler is None:
            did_path = self.config_dir / "did.json"
            key_path = self.config_dir / "private-key.pem"
            
            if did_path.exists() and key_path.exists():
                self._crawler = ANPCrawler(
                    did_document_path=str(did_path),
                    private_key_path=str(key_path)
                )
            else:
                raise FileNotFoundError(
                    f"DID 配置文件不存在: {did_path} 或 {key_path}\n"
                    "请运行 setup.sh 生成本地身份"
                )
        
        return self._crawler
    
    async def _fetch_ad(self, ad_url: str) -> dict:
        """获取 Agent Description 文档"""
        if ad_url in self._ad_cache:
            return self._ad_cache[ad_url]
        
        async with aiohttp.ClientSession() as session:
            async with session.get(ad_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    ad = await resp.json()
                    self._ad_cache[ad_url] = ad
                    return ad
                raise Exception(f"获取 AD 失败: HTTP {resp.status}")
    
    async def _get_endpoint(self, ad_url: str) -> str:
        """从 AD 获取 RPC 端点"""
        if ad_url in self._endpoint_cache:
            return self._endpoint_cache[ad_url]
        
        ad = await self._fetch_ad(ad_url)
        interfaces = ad.get("interfaces", [])
        
        if not interfaces:
            raise ValueError(f"AD 中没有定义接口: {ad_url}")
        
        interface_url = interfaces[0].get("url")
        if not interface_url:
            raise ValueError(f"接口 URL 为空: {ad_url}")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(interface_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    interface_doc = await resp.json()
                    servers = interface_doc.get("servers", [])
                    if servers:
                        endpoint = servers[0].get("url")
                        self._endpoint_cache[ad_url] = endpoint
                        return endpoint
        
        raise ValueError(f"无法获取 RPC 端点: {ad_url}")
    
    async def connect(self, agent_config: dict) -> Connection:
        """建立连接"""
        ad_url = agent_config.get("ad_url")
        if not ad_url:
            raise ValueError("ANP Agent 配置必须包含 ad_url")
        
        ad = await self._fetch_ad(ad_url)
        endpoint = await self._get_endpoint(ad_url)
        
        return Connection(
            agent_id=agent_config.get("id", ""),
            protocol=self.protocol_name,
            endpoint=endpoint,
            session=self._get_crawler(),
            metadata={
                "ad_url": ad_url,
                "ad": ad,
                "name": ad.get("name", ""),
            }
        )
    
    async def call(
        self, 
        connection: Connection, 
        method: str, 
        params: dict,
        timeout: float = 30.0
    ) -> dict:
        """调用 Agent 方法"""
        crawler = connection.session
        endpoint = connection.endpoint
        
        result = await crawler.execute_json_rpc(
            endpoint=endpoint,
            method=method,
            params=params
        )
        
        return result
    
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
            if agent.get("protocol") != "anp":
                continue
            
            if capability and capability.lower() not in agent.get("id", "").lower():
                continue
            
            agents.append(AgentInfo(
                id=f"{agent['id']}@anp",
                protocol="anp",
                name=agent.get("name", agent["id"]),
                endpoint=agent.get("ad_url", ""),
                metadata=agent
            ))
        
        return agents
    
    async def close(self, connection: Connection):
        """关闭连接"""
        pass
    
    async def get_methods(self, connection: Connection) -> List[dict]:
        """获取 Agent 支持的方法"""
        ad_url = connection.metadata.get("ad_url")
        if not ad_url:
            return []
        
        ad = await self._fetch_ad(ad_url)
        interfaces = ad.get("interfaces", [])
        
        if not interfaces:
            return []
        
        interface_url = interfaces[0].get("url")
        if not interface_url:
            return []
        
        async with aiohttp.ClientSession() as session:
            async with session.get(interface_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    interface_doc = await resp.json()
                    return interface_doc.get("methods", [])
        
        return []
    
    def validate_config(self, agent_config: dict) -> bool:
        """验证配置"""
        return "ad_url" in agent_config
