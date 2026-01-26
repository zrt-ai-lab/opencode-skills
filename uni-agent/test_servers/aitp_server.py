#!/usr/bin/env python3
"""
AITP 测试服务器 - 模拟交互与交易
HTTP 服务，支持 Thread 会话
"""

import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime

PORT = 8101


class AITPHandler(BaseHTTPRequestHandler):
    
    threads = {}
    
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
        
        if path == "/":
            self.send_json({
                "name": "Test AITP Agent",
                "description": "A simple AITP agent for testing",
                "version": "1.0.0",
                "capabilities": ["aitp-01", "aitp-02", "aitp-03"]
            })
        
        elif path.startswith("/threads/"):
            parts = path.split("/")
            if len(parts) >= 3:
                thread_id = parts[2]
                if thread_id in AITPHandler.threads:
                    self.send_json(AITPHandler.threads[thread_id])
                else:
                    self.send_json({"error": "Thread not found"}, 404)
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
        
        if path == "/threads":
            thread_id = str(uuid.uuid4())
            AITPHandler.threads[thread_id] = {
                "id": thread_id,
                "status": "open",
                "messages": [],
                "created_at": datetime.now().isoformat()
            }
            self.send_json({"thread_id": thread_id})
        
        elif path.startswith("/threads/") and path.endswith("/messages"):
            parts = path.split("/")
            thread_id = parts[2]
            
            if thread_id not in AITPHandler.threads:
                AITPHandler.threads[thread_id] = {
                    "id": thread_id,
                    "status": "open",
                    "messages": [],
                    "created_at": datetime.now().isoformat()
                }
            
            thread = AITPHandler.threads[thread_id]
            
            if "capability" in request:
                capability = request.get("capability")
                
                if capability == "aitp-01":
                    payment_req = request.get("payment_request", {})
                    response = {
                        "role": "agent",
                        "capability": "aitp-01",
                        "payment_response": {
                            "status": "approved",
                            "transaction_id": str(uuid.uuid4()),
                            "amount": payment_req.get("amount"),
                            "currency": payment_req.get("currency", "NEAR"),
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                
                elif capability == "aitp-02":
                    decision_req = request.get("decision_request", {})
                    response = {
                        "role": "agent",
                        "capability": "aitp-02",
                        "decision_response": {
                            "question": decision_req.get("question"),
                            "selected": decision_req.get("options", ["Yes"])[0] if decision_req.get("options") else "Yes"
                        }
                    }
                
                elif capability == "aitp-03":
                    data_req = request.get("data_request", {})
                    response = {
                        "role": "agent",
                        "capability": "aitp-03",
                        "data_response": {
                            "schema": data_req.get("schema", {}),
                            "data": {"sample": "test_data", "timestamp": datetime.now().isoformat()}
                        }
                    }
                
                else:
                    response = {
                        "role": "agent",
                        "error": f"Unknown capability: {capability}"
                    }
            
            else:
                message = request.get("message", {})
                content = message.get("content", "")
                
                response = {
                    "role": "agent",
                    "content": f"AITP Echo: {content}",
                    "timestamp": datetime.now().isoformat()
                }
            
            thread["messages"].append(request)
            thread["messages"].append(response)
            
            self.send_json(response)
        
        else:
            self.send_json({"error": "Not found"}, 404)


def main():
    server = HTTPServer(("localhost", PORT), AITPHandler)
    print(f"AITP Test Server running on http://localhost:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
