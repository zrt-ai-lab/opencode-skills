# OpenCode Skills

OpenCode 技能集合，扩展 AI Agent 的专业能力。

## 技能列表

### 🎬 内容创作

| Skill | 用途 | 说明 |
|-------|------|------|
| [video-creator](./video-creator/) | 视频生成 | 图片+音频合成视频，支持TTS配音、转场、字幕、片尾、BGM。内置 verify_alignment.py 强制校验音画同步 |
| [image-service](./image-service/) | 图像生成/编辑/分析 | 文生图、图生图、图转文、长图拼接，支持10种比例 |
| [story-to-scenes](./story-to-scenes/) | 故事拆镜生图 | 故事/剧本 → 分镜 → 风格一致的系列图片 |
| [searchnews](./searchnews/) | AI 新闻搜索整理 | Ralph Loop 地毯式搜索 + 日报生成 + 视频制作全流程 |

### 📱 自动发布

| Skill | 用途 | 说明 |
|-------|------|------|
| [auto-douyin](./auto-douyin/) | 抖音自动发布 | Playwright 自动化，支持定时发布、话题标签、封面设置 |
| [auto-redbook](./auto-redbook/) | 小红书笔记创作 | Markdown → 精美图片卡片渲染（8套主题），支持自动发布 |
| [auto-weixin-video](./auto-weixin-video/) | 视频号自动发布 | Playwright 自动化，支持原创声明、定时发布、合集 |

### 🎥 视频剪辑

| Skill | 用途 | 说明 |
|-------|------|------|
| [videocut-clip](./videocut-clip/) | 视频片段裁剪 | 按时间戳精确裁剪视频片段 |
| [videocut-clip-oral](./videocut-clip-oral/) | 口播视频剪辑 | 自动识别口播内容并裁剪 |
| [videocut-subtitle](./videocut-subtitle/) | 视频字幕 | 自动生成/烧录字幕 |
| [videocut-install](./videocut-install/) | videocut 安装 | videocut 工具链安装指南 |
| [videocut-self-update](./videocut-self-update/) | videocut 更新 | videocut 自动更新 |

### 🔧 开发工具

| Skill | 用途 | 说明 |
|-------|------|------|
| [smart-query](./smart-query/) | 数据库智能查询 | 自然语言 → SQL，支持多种数据库 |
| [csv-data-summarizer](./csv-data-summarizer/) | CSV 数据分析 | CSV 数据统计、可视化、报告生成 |
| [log-analyzer](./log-analyzer/) | 日志智能分析 | 日志模式识别、异常检测、根因分析 |
| [mcp-builder](./mcp-builder/) | MCP Server 创建 | 快速构建 Model Context Protocol 服务 |
| [skill-creator](./skill-creator/) | Skill 创建指南 | 标准化 Skill 开发模板和工具 |

### 🤖 Agent 调度

| Skill | 用途 | 说明 |
|-------|------|------|
| [uni-agent](./uni-agent/) | 统一 Agent 调度 | 多 Agent 协作任务编排 |
| [deep-research](./deep-research/) | 深度调研 | 多轮搜索 + 信息整合 + 报告生成 |

## 安装使用

将需要的 skill 目录复制到 `~/.opencode/skills/` 下即可：

```bash
# 复制单个 skill
cp -r video-creator ~/.opencode/skills/

# 复制全部
cp -r */ ~/.opencode/skills/
```

## 注意事项

- **敏感数据**：auto-douyin / auto-redbook / auto-weixin-video 需要各自配置 Cookie，首次使用需扫码登录
- **Python 环境**：video-creator 和 image-service 需要 Python 3.10+ 及相关依赖
- **ffmpeg**：视频相关 skill 需要安装 ffmpeg（`brew install ffmpeg`）
- **Playwright**：自动发布 skill 需要安装 Playwright（`pip install playwright && playwright install chromium`）

## License

MIT
