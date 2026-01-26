---
name: log-analyzer
description: 全维度日志分析技能。自动识别日志类型（Java应用/MySQL Binlog/Nginx/Trace/告警），提取关键实体（IP、thread_id、trace_id、用户、表名等），进行根因定位、告警分析、异常洞察。支持100M+大文件。触发词：分析日志、日志排查、根因定位、告警分析、异常分析。
---

# 日志分析器

基于 RAPHL（Recursive Analysis Pattern for Hierarchical Logs）的全维度智能日志分析技能。流式处理，内存占用低，100M+ 日志秒级分析。

## 核心能力

| 能力 | 说明 |
|------|------|
| 自动识别 | 自动识别日志类型：Java App / MySQL Binlog / Nginx / Trace / Alert |
| 实体提取 | IP、thread_id、trace_id、user_id、session_id、bucket、URL、表名等 20+ 种 |
| 操作分析 | DELETE/UPDATE/INSERT/DROP 等敏感操作检测 |
| 关联分析 | 时间线、因果链、操作链构建 |
| 智能洞察 | 自动生成分析结论、证据、建议 |

## 支持的日志类型

| 类型 | 识别特征 | 提取内容 |
|------|----------|----------|
| **Java App** | ERROR/WARN + 堆栈 | 异常类型、堆栈、logger、时间 |
| **MySQL Binlog** | server id、GTID、Table_map | 表操作、thread_id、server_id、数据变更 |
| **Nginx Access** | IP + HTTP 方法 + 状态码 | 请求IP、URL、状态码、耗时 |
| **Trace** | trace_id、span_id | 链路追踪、调用关系、耗时 |
| **Alert** | CRITICAL/告警 | 告警级别、来源、消息 |
| **General** | 通用 | 时间、IP、关键词 |

## 使用方法

```bash
python .opencode/skills/log-analyzer/scripts/preprocess.py <日志文件> -o ./log_analysis
```

## 输出文件

| 文件 | 内容 | 用途 |
|------|------|------|
| `summary.md` | 完整分析报告 | **优先阅读** |
| `entities.md` | 实体详情（IP、用户、表名等） | 追溯操作来源 |
| `operations.md` | 操作详情 | 查看具体操作 |
| `insights.md` | 智能洞察 | 问题定位和建议 |
| `analysis.json` | 结构化数据 | 程序处理 |

## 实体提取清单

### 网络/连接类
- IP 地址、IP:Port、URL、MAC 地址

### 追踪/会话类
- trace_id、span_id、request_id、session_id、thread_id

### 用户/权限类
- user_id、ak（access_key）、bucket

### 数据库类
- database.table、server_id

### 性能/状态类
- duration（耗时）、http_status、error_code

## 敏感操作检测

| 类型 | 检测模式 | 风险级别 |
|------|----------|----------|
| 数据删除 | DELETE, DROP, TRUNCATE | HIGH |
| 数据修改 | UPDATE, ALTER, MODIFY | MEDIUM |
| 权限变更 | GRANT, REVOKE, chmod | HIGH |
| 认证操作 | LOGIN, LOGOUT, AUTH | MEDIUM |

## 智能洞察类型

| 类型 | 说明 |
|------|------|
| security | 大批量删除/修改、权限变更 |
| anomaly | 高频 IP、异常时间段操作 |
| error | 严重异常、错误聚类 |
| audit | 操作来源、用户行为 |

## 分析流程

```
Phase 1: 日志类型识别（采样前100行）
    ↓
Phase 2: 全量扫描提取（流式处理）
    ↓
Phase 3: 关联分析（时间排序、聚合统计）
    ↓
Phase 4: 智能洞察（异常检测、生成结论）
    ↓
Phase 5: 生成报告（Markdown + JSON）
```

## 技术特点

| 特点 | 说明 |
|------|------|
| 流式处理 | 逐行读取，100M 文件只占几 MB 内存 |
| 正则预编译 | 20+ 种实体模式预编译，匹配快 |
| 一次遍历 | 提取 + 统计 + 分类一次完成 |
| 类型适配 | 不同日志类型用专用解析器 |

## 注意事项

1. **Binlog 不记录客户端 IP**：只有 server_id 和 thread_id，需结合 general_log 确认操作者
2. **敏感信息脱敏**：报告中注意不要暴露密码、密钥
3. **结合多源日志**：binlog + 应用日志 + 审计日志 才能完整还原
