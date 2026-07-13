# skill-scanner

无第三方依赖的 Skill 安全预检工具。它只读扫描，不执行目标 Skill，也不回显敏感匹配内容。

## 快速开始

```bash
python3 scripts/scan_skill.py ../some-skill
python3 scripts/scan_skill.py ../some-skill --json
```

示例输出只保留风险类型和位置：

```text
# Skill Scan: CAUTION

## Findings

- `medium` `outbound-download` at `scripts/fetch.py:12`
```

## 检测范围

| 类别 | 示例 |
|---|---|
| `credential` | Token、密码、API Key 赋值 |
| `private-key` | 私钥头 |
| `absolute-path` | 固定本机路径 |
| `dangerous-command` | 递归删除、提权、持久化、反向 Shell、下载执行 |
| `outbound-download` | HTTP、Socket、包管理器或远程下载 |
| `obfuscation` | `eval`、`exec`、编码解码后执行 |
| `sensitive-directory` | SSH、云凭证、系统密码、Keychain 等目录 |

## 接入仓库检查

```bash
python3 scripts/scan_skill.py ./new-skill --json > /tmp/skill-scan.json
status=$?
case "$status" in
  0) echo "approved" ;;
  1) echo "review required" ;;
  2) echo "reject" ;;
esac
exit "$status"
```

不要把扫描报告中的绝对路径、环境变量值或原始代码片段提交到仓库。

## 测试

```bash
python3 -m unittest discover -s tests -v
```
