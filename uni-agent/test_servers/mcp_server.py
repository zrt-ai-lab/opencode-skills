#!/usr/bin/env python3
"""
MCP 测试服务器 - 简单的 Echo + 计算器
通过 stdio 通信
"""

import json
import sys
from datetime import datetime


def send_response(id: str, result: dict):
    """发送 JSON-RPC 响应"""
    response = {
        "jsonrpc": "2.0",
        "id": id,
        "result": result
    }
    msg = json.dumps(response)
    sys.stdout.write(f"Content-Length: {len(msg)}\r\n\r\n{msg}")
    sys.stdout.flush()


def send_error(id: str, code: int, message: str):
    """发送错误响应"""
    response = {
        "jsonrpc": "2.0",
        "id": id,
        "error": {"code": code, "message": message}
    }
    msg = json.dumps(response)
    sys.stdout.write(f"Content-Length: {len(msg)}\r\n\r\n{msg}")
    sys.stdout.flush()


def handle_request(request: dict):
    """处理请求"""
    method = request.get("method", "")
    params = request.get("params", {})
    req_id = request.get("id", "0")
    
    if method == "initialize":
        send_response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": True}
            },
            "serverInfo": {
                "name": "test-mcp-server",
                "version": "1.0.0"
            }
        })
    
    elif method == "notifications/initialized":
        pass
    
    elif method == "tools/list":
        send_response(req_id, {
            "tools": [
                {
                    "name": "echo",
                    "description": "返回输入的消息",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {"type": "string", "description": "要返回的消息"}
                        },
                        "required": ["message"]
                    }
                },
                {
                    "name": "add",
                    "description": "两数相加",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "a": {"type": "number"},
                            "b": {"type": "number"}
                        },
                        "required": ["a", "b"]
                    }
                },
                {
                    "name": "get_time",
                    "description": "获取当前时间",
                    "inputSchema": {"type": "object", "properties": {}}
                }
            ]
        })
    
    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        
        if tool_name == "echo":
            msg = tool_args.get("message", "")
            send_response(req_id, {
                "content": [{"type": "text", "text": f"Echo: {msg}"}]
            })
        
        elif tool_name == "add":
            a = tool_args.get("a", 0)
            b = tool_args.get("b", 0)
            send_response(req_id, {
                "content": [{"type": "text", "text": str(a + b)}]
            })
        
        elif tool_name == "get_time":
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            send_response(req_id, {
                "content": [{"type": "text", "text": now}]
            })
        
        else:
            send_error(req_id, -32601, f"Unknown tool: {tool_name}")
    
    else:
        send_error(req_id, -32601, f"Unknown method: {method}")


def main():
    """主循环 - 读取 stdin，处理请求"""
    buffer = ""
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            buffer += line
            
            if "Content-Length:" in buffer:
                parts = buffer.split("\r\n\r\n", 1)
                if len(parts) == 2:
                    header, body = parts
                    length = int(header.split(":")[1].strip())
                    
                    while len(body) < length:
                        body += sys.stdin.read(length - len(body))
                    
                    request = json.loads(body[:length])
                    handle_request(request)
                    
                    buffer = body[length:]
            
            elif buffer.strip().startswith("{"):
                try:
                    request = json.loads(buffer.strip())
                    handle_request(request)
                    buffer = ""
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    main()
