---
name: server-manager
description: 服务器进程管理技能。当用户需要启动开发服务器（npm run dev / streamlit run / python manage.py runserver 等）且不希望阻塞终端对话时触发，自动后台运行、追踪端口、记录日志。需要与 start-server / stop-server / list-servers / health-server / tail-server / grep-server 命令配合使用。适用于 Node.js (Vite/Next.js/HyperFrames/Remotion)、Python (Streamlit/Flask)、Go 等任意技术栈的开发服务器。
---

# Server Manager

后台启动、追踪、关闭开发服务器，不阻塞 AI 对话。支持任意技术栈的服务器进程（Node.js、Python、Go、Rust 等）。

## 核心问题

AI 在终端里运行 `npm run dev` 时，命令会一直占用终端，导致无法继续对话。`Start-Process` 可以后台运行，但 AI 不知道它开了什么、端口是多少、什么时候能访问。

## 设计原理

```
Start-Process cmd /c "$Command > $LogFile 2>&1"
```

启动命令通过 `cmd /c` 重定向到日志文件，实现**不阻塞**。同时记录端口和 PID 到 `.servers.json`，后续命令通过这个文件追踪所有服务器。

## 启动服务器（核心命令）

```powershell
# 基础用法（自动检测端口）
start-server -Name "myapp" -Command "npm run dev"

# 指定端口
start-server -Name "nextjs" -Command "npm run dev" -Port 3000

# 指定工作目录
start-server -Name "streamlit" -Command "streamlit run app.py" -Cwd "C:\project" -Port 8501
```

**参数说明：**

| 参数 | 必填 | 说明 |
|------|------|------|
| `-Name` | ✅ | 服务器名称，唯一标识 |
| `-Command` | ✅ | 完整启动命令 |
| `-Port` | ❌ | 期望端口。不指定时自动检测 |
| `-Cwd` | ❌ | 工作目录 |

**成功输出：**
```
Started: nextjs port: 3000
Log: C:\project\.server-logs\nextjs.log
```

**端口冲突处理：** 如果指定端口被占用，自动切换到下一个可用端口，不报错。

---

## 查询服务器列表

```powershell
# 列出所有通过 skill 启动的服务器
list-servers

# 示例输出：
# nextjs     | port: 3000 | 5m | running | log: C:\..\nextjs.log
# streamlit | port: 8501 | 15s | running
```

**功能：**
- 显示所有活跃服务器及运行时间
- 自动清理已崩溃/关闭的僵尸进程记录
- 实时端口监听状态检测

---

## 健康检查

```powershell
# 检查服务器是否响应 HTTP 请求
health-server -Name "nextjs"

# 检查特定路径
health-server -Name "nextjs" -Path "/api/health"

# 自定义超时（秒）
health-server -Name "nextjs" -TimeoutSec 10
```

**输出示例：**
```
OK  200  141ms  http://localhost:3000/
DOWN  connection refused  http://localhost:3000/
```

**与端口检测的区别：** 端口在监听 ≠ 服务器正常响应。HTTP 健康检查能发现服务器卡死、接口报错等更真实的问题。

---

## 停止服务器

```powershell
# 停止单个服务器
stop-server -Name "nextjs"

# 停止所有服务器
stop-all
```

**停止原理：** 通过端口查当前监听进程 → `Stop-Process -Force` 强制终止。

---

## 查看日志

```powershell
# 查看服务器日志末尾（默认20行）
tail-server -Name "nextjs"

# 查看更多行
tail-server -Name "nextjs" -Lines 50
```

---

## 日志搜索

```powershell
# 搜索包含关键词的行
grep-server -Name "nextjs" -Pattern "error"

# 按日志级别过滤（error/warn/info/debug）
grep-server -Name "nextjs" -Level error

# 组合：error级别中包含"port"的行，读最近200行
grep-server -Name "nextjs" -Level error -Pattern "port" -Lines 200
```

**注意：** 日志文件在服务器启动时清空，每次重启后重新记录。`grep` 搜到的是"最后一次启动以来"的日志，不会翻到旧错误。

---

## 支持的技术栈

| 技术栈 | 启动命令 | 默认端口 |
|--------|----------|----------|
| Next.js | `npm run dev` | 3000 |
| Vite | `npm run dev` | 自动检测 |
| HyperFrames | `npx hyperframes preview` | 3456 |
| Remotion | `npm run dev` | 3000 |
| Motion Canvas | `npm run template:dev` | 自动检测 |
| Streamlit | `streamlit run app.py` | 8501 |
| Flask | `flask run` | 5000 |
| Django | `python manage.py runserver` | 8000 |
| FastAPI | `uvicorn main:app` | 8000 |
| Go HTTP | `go run .` | 自动检测 |

**通用原则：** 任何启动后监听端口的开发服务器都支持。

---

## 文件结构

```
server-manager/
├── SKILL.md              # 本文件
├── README.md              # 使用文档
└── scripts/
    ├── start-server.ps1   # 启动服务器
    ├── stop-server.ps1    # 停止单个服务器
    ├── stop-all.ps1       # 停止所有服务器
    ├── list-servers.ps1   # 列出服务器
    ├── health-server.ps1  # HTTP 健康检查
    ├── tail-server.ps1   # 查看日志末尾
    └── grep-server.ps1    # 日志搜索
```

## 状态文件

`.servers.json` 在 `start-server` 执行目录生成，记录所有活跃服务器：

```json
{
  "servers": [
    {
      "name": "nextjs",
      "port": 3000,
      "pid": 12345,
      "startedAt": "2026-04-24T10:00:00",
      "logFile": "C:\\project\\.server-logs\\nextjs.log",
      "command": "npm run dev"
    }
  ]
}
```

## 注意事项

1. **端口检测范围：** 自动检测仅覆盖 3000-9999，超出范围需手动指定 `-Port`
2. **日志文件位置：** 默认在执行命令的目录下创建 `.server-logs/` 目录
3. **停止机制：** 通过端口查到进程直接杀，不区分来源，可能误伤同名进程
4. **Python 版本：** PowerShell 7+ 推荐，Windows PowerShell 5.1 兼容
