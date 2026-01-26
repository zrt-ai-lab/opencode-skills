#!/usr/bin/env python3
"""
UniAgent 完整测试脚本
启动测试服务器，测试所有协议的真实交互
"""

import asyncio
import json
import subprocess
import sys
import time
import signal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters import get_adapter


SERVERS = {}


def start_server(name: str, script: str, port: int) -> subprocess.Popen:
    """启动测试服务器"""
    script_path = Path(__file__).parent.parent / "test_servers" / script
    proc = subprocess.Popen(
        [sys.executable, str(script_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(0.5)
    if proc.poll() is not None:
        stderr = proc.stderr.read().decode()
        print(f"  ❌ {name} 启动失败: {stderr}")
        return None
    print(f"  ✅ {name} 启动成功 (port {port})")
    return proc


def stop_servers():
    """停止所有服务器"""
    for name, proc in SERVERS.items():
        if proc and proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=2)


async def test_anp():
    """测试 ANP 适配器"""
    print("\n" + "=" * 50)
    print("[ANP] Agent Network Protocol")
    print("=" * 50)
    
    adapter = get_adapter("anp")
    config = {
        "id": "amap",
        "protocol": "anp",
        "ad_url": "https://agent-connect.ai/mcp/agents/amap/ad.json"
    }
    
    try:
        conn = await adapter.connect(config)
        print(f"✅ 连接成功: {conn.endpoint[:50]}...")
        
        result = await adapter.call(conn, "maps_weather", {"city": "北京"})
        city = result.get("result", {}).get("city", "")
        print(f"✅ maps_weather: {city}")
        
        result = await adapter.call(conn, "maps_text_search", {"keywords": "咖啡厅", "city": "上海"})
        pois = result.get("result", {}).get("pois", [])
        print(f"✅ maps_text_search: 找到 {len(pois)} 个结果")
        
        await adapter.close(conn)
        print(f"✅ 关闭连接")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def test_a2a():
    """测试 A2A 适配器"""
    print("\n" + "=" * 50)
    print("[A2A] Agent-to-Agent Protocol")
    print("=" * 50)
    
    adapter = get_adapter("a2a")
    config = {
        "id": "test_agent",
        "protocol": "a2a",
        "endpoint": "http://localhost:8100"
    }
    
    try:
        conn = await adapter.connect(config)
        print(f"✅ 连接成功")
        
        methods = await adapter.get_methods(conn)
        print(f"✅ 获取方法: {len(methods)} 个 (包含 skills)")
        
        result = await adapter.call(conn, "tasks/send", {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "Hello A2A!"}]
            }
        })
        if result.get("success"):
            task = result.get("result", {})
            history = task.get("history", [])
            if len(history) >= 2:
                response = history[-1].get("parts", [{}])[0].get("text", "")
                print(f"✅ tasks/send: {response}")
            else:
                print(f"✅ tasks/send: 任务已创建")
        else:
            print(f"❌ tasks/send 失败: {result}")
            return False
        
        await adapter.close(conn)
        print(f"✅ 关闭连接")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def test_aitp():
    """测试 AITP 适配器"""
    print("\n" + "=" * 50)
    print("[AITP] Agent Interaction & Transaction Protocol")
    print("=" * 50)
    
    adapter = get_adapter("aitp")
    config = {
        "id": "test_shop",
        "protocol": "aitp",
        "endpoint": "http://localhost:8101"
    }
    
    try:
        conn = await adapter.connect(config)
        print(f"✅ 连接成功 (Thread: {conn.session[:8]}...)")
        
        result = await adapter.call(conn, "message", {"content": "Hello AITP!"})
        if result.get("success"):
            response = result.get("result", {}).get("content", "")
            print(f"✅ message: {response}")
        else:
            print(f"❌ message 失败")
            return False
        
        result = await adapter.call(conn, "payment", {
            "amount": 10,
            "currency": "NEAR",
            "recipient": "shop.near"
        })
        if result.get("success"):
            payment = result.get("result", {}).get("payment_response", {})
            status = payment.get("status", "")
            tx_id = payment.get("transaction_id", "")[:8]
            print(f"✅ payment: {status} (tx: {tx_id}...)")
        else:
            print(f"❌ payment 失败")
            return False
        
        result = await adapter.call(conn, "decision", {
            "question": "选择颜色",
            "options": ["红色", "蓝色", "绿色"]
        })
        if result.get("success"):
            decision = result.get("result", {}).get("decision_response", {})
            selected = decision.get("selected", "")
            print(f"✅ decision: 选择了 {selected}")
        else:
            print(f"❌ decision 失败")
            return False
        
        await adapter.close(conn)
        print(f"✅ 关闭连接")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def test_agent_protocol():
    """测试 Agent Protocol 适配器"""
    print("\n" + "=" * 50)
    print("[AP] Agent Protocol")
    print("=" * 50)
    
    adapter = get_adapter("agent_protocol")
    config = {
        "id": "test_agent",
        "protocol": "agent_protocol",
        "endpoint": "http://localhost:8102"
    }
    
    try:
        conn = await adapter.connect(config)
        print(f"✅ 连接成功")
        
        result = await adapter.call(conn, "create_task", {"input": "Hello Agent Protocol!"})
        if result.get("success"):
            task_id = result.get("task_id", "")
            print(f"✅ create_task: {task_id[:8]}...")
        else:
            print(f"❌ create_task 失败")
            return False
        
        result = await adapter.call(conn, "execute_step", {
            "task_id": task_id,
            "input": "Process this"
        })
        if result.get("success"):
            step = result.get("result", {})
            output = step.get("output", "")
            print(f"✅ execute_step: {output}")
        else:
            print(f"❌ execute_step 失败")
            return False
        
        result = await adapter.call(conn, "get_task", {"task_id": task_id})
        if result.get("success"):
            task = result.get("result", {})
            status = task.get("status", "")
            print(f"✅ get_task: status={status}")
        else:
            print(f"❌ get_task 失败")
            return False
        
        result = await adapter.call(conn, "get_artifacts", {"task_id": task_id})
        if result.get("success"):
            artifacts = result.get("result", {}).get("artifacts", [])
            print(f"✅ get_artifacts: {len(artifacts)} 个产物")
        else:
            print(f"❌ get_artifacts 失败")
            return False
        
        await adapter.close(conn)
        print(f"✅ 关闭连接")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def test_lmos():
    """测试 LMOS 适配器"""
    print("\n" + "=" * 50)
    print("[LMOS] Language Model Operating System")
    print("=" * 50)
    
    adapter = get_adapter("lmos")
    config = {
        "id": "calculator",
        "protocol": "lmos",
        "endpoint": "http://localhost:8103/agents/calculator"
    }
    
    try:
        conn = await adapter.connect(config)
        print(f"✅ 连接成功")
        
        result = await adapter.call(conn, "invoke", {
            "capability": "add",
            "input": {"a": 10, "b": 20}
        })
        if result.get("success"):
            output = result.get("result", {}).get("output", {})
            calc_result = output.get("result", "")
            print(f"✅ invoke add(10, 20): {calc_result}")
        else:
            print(f"❌ invoke add 失败")
            return False
        
        result = await adapter.call(conn, "invoke", {
            "capability": "multiply",
            "input": {"a": 6, "b": 7}
        })
        if result.get("success"):
            output = result.get("result", {}).get("output", {})
            calc_result = output.get("result", "")
            print(f"✅ invoke multiply(6, 7): {calc_result}")
        else:
            print(f"❌ invoke multiply 失败")
            return False
        
        greeter_config = {
            "id": "greeter",
            "protocol": "lmos",
            "endpoint": "http://localhost:8103/agents/greeter"
        }
        conn2 = await adapter.connect(greeter_config)
        result = await adapter.call(conn2, "invoke", {
            "capability": "greet",
            "input": {"name": "test_user"}
        })
        if result.get("success"):
            output = result.get("result", {}).get("output", {})
            greeting = output.get("greeting", "")
            print(f"✅ invoke greet: {greeting}")
        else:
            print(f"❌ invoke greet 失败")
            return False
        
        await adapter.close(conn)
        await adapter.close(conn2)
        print(f"✅ 关闭连接")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


async def main():
    print("=" * 60)
    print("  UniAgent 完整交互测试")
    print("=" * 60)
    
    print("\n[1] 启动测试服务器...")
    SERVERS["A2A"] = start_server("A2A Server", "a2a_server.py", 8100)
    SERVERS["AITP"] = start_server("AITP Server", "aitp_server.py", 8101)
    SERVERS["AP"] = start_server("Agent Protocol Server", "agent_protocol_server.py", 8102)
    SERVERS["LMOS"] = start_server("LMOS Server", "lmos_server.py", 8103)
    
    time.sleep(1)
    
    print("\n[2] 开始测试...")
    
    results = {}
    
    try:
        results["ANP"] = await test_anp()
        results["A2A"] = await test_a2a()
        results["AITP"] = await test_aitp()
        results["Agent Protocol"] = await test_agent_protocol()
        results["LMOS"] = await test_lmos()
    finally:
        print("\n[3] 停止测试服务器...")
        stop_servers()
        print("  ✅ 所有服务器已停止")
    
    print("\n" + "=" * 60)
    print("  测试汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 所有协议测试通过！")
    else:
        print("⚠️  部分测试失败")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        stop_servers()
        print("\n测试中断")
