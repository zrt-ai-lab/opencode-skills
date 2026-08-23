---
name: videocut-subtitle
description: 字幕生成与烧录。转录→词典纠错→审核→烧录。触发词：加字幕、生成字幕、字幕
metadata:
  version: "1.1.0"
  alias: "videocut:字幕"
---

# 字幕

> 转录 → 纠错 → 审核 → 匹配 → 烧录

## 流程

```
1. 转录视频（Whisper）
    ↓
2. 词典纠错 + 分句
    ↓
3. 输出字幕稿（纯文本，一句一行）
    ↓
【用户审核修改】
    ↓
4. 用户给回修改后的文本
    ↓
5. 我匹配时间戳 → 生成 SRT
    ↓
6. 烧录字幕（FFmpeg）
```

## 转录

使用 OpenAI Whisper 模型进行语音转文字：

```bash
whisper video.mp4 --model medium --language zh --output_format json
```

| 模型 | 用途 |
|------|------|
| `medium` | 默认，平衡速度与准确率 |
| `large-v3` | 高精度，较慢 |

输出 JSON 包含逐词时间戳，用于后续 SRT 生成。

### 可选：Atlas Cloud 转录

默认继续使用本地 Whisper，中文转录也必须保持该流程。只有用户明确选择 Atlas Cloud，且音频语言在 `xai/stt-v1` 当前支持列表内时，才使用仓库内置的 `scripts/atlas_transcribe.py`。输出保留 `words[].start` 和 `words[].end`，可继续用于后续文本审核和 SRT 时间戳匹配。

先预览请求，不访问网络，也不会产生费用：

```bash
python3 videocut-subtitle/scripts/atlas_transcribe.py \
  --input video.mp4 \
  --language en \
  --keyterm Claude \
  --output transcript.json
```

用户确认参数后显式执行：

```bash
python3 videocut-subtitle/scripts/atlas_transcribe.py \
  --input video.mp4 \
  --language en \
  --keyterm Claude \
  --output transcript.json \
  --execute
```

- 从环境变量 `ATLASCLOUD_API_KEY` 读取认证信息
- `--language` 仅接受模型 schema 当前列出的语言代码；不支持中文，中文必须继续使用 Whisper
- 本地文件最大 25 MiB；更大的媒体文件使用公开 HTTPS 地址配合 `--audio-url`
- 可重复传入 `--keyterm`，将 `词典.txt` 中的专有词作为识别提示
- 付费生成 POST 只提交一次，失败时不自动重试；仅结果 GET 使用有界退避
- 默认不会覆盖已有输出，且输出路径必须位于当前工作目录内

---

## 字幕规范

| 规则 | 说明 |
|------|------|
| 一屏一行 | 不换行，不堆叠 |
| ≤15字/行 | 超过15字必须拆分（4:3竖屏） |
| 句尾无标点 | `你好` 不是 `你好。` |
| 句中保留标点 | `先点这里，再点那里` |

---

## 词典纠错

读取 `词典.txt`，每行一个正确写法：

```
skills
Claude
iPhone
```

我自动识别变体：`claude` → `Claude`

---

## 字幕稿格式

**我给用户的**（纯文本，≤15字/行）：

```
今天给大家分享一个技巧
很多人可能不知道
其实这个功能
藏在设置里面
你只要点击这里
就能看到了
```

**用户修改后给回我**，我再匹配时间戳生成 SRT。

---

## 样式

默认：24号白字、黑色描边、底部居中

**可选样式：**
| 样式 | 说明 |
|------|------|
| 默认 | 白字黑边 |
| 黄字 | 黄字黑边（醒目） |

用户可说：
- "字大一点" → 32号
- "放顶部" → 顶部居中
- "黄色字幕" → 黄字黑边

---

## 输出

```
01-xxx_字幕稿.txt   # 纯文本，用户编辑
01-xxx.srt          # 字幕文件
01-xxx-字幕.mp4     # 带字幕视频
```
