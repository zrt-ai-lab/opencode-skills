# OpenCode Skills

OpenCode / OpenClaw 技能集合，扩展 AI Agent 的专业能力。20 个 Skill，覆盖内容创作、自动发布、视频剪辑、开发工具、Agent 调度五大方向。

## 技能总览

### 🎬 内容创作

| Skill | 用途 | 说明 | 配置 |
|-------|------|------|------|
| [image-service](./image-service/) | 图像生成/编辑/分析 | 8大场景路由（信息图/封面/长图/幻灯片/漫画/文章插图/小红书/营销），4500+种组合。核心引擎：文生图、图生图、图生文、长图拼接 | ⚙️ 图像API + 视觉API |
| [video-creator](./video-creator/) | 视频生成 | 图片+音频→视频全流程。支持TTS配音、淡入淡出转场、字幕烧录、片尾拼接、BGM混音。内含生图→配音→合成完整链路 | ⚙️ TTS API |
| [story-to-scenes](./story-to-scenes/) | 故事拆镜生图 | 长文本智能拆分场景，批量生成风格统一、角色一致的配图。支持故事/课程/连环画/绘本 | 无 |
| [auto-redbook](./auto-redbook/) | 小红书笔记创作 | Markdown→精美图片卡片渲染（8套主题），自动排版封面+正文卡片，支持一键发布 | 🔑 小红书Cookie |
| [searchnews](./searchnews/) | AI新闻搜索整理 | Ralph Loop地毯式搜索，10大分类100+标签筛选，日报生成+视频制作全流程 | 无 |
| [deep-research](./deep-research/) | 深度调研 | 多轮搜索+信息整合+结构化报告生成，适合技术选型和行业分析 | 无 |

### 📱 自动发布

| Skill | 用途 | 说明 | 配置 |
|-------|------|------|------|
| [auto-douyin](./auto-douyin/) | 抖音发布 | Playwright自动化上传视频，支持定时发布、话题标签、封面设置 | 🔑 首次扫码登录 |
| [auto-weixin-video](./auto-weixin-video/) | 视频号发布 | Playwright自动化上传视频，支持原创声明、定时发布、合集管理 | 🔑 首次微信扫码 |

### 🎥 视频剪辑（videocut 系列）

5个skill协同工作，覆盖口播视频从转录到成片的完整流程：

| Skill | 用途 | 说明 | 配置 |
|-------|------|------|------|
| [videocut-install](./videocut-install/) | 环境安装 | 安装依赖、下载Whisper模型、验证环境 | 无 |
| [videocut-clip-oral](./videocut-clip-oral/) | 口播转录+口误识别 | 语音转录→口误自动识别→生成审查稿和删除任务清单 | 无 |
| [videocut-clip](./videocut-clip/) | 视频裁剪 | 按确认的删除任务执行FFmpeg精确裁剪，循环直到零口误 | 无 |
| [videocut-subtitle](./videocut-subtitle/) | 字幕生成 | 转录→词典纠错→人工审核→字幕烧录 | 无 |
| [videocut-self-update](./videocut-self-update/) | 规则自更新 | 记录用户反馈，自动更新方法论和识别规则 | 无 |

### 🔧 开发工具

| Skill | 用途 | 说明 | 配置 |
|-------|------|------|------|
| [smart-query](./smart-query/) | 数据库智能查询 | 自然语言→SQL，支持SSH隧道连接线上数据库，表结构探索 | ⚙️ SSH + 数据库连接 |
| [csv-data-summarizer](./csv-data-summarizer/) | CSV数据分析 | pandas驱动的数据统计、可视化图表、分析报告生成 | 无 |
| [log-analyzer](./log-analyzer/) | 日志智能分析 | 自动识别日志类型（Java/MySQL/Nginx/Trace/告警），实体提取，根因定位。支持100M+大文件 | 无 |
| [mcp-builder](./mcp-builder/) | MCP Server开发 | 快速构建Model Context Protocol服务，支持Python(FastMCP)和Node/TypeScript | 无 |
| [skill-creator](./skill-creator/) | Skill开发指南 | 标准化Skill开发模板、目录规范、最佳实践 | 无 |
| [build-project-docs](./build-project-docs/) | 项目文档体系构建 | 分层式LLM友好文档生成。已有项目8阶段（探查→分类→索引→基础模块→业务模块→配置→变更日志→验证），新项目5阶段（PRD解析→架构→拆解→开发指南→模块文档） | 需要 git |

### 🤖 Agent 调度

| Skill | 用途 | 说明 | 配置 |
|-------|------|------|------|
| [uni-agent](./uni-agent/) | 统一Agent调度 | 一套API调用所有Agent协议（ANP/MCP/A2A/AITP），跨协议适配 | ⚙️ agents.yaml |

---

## ⚙️ 配置速查

需要配置的skill：

| Skill | 配置文件 | 需要填写 |
|-------|---------|---------|
| **image-service** | `config/settings.json` | 图像生成API（地址+密钥+模型）、视觉理解API（地址+密钥+模型） |
| **video-creator** | `video_config.yaml` | TTS API配置 |
| **smart-query** | `config/settings.json` | SSH连接（host/port/username/password）、数据库连接（type/host/port/database） |
| **uni-agent** | `config/agents.yaml` | Agent注册（协议类型、地址、能力描述） |
| **auto-douyin** | 运行时生成 | 执行 `scripts/get_cookie.py` 扫码登录，自动保存Cookie |
| **auto-redbook** | 环境变量 | `XHS_COOKIE`，从浏览器登录小红书后获取 |
| **auto-weixin-video** | 运行时生成 | 执行 `scripts/get_cookie.py` 微信扫码登录，自动保存Cookie |

其余13个skill无需配置，开箱即用（build-project-docs 仅需系统已安装 git）。

---

## 🔧 环境依赖

| 依赖 | 涉及Skill | 安装方式 |
|------|----------|---------|
| **Python 3.10+** | image-service, video-creator, csv-data-summarizer, auto-*, smart-query, uni-agent | 系统自带或 `brew install python` |
| **ffmpeg** | video-creator, videocut-* | `brew install ffmpeg` |
| **Playwright** | auto-douyin, auto-redbook, auto-weixin-video | `pip install playwright && playwright install chromium` |
| **httpx + Pillow + numpy** | image-service | `pip install httpx pillow numpy` |
| **pandas + matplotlib** | csv-data-summarizer | `pip install pandas matplotlib` |

---

## 安装使用

将需要的skill目录复制到 `~/.opencode/skills/`（OpenCode）或 `~/.openclaw/skills/`（OpenClaw）下即可：

```bash
# 复制单个skill
cp -r image-service ~/.opencode/skills/

# 复制全部
cp -r */ ~/.opencode/skills/
```

## License

MIT
