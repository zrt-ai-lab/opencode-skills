---
name: skill-scanner
description: Use when reviewing an agent Skill before sharing, installing, or executing it and when checking a Skill bundle for credentials, dangerous commands, suspicious network behavior, or obfuscated code.
---

# Skill Scanner

扫描 Skill 目录中的脚本、文档和配置，报告凭证、私钥、危险命令、敏感目录访问、外联下载和代码混淆等风险。

## 触发场景

- 引入外部 Skill 前。
- 将新 Skill 推送到公共仓库前。
- 升级 Skill 依赖或脚本后做回归检查。
- 审查用户上传的 Skill 压缩包或本地目录。

## 安全边界

- 只读取目标目录，不执行被扫描的脚本，不联网，不安装依赖。
- 报告只包含风险类型、严重级别、相对文件路径和行号；禁止输出匹配代码、Token、密码或私钥内容。
- `reject` 表示发现关键风险；`caution` 表示发现需要人工复核的风险；`approved` 只表示未命中当前规则，不能替代人工审查。
- 将扫描结果作为合并前检查，不把它当作安全证明。

## 使用方式

在 Skill 根目录执行：

```bash
python3 scripts/scan_skill.py path/to/skill
python3 scripts/scan_skill.py path/to/skill --json
python3 scripts/scan_skill.py path/to/skill --output report.md
```

退出码：`0` 表示未发现问题，`1` 表示需要复核，`2` 表示关键风险。

## 标准流程

1. 读取目标 Skill 的文件清单，确认扫描范围。
2. 执行 Markdown 报告和 JSON 报告两种模式。
3. 优先处理 `critical`、`high`，再判断 `medium` 是否为明确业务需要。
4. 核对报告中的相对路径和行号；不要要求工具回显敏感内容。
5. 清理或隔离问题后重新扫描，并保存不含敏感值的报告。

## 规则覆盖

- 凭证赋值、云密钥、Token、密码和私钥头。
- `/Users`、`/home`、敏感配置目录和宿主凭证目录。
- 递归删除、提权、系统持久化、反向 Shell 和下载后执行。
- `eval`、`exec`、动态导入、Base64/Hex/Marshal 解码等混淆信号。
- HTTP 请求、包管理器下载和 Socket 等外联信号。

## 局限

规则扫描可能产生误报，也可能漏掉语义级攻击。对高风险 Skill 继续做人工代码审查、最小权限运行和隔离环境验证。
