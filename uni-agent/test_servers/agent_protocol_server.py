#!/usr/bin/env python3
"""
Agent Protocol 测试服务器
REST API 标准实现
"""

import json
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime

PORT = 8102


class APHandler(BaseHTTPRequestHandler):
    
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
        
        if path == "/" or path == "/ap/v1":
            self.send_json({
                "name": "Test Agent Protocol Server",
                "version": "1.0.0",
                "protocol_version": "v1"
            })
        
        elif path == "/ap/v1/agent/tasks":
            self.send_json({
                "tasks": list(APHandler.tasks.values())
            })
        
        elif path.startswith("/ap/v1/agent/tasks/"):
            parts = path.split("/")
            task_id = parts[5] if len(parts) > 5 else ""
            
            if "/artifacts" in path:
                if task_id in APHandler.tasks:
                    self.send_json({
                        "artifacts": APHandler.tasks[task_id].get("artifacts", [])
                    })
                else:
                    self.send_json({"error": "Task not found"}, 404)
            
            elif "/steps" in path:
                if task_id in APHandler.tasks:
                    self.send_json({
                        "steps": APHandler.tasks[task_id].get("steps", [])
                    })
                else:
                    self.send_json({"error": "Task not found"}, 404)
            
            else:
                if task_id in APHandler.tasks:
                    self.send_json(APHandler.tasks[task_id])
                else:
                    self.send_json({"error": "Task not found"}, 404)
        
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        
        try:
            request = json.loads(body) if body else {}
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        
        if path == "/ap/v1/agent/tasks":
            task_id = str(uuid.uuid4())
            task_input = request.get("input", "")
            
            APHandler.tasks[task_id] = {
                "task_id": task_id,
                "input": task_input,
                "status": "running",
                "steps": [],
                "artifacts": [],
                "created_at": datetime.now().isoformat()
            }
            
            self.send_json(APHandler.tasks[task_id], 201)
        
        elif path.startswith("/ap/v1/agent/tasks/") and path.endswith("/steps"):
            parts = path.split("/")
            task_id = parts[5]
            
            if task_id not in APHandler.tasks:
                self.send_json({"error": "Task not found"}, 404)
                return
            
            step_input = request.get("input", "")
            step_id = str(uuid.uuid4())
            
            step = {
                "step_id": step_id,
                "input": step_input,
                "output": f"Processed: {step_input}" if step_input else "Step executed",
                "status": "completed",
                "is_last": True,
                "created_at": datetime.now().isoformat()
            }
            
            APHandler.tasks[task_id]["steps"].append(step)
            APHandler.tasks[task_id]["status"] = "completed"
            
            APHandler.tasks[task_id]["artifacts"].append({
                "artifact_id": str(uuid.uuid4()),
                "file_name": "output.txt",
                "relative_path": "/output.txt",
                "content": step["output"]
            })
            
            self.send_json(step, 201)
        
        else:
            self.send_json({"error": "Not found"}, 404)


def main():
    server = HTTPServer(("localhost", PORT), APHandler)
    print(f"Agent Protocol Test Server running on http://localhost:{PORT}")
    print(f"API Base: http://localhost:{PORT}/ap/v1")
    server.serve_forever()


if __name__ == "__main__":
    main()
