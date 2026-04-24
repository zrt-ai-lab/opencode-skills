# Server Manager

后台启动、追踪、关闭开发服务器，不阻塞 AI 对话。

## 解决的问题

在 AI 终端里运行 `npm run dev` 会一直占用终端，无法继续对话。本 skill 实现**完全不阻塞**的后台服务器管理。

## 安装

Skill 已包含所有脚本，直接使用：

```powershell
# 启动服务器
start-server -Name "myapp" -Command "npm run dev" -Port 3000

# 列出所有服务器
list-servers

# 健康检查
health-server -Name "myapp"

# 停止
stop-server -Name "myapp"
```

## 支持的技术栈

Node.js (Next.js / Vite / HyperFrames / Remotion / Motion Canvas)、Python (Streamlit / Flask / Django)、Go、Ruby、Rust 等任何开发服务器。

## 命令

| 命令 | 用途 |
|------|------|
| `start-server` | 启动服务器（不阻塞） |
| `stop-server` | 停止单个服务器 |
| `stop-all` | 停止所有服务器 |
| `list-servers` | 列出活跃服务器 |
| `health-server` | HTTP 健康检查 |
| `tail-server` | 查看日志末尾 |
| `grep-server` | 搜索日志关键词 |
