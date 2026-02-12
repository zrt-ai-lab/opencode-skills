# auto-weixin-video

微信视频号自动发布技能。基于 Playwright 浏览器自动化，模拟真实用户操作视频号创作者中心。

## 功能

- 🔐 微信扫码登录 + Cookie 持久化
- 📤 自动上传视频
- 📝 自动填充标题、话题、短标题
- ✍️ 支持原创声明
- 📁 自动添加到合集
- ⏰ 支持定时发布
- 📋 支持保存为草稿
- 🤖 支持无头模式后台运行

## 快速开始

### 1. 安装依赖

```bash
pip install playwright
playwright install chromium
```

### 2. 首次登录

```bash
python scripts/get_cookie.py
```

打开浏览器后用微信扫码登录，Cookie 自动保存。

### 3. 发布视频

```bash
python scripts/publish.py \
    -v ~/Videos/demo.mp4 \
    -t "今天学到一个超实用的技巧" \
    -g "干货分享,效率提升,学习"
```

## 参数说明

| 参数 | 简写 | 说明 | 必填 |
|------|------|------|------|
| `--video` | `-v` | 视频文件路径 | ✅ |
| `--title` | `-t` | 视频标题 | ✅ |
| `--tags` | `-g` | 话题标签，逗号分隔 | ❌ |
| `--original` | `-o` | 声明原创 | ❌ |
| `--category` | `-c` | 原创类型（生活、科技等） | ❌ |
| `--schedule` | `-s` | 定时发布（YYYY-MM-DD HH:MM） | ❌ |
| `--draft` | | 保存为草稿 | ❌ |
| `--headless` | | 无头模式 | ❌ |

## 目录结构

```
auto-weixin-video/
├── SKILL.md              # 技能说明（Agent 读取）
├── README.md             # 本文件
├── scripts/
│   ├── get_cookie.py     # 扫码登录获取 Cookie
│   ├── check_cookie.py   # 检查 Cookie 有效性
│   └── publish.py        # 发布视频
└── cookies/
    └── .gitkeep          # Cookie 文件（自动生成，已 gitignore）
```

## 注意事项

- 微信 Cookie 有效期相对较短，建议每次使用前检查
- 系统会自动从标题生成 6-16 字的短标题
- 原创声明需符合平台规范，否则可能被处罚
- 如果账号有合集，视频会自动添加到第一个合集
- 推荐视频格式：MP4，H264 编码，1080×1920（9:16）或 1920×1080（16:9）

## 参考

基于 [social-auto-upload](https://github.com/dreammis/social-auto-upload) 项目。
