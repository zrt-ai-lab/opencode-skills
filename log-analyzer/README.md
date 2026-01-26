# Log Analyzer

智能日志分析器，支持多种日志类型。

## 依赖

无需额外安装，纯 Python 标准库实现。

## 功能

- 自动识别日志类型（Java App / MySQL Binlog / Nginx / Trace / Alert）
- 提取 20+ 种实体（IP、thread_id、user_id、表名等）
- 敏感操作检测、异常洞察
- 支持 100M+ 大文件流式处理

## 使用

```bash
python scripts/preprocess.py <日志文件> -o ./log_analysis
```
