#!/usr/bin/env python3
"""
LMOS 测试服务器 - 模拟企业级 Agent 平台
包含注册中心和 Agent 能力调用
"""

import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

PORT = 8103


MOCK_AGENTS = [
    {
        "id": "calculator",
        "name": "Calculator Agent",
        "description": "Performs calculations",
        "endpoint": f"http://localhost:{PORT}/agents/calculator",
        "capabilities": [
            {"id": "add", "description": "Add two numbers"},
            {"id": "multiply", "description": "Multiply two numbers"}
        ]
    },
    {
        "id": "greeter",
        "name": "Greeter Agent",
        "description": "Greets users",
        "endpoint": f"http://localhost:{PORT}/agents/greeter",
        "capabilities": [
            {"id": "greet", "description": "Greet a user by name"}
        ]
    }
]


class LMOSHandler(BaseHTTPRequestHandler):
    
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
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        if path == "/":
            self.send_json({
                "name": "Test LMOS Registry",
                "version": "1.0.0",
                "agents": len(MOCK_AGENTS)
            })
        
        elif path == "/agents":
            capability = query.get("capability", [None])[0]
            
            if capability:
                filtered = [
                    a for a in MOCK_AGENTS 
                    if any(c["id"] == capability for c in a["capabilities"])
                ]
                self.send_json({"agents": filtered})
            else:
                self.send_json({"agents": MOCK_AGENTS})
        
        elif path.startswith("/agents/") and path.endswith("/capabilities"):
            agent_id = path.split("/")[2]
            agent = next((a for a in MOCK_AGENTS if a["id"] == agent_id), None)
            
            if agent:
                self.send_json({"capabilities": agent["capabilities"]})
            else:
                self.send_json({"error": "Agent not found"}, 404)
        
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            request = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        
        if path.startswith("/agents/") and path.endswith("/invoke"):
            agent_id = path.split("/")[2]
            agent = next((a for a in MOCK_AGENTS if a["id"] == agent_id), None)
            
            if not agent:
                self.send_json({"error": "Agent not found"}, 404)
                return
            
            capability = request.get("capability", "")
            input_data = request.get("input", {})
            
            if agent_id == "calculator":
                if capability == "add":
                    a = input_data.get("a", 0)
                    b = input_data.get("b", 0)
                    result = {"result": a + b}
                elif capability == "multiply":
                    a = input_data.get("a", 0)
                    b = input_data.get("b", 0)
                    result = {"result": a * b}
                else:
                    result = {"error": f"Unknown capability: {capability}"}
            
            elif agent_id == "greeter":
                if capability == "greet":
                    name = input_data.get("name", "World")
                    result = {"greeting": f"Hello, {name}!"}
                else:
                    result = {"error": f"Unknown capability: {capability}"}
            
            else:
                result = {"error": "Unknown agent"}
            
            self.send_json({
                "agent_id": agent_id,
                "capability": capability,
                "output": result,
                "timestamp": datetime.now().isoformat()
            })
        
        elif path == "/route":
            query_text = request.get("query", "")
            
            if "add" in query_text.lower() or "calculate" in query_text.lower():
                best_agent = MOCK_AGENTS[0]
            elif "greet" in query_text.lower() or "hello" in query_text.lower():
                best_agent = MOCK_AGENTS[1]
            else:
                best_agent = MOCK_AGENTS[0]
            
            self.send_json({
                "recommended_agent": best_agent,
                "confidence": 0.85,
                "alternatives": [a for a in MOCK_AGENTS if a["id"] != best_agent["id"]]
            })
        
        else:
            self.send_json({"error": "Not found"}, 404)


def main():
    server = HTTPServer(("localhost", PORT), LMOSHandler)
    print(f"LMOS Test Server running on http://localhost:{PORT}")
    print(f"Registry: http://localhost:{PORT}/agents")
    server.serve_forever()


if __name__ == "__main__":
    main()
