# auto-douyin

抖音视频自动发布技能。基于 Playwright 浏览器自动化，模拟真实用户操作抖音创作者中心。

## 功能

- 🔐 扫码登录 + Cookie 持久化
- 📤 自动上传视频
- 📝 自动填充标题、话题标签
- 🖼️ 支持自定义封面
- ⏰ 支持定时发布
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

打开浏览器后用抖音 APP 扫码登录，Cookie 自动保存。

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
| `--title` | `-t` | 视频标题（最多30字） | ✅ |
| `--tags` | `-g` | 话题标签，逗号分隔 | ❌ |
| `--cover` | `-c` | 封面图片路径 | ❌ |
| `--schedule` | `-s` | 定时发布（YYYY-MM-DD HH:MM） | ❌ |
| `--headless` | | 无头模式 | ❌ |

## 目录结构

```
auto-douyin/
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

- Cookie 有效期较长，失效后重新扫码即可
- 建议控制发布频率，避免触发平台风控
- 推荐视频格式：MP4，分辨率 1080×1920（9:16 竖版）

## 参考

基于 [social-auto-upload](https://github.com/dreammis/social-auto-upload) 项目。
