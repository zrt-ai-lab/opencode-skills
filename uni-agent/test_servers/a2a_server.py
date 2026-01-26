#!/usr/bin/env python3
"""
A2A 测试服务器 - 简单的 Echo Agent
HTTP 服务，提供 Agent Card 和 JSON-RPC 端点
"""

import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

PORT = 8100


class A2AHandler(BaseHTTPRequestHandler):
    
    tasks = {}
    
    def log_message(self, format, *args):
        pass
    
    def send_json(self, data: dict, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == "/.well-known/agent.json":
            self.send_json({
                "name": "Test A2A Agent",
                "description": "A simple echo agent for testing",
                "url": f"http://localhost:{PORT}/rpc",
                "version": "1.0.0",
                "capabilities": {
                    "streaming": False,
                    "pushNotifications": False
                },
                "skills": [
                    {
                        "id": "echo",
                        "name": "Echo",
                        "description": "Echo back the message",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "message": {"type": "string"}
                            }
                        }
                    },
                    {
                        "id": "greet",
                        "name": "Greet",
                        "description": "Greet the user",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"}
                            }
                        }
                    }
                ],
                "authentication": {
                    "schemes": ["none"]
                }
            })
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            request = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        
        if path == "/rpc":
            self.handle_rpc(request)
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def handle_rpc(self, request: dict):
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id", str(uuid.uuid4()))
        
        if method == "tasks/send":
            task_id = params.get("id", str(uuid.uuid4()))
            message = params.get("message", {})
            content = message.get("parts", [{}])[0].get("text", "") if "parts" in message else message.get("content", "")
            
            response_text = f"Echo: {content}"
            
            A2AHandler.tasks[task_id] = {
                "id": task_id,
                "status": {"state": "completed"},
                "history": [
                    message,
                    {"role": "agent", "parts": [{"type": "text", "text": response_text}]}
                ]
            }
            
            self.send_json({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": A2AHandler.tasks[task_id]
            })
        
        elif method == "tasks/get":
            task_id = params.get("id", "")
            if task_id in A2AHandler.tasks:
                self.send_json({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": A2AHandler.tasks[task_id]
                })
            else:
                self.send_json({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": "Task not found"}
                })
        
        elif method == "tasks/cancel":
            task_id = params.get("id", "")
            if task_id in A2AHandler.tasks:
                A2AHandler.tasks[task_id]["status"]["state"] = "canceled"
                self.send_json({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"success": True}
                })
            else:
                self.send_json({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": "Task not found"}
                })
        
        else:
            self.send_json({
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"}
            })


def main():
    server = HTTPServer(("localhost", PORT), A2AHandler)
    print(f"A2A Test Server running on http://localhost:{PORT}")
    print(f"Agent Card: http://localhost:{PORT}/.well-known/agent.json")
    server.serve_forever()


if __name__ == "__main__":
    main()
