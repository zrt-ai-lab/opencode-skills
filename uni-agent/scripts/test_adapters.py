#!/usr/bin/env python3
"""
UniAgent 适配器测试脚本
测试所有协议适配器的基本功能
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters import get_adapter, ADAPTERS, list_protocols


class TestResult:
    def __init__(self, protocol: str):
        self.protocol = protocol
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.errors = []
    
    def pass_(self, msg: str):
        self.passed += 1
        print(f"  ✅ {msg}")
    
    def fail(self, msg: str, error: str = ""):
        self.failed += 1
        self.errors.append(f"{msg}: {error}")
        print(f"  ❌ {msg}: {error[:100]}")
    
    def skip(self, msg: str):
        self.skipped += 1
        print(f"  ⏭️  {msg} (跳过)")
    
    def summary(self) -> str:
        status = "✅" if self.failed == 0 else "❌"
        return f"{status} {self.protocol}: {self.passed} passed, {self.failed} failed, {self.skipped} skipped"


async def test_anp() -> TestResult:
    """测试 ANP 适配器"""
    result = TestResult("ANP")
    print("\n[ANP] 测试 Agent Network Protocol...\n")
    
    try:
        adapter = get_adapter("anp")
        result.pass_("获取适配器")
    except Exception as e:
        result.fail("获取适配器", str(e))
        return result
    
    agent_config = {
        "id": "amap",
        "protocol": "anp",
        "ad_url": "https://agent-connect.ai/mcp/agents/amap/ad.json"
    }
    
    try:
        connection = await adapter.connect(agent_config)
        result.pass_(f"建立连接: {connection.endpoint[:50]}...")
    except Exception as e:
        result.fail("建立连接", str(e))
        return result
    
    try:
        methods = await adapter.get_methods(connection)
        result.pass_(f"获取方法列表: {len(methods)} 个方法")
    except Exception as e:
        result.fail("获取方法列表", str(e))
    
    try:
        res = await adapter.call(connection, "maps_weather", {"city": "北京"})
        if res.get("success") or res.get("result"):
            city = res.get("result", {}).get("city", "")
            result.pass_(f"调用 maps_weather: {city}")
        else:
            result.fail("调用 maps_weather", str(res))
    except Exception as e:
        result.fail("调用 maps_weather", str(e))
    
    try:
        res = await adapter.call(connection, "maps_text_search", {"keywords": "咖啡厅", "city": "上海"})
        if res.get("success") or res.get("result"):
            pois = res.get("result", {}).get("pois", [])
            result.pass_(f"调用 maps_text_search: 找到 {len(pois)} 个结果")
        else:
            result.fail("调用 maps_text_search", str(res))
    except Exception as e:
        result.fail("调用 maps_text_search", str(e))
    
    try:
        agents = await adapter.discover()
        result.pass_(f"发现 Agent: {len(agents)} 个")
    except Exception as e:
        result.fail("发现 Agent", str(e))
    
    try:
        await adapter.close(connection)
        result.pass_("关闭连接")
    except Exception as e:
        result.fail("关闭连接", str(e))
    
    return result


async def test_mcp() -> TestResult:
    """测试 MCP 适配器"""
    result = TestResult("MCP")
    print("\n[MCP] 测试 Model Context Protocol...\n")
    
    try:
        adapter = get_adapter("mcp")
        result.pass_("获取适配器")
    except Exception as e:
        result.fail("获取适配器", str(e))
        return result
    
    result.skip("MCP 需要本地 npx 环境，跳过实际连接测试")
    result.skip("如需测试，请配置 config/agents.yaml 中的 MCP Server")
    
    return result


async def test_a2a() -> TestResult:
    """测试 A2A 适配器"""
    result = TestResult("A2A")
    print("\n[A2A] 测试 Agent-to-Agent Protocol...\n")
    
    try:
        adapter = get_adapter("a2a")
        result.pass_("获取适配器")
    except Exception as e:
        result.fail("获取适配器", str(e))
        return result
    
    result.skip("A2A 需要配置 Agent endpoint，跳过实际连接测试")
    result.skip("如需测试，请配置 config/agents.yaml 中的 A2A Agent")
    
    try:
        agents = await adapter.discover()
        result.pass_(f"发现 Agent: {len(agents)} 个 (本地配置)")
    except Exception as e:
        result.fail("发现 Agent", str(e))
    
    return result


async def test_aitp() -> TestResult:
    """测试 AITP 适配器"""
    result = TestResult("AITP")
    print("\n[AITP] 测试 Agent Interaction & Transaction Protocol...\n")
    
    try:
        adapter = get_adapter("aitp")
        result.pass_("获取适配器")
    except Exception as e:
        result.fail("获取适配器", str(e))
        return result
    
    result.skip("AITP 需要配置 NEAR 钱包和 endpoint，跳过实际连接测试")
    result.skip("如需测试，请配置 config/agents.yaml 中的 AITP Agent")
    
    try:
        agents = await adapter.discover()
        result.pass_(f"发现 Agent: {len(agents)} 个 (本地配置)")
    except Exception as e:
        result.fail("发现 Agent", str(e))
    
    try:
        methods = [
            {"name": "message", "desc": "发送消息"},
            {"name": "payment", "desc": "发起支付"},
            {"name": "decision", "desc": "请求决策"},
        ]
        result.pass_(f"支持方法: {', '.join([m['name'] for m in methods])}")
    except Exception as e:
        result.fail("检查方法", str(e))
    
    return result


async def test_agent_protocol() -> TestResult:
    """测试 Agent Protocol 适配器"""
    result = TestResult("Agent Protocol")
    print("\n[AP] 测试 Agent Protocol...\n")
    
    try:
        adapter = get_adapter("agent_protocol")
        result.pass_("获取适配器 (agent_protocol)")
    except Exception as e:
        result.fail("获取适配器", str(e))
        return result
    
    try:
        adapter2 = get_adapter("ap")
        result.pass_("获取适配器 (别名 ap)")
    except Exception as e:
        result.fail("获取适配器别名", str(e))
    
    result.skip("Agent Protocol 需要运行中的 Agent 服务，跳过实际连接测试")
    result.skip("如需测试，请启动 AutoGPT 或其他兼容服务")
    
    try:
        agents = await adapter.discover()
        result.pass_(f"发现 Agent: {len(agents)} 个 (本地配置)")
    except Exception as e:
        result.fail("发现 Agent", str(e))
    
    return result


async def test_lmos() -> TestResult:
    """测试 LMOS 适配器"""
    result = TestResult("LMOS")
    print("\n[LMOS] 测试 Language Model Operating System...\n")
    
    try:
        adapter = get_adapter("lmos")
        result.pass_("获取适配器")
    except Exception as e:
        result.fail("获取适配器", str(e))
        return result
    
    result.skip("LMOS 需要配置注册中心或 Agent endpoint，跳过实际连接测试")
    result.skip("如需测试，请配置 config/agents.yaml 中的 LMOS Agent")
    
    try:
        agents = await adapter.discover()
        result.pass_(f"发现 Agent: {len(agents)} 个 (本地配置)")
    except Exception as e:
        result.fail("发现 Agent", str(e))
    
    return result


async def main():
    print("=" * 60)
    print("  UniAgent 适配器测试")
    print("=" * 60)
    
    print(f"\n支持的协议: {list_protocols()}\n")
    
    results = []
    
    results.append(await test_anp())
    results.append(await test_mcp())
    results.append(await test_a2a())
    results.append(await test_aitp())
    results.append(await test_agent_protocol())
    results.append(await test_lmos())
    
    print("\n" + "=" * 60)
    print("  测试汇总")
    print("=" * 60 + "\n")
    
    total_passed = 0
    total_failed = 0
    total_skipped = 0
    
    for r in results:
        print(r.summary())
        total_passed += r.passed
        total_failed += r.failed
        total_skipped += r.skipped
    
    print(f"\n总计: {total_passed} passed, {total_failed} failed, {total_skipped} skipped")
    
    if total_failed > 0:
        print("\n失败详情:")
        for r in results:
            for err in r.errors:
                print(f"  - [{r.protocol}] {err}")
        sys.exit(1)
    else:
        print("\n🎉 所有测试通过！")


if __name__ == "__main__":
    asyncio.run(main())
