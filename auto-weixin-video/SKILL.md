---
name: auto-weixin-video
description: 微信视频号自动发布技能。当用户需要发布视频到微信视频号时使用这个技能。技能包含：获取登录Cookie、上传视频、设置标题话题、定时发布、原创声明等功能。
---

# 微信视频号自动发布技能

这个技能用于自动化发布视频到微信视频号创作者中心。

## 使用场景

- 用户需要发布视频到视频号时
- 用户说"发视频号"、"上传视频号"、"发布到微信视频号"时
- 用户有视频文件需要分发到视频号平台时

## 技术原理

基于 Playwright 浏览器自动化，模拟真实用户操作微信视频号创作者中心（https://channels.weixin.qq.com）：
1. 首次使用需微信扫码登录，保存 Cookie
2. 后续使用 Cookie 自动登录
3. 自动化填充标题、话题、短标题等信息
4. 支持定时发布、原创声明、添加到合集

## 前置条件

### 1. 安装依赖

```bash
pip install playwright
playwright install chromium
```

### 2. 首次登录获取 Cookie

```bash
python .opencode/skills/auto-weixin-video/scripts/get_cookie.py
```

执行后会打开浏览器，使用微信扫码登录，登录成功后 Cookie 会自动保存。

## 工作流程

### 第一步：确认登录状态

检查 Cookie 是否存在且有效：

```bash
python .opencode/skills/auto-weixin-video/scripts/check_cookie.py
```

如果 Cookie 失效，需要重新获取：

```bash
python .opencode/skills/auto-weixin-video/scripts/get_cookie.py
```

### 第二步：准备视频文件

视频文件要求：
- 格式：`.mp4`（推荐）
- 分辨率：建议 1080x1920（竖版 9:16）或 1920x1080（横版 16:9）
- 时长：建议 1 分钟以内效果最佳

### 第三步：发布视频

```bash
python .opencode/skills/auto-weixin-video/scripts/publish.py \
    --video "视频文件路径" \
    --title "视频标题" \
    --tags "话题1,话题2,话题3" \
    [--original] \
    [--schedule "2025-01-31 18:00"]
```

#### 参数说明

| 参数 | 简写 | 说明 | 必填 |
|------|------|------|------|
| `--video` | `-v` | 视频文件路径 | ✅ |
| `--title` | `-t` | 视频标题 | ✅ |
| `--tags` | `-g` | 话题标签，逗号分隔 | ❌ |
| `--original` | `-o` | 声明原创 | ❌ |
| `--category` | `-c` | 原创类型（如：生活、科技） | ❌ |
| `--schedule` | `-s` | 定时发布时间（格式：YYYY-MM-DD HH:MM） | ❌ |
| `--draft` | | 保存为草稿而不发布 | ❌ |
| `--headless` | | 无头模式运行（不显示浏览器） | ❌ |

#### 使用示例

```bash
# 立即发布
python .opencode/skills/auto-weixin-video/scripts/publish.py \
    -v ~/Videos/demo.mp4 \
    -t "今天学到一个超实用的技巧" \
    -g "干货分享,效率提升,学习"

# 声明原创 + 定时发布
python .opencode/skills/auto-weixin-video/scripts/publish.py \
    -v ~/Videos/demo.mp4 \
    -t "周末vlog｜一个人的惬意时光" \
    -g "vlog,周末日常,生活记录" \
    --original \
    -s "2025-02-01 18:00"

# 保存为草稿
python .opencode/skills/auto-weixin-video/scripts/publish.py \
    -v ~/Videos/demo.mp4 \
    -t "测试视频" \
    --draft
```

## 目录结构

```
.opencode/skills/auto-weixin-video/
├── skill.md              # 技能说明文档
├── scripts/
│   ├── get_cookie.py     # 获取登录 Cookie
│   ├── check_cookie.py   # 检查 Cookie 有效性
│   └── publish.py        # 发布视频主脚本
└── cookies/
    └── weixin_video.json # Cookie 存储文件（自动生成）
```

## 注意事项

1. **Cookie 有效期**：微信 Cookie 有效期相对较短，建议每次使用前检查
2. **发布频率**：建议控制发布频率，避免被平台识别为异常行为
3. **短标题**：系统会自动从标题生成 6-16 字的短标题
4. **话题数量**：建议添加 3-5 个相关话题
5. **原创声明**：勾选原创需要符合平台原创规范，否则可能被处罚
6. **合集**：如果账号有合集，视频会自动添加到第一个合集

## 常见问题

### Q: Cookie 失效怎么办？
A: 重新运行 `get_cookie.py` 扫码登录即可。

### Q: 上传失败怎么办？
A: 检查网络连接，确认视频文件格式正确。视频号对 H264 编码支持最好。

### Q: 如何批量发布？
A: 可以编写循环脚本，依次调用 `publish.py`，建议每次发布间隔几分钟。

## 参考项目

本技能参考了 [social-auto-upload](https://github.com/dreammis/social-auto-upload) 项目的实现。
