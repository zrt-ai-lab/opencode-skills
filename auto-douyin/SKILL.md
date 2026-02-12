---
name: auto-douyin
description: 抖音视频自动发布技能。当用户需要发布视频到抖音时使用这个技能。技能包含：获取登录Cookie、上传视频、设置标题话题、定时发布等功能。
---

# 抖音视频自动发布技能

这个技能用于自动化发布视频到抖音创作者中心。

## 使用场景

- 用户需要发布视频到抖音时
- 用户说"发抖音"、"上传抖音"、"发布到抖音"时
- 用户有视频文件需要分发到抖音平台时

## 技术原理

基于 Playwright 浏览器自动化，模拟真实用户操作抖音创作者中心（https://creator.douyin.com）：
1. 首次使用需扫码登录，保存 Cookie
2. 后续使用 Cookie 自动登录
3. 自动化填充标题、话题、封面等信息
4. 支持定时发布

## 前置条件

### 1. 安装依赖

```bash
pip install playwright
playwright install chromium
```

### 2. 首次登录获取 Cookie

```bash
python .opencode/skills/auto-douyin/scripts/get_cookie.py
```

执行后会打开浏览器，使用抖音 APP 扫码登录，登录成功后 Cookie 会自动保存。

## 工作流程

### 第一步：确认登录状态

检查 Cookie 是否存在且有效：

```bash
python .opencode/skills/auto-douyin/scripts/check_cookie.py
```

如果 Cookie 失效，需要重新获取：

```bash
python .opencode/skills/auto-douyin/scripts/get_cookie.py
```

### 第二步：准备视频文件

视频文件要求：
- 格式：`.mp4`（推荐）
- 分辨率：建议 1080x1920（竖版 9:16）
- 文件大小：建议不超过 4GB

可选：准备同名的封面图片（`.png` 或 `.jpg`）

### 第三步：发布视频

```bash
python .opencode/skills/auto-douyin/scripts/publish.py \
    --video "视频文件路径" \
    --title "视频标题" \
    --tags "话题1,话题2,话题3" \
    [--cover "封面图片路径"] \
    [--schedule "2025-01-31 18:00"]
```

#### 参数说明

| 参数 | 简写 | 说明 | 必填 |
|------|------|------|------|
| `--video` | `-v` | 视频文件路径 | ✅ |
| `--title` | `-t` | 视频标题（最多30字） | ✅ |
| `--tags` | `-g` | 话题标签，逗号分隔 | ❌ |
| `--cover` | `-c` | 封面图片路径 | ❌ |
| `--schedule` | `-s` | 定时发布时间（格式：YYYY-MM-DD HH:MM） | ❌ |
| `--headless` | | 无头模式运行（不显示浏览器） | ❌ |

#### 使用示例

```bash
# 立即发布，自动生成封面
python .opencode/skills/auto-douyin/scripts/publish.py \
    -v ~/Videos/demo.mp4 \
    -t "今天学到一个超实用的技巧" \
    -g "干货分享,效率提升,学习"

# 定时发布，指定封面
python .opencode/skills/auto-douyin/scripts/publish.py \
    -v ~/Videos/demo.mp4 \
    -t "周末vlog｜一个人的惬意时光" \
    -g "vlog,周末日常,生活记录" \
    -c ~/Videos/demo_cover.png \
    -s "2025-02-01 18:00"

# 无头模式（后台运行）
python .opencode/skills/auto-douyin/scripts/publish.py \
    -v ~/Videos/demo.mp4 \
    -t "测试视频" \
    --headless
```

## 目录结构

```
.opencode/skills/auto-douyin/
├── skill.md              # 技能说明文档
├── scripts/
│   ├── get_cookie.py     # 获取登录 Cookie
│   ├── check_cookie.py   # 检查 Cookie 有效性
│   └── publish.py        # 发布视频主脚本
└── cookies/
    └── douyin.json       # Cookie 存储文件（自动生成）
```

## 注意事项

1. **Cookie 有效期**：Cookie 通常有效期较长，但如果长时间未使用或平台更新，可能需要重新登录
2. **发布频率**：建议控制发布频率，避免被平台识别为异常行为
3. **标题限制**：抖音标题最多30字，超出会自动截断
4. **话题数量**：建议添加3-5个相关话题，提高曝光
5. **封面选择**：如不指定封面，系统会自动从视频中选取推荐封面
6. **定时发布**：定时发布时间需在当前时间之后，且在平台允许的时间范围内

## 常见问题

### Q: Cookie 失效怎么办？
A: 重新运行 `get_cookie.py` 扫码登录即可。

### Q: 上传失败怎么办？
A: 检查网络连接，确认视频文件格式正确，查看脚本输出的错误信息。

### Q: 如何批量发布？
A: 可以编写循环脚本，依次调用 `publish.py`，建议每次发布间隔几分钟。

## 参考项目

本技能参考了 [social-auto-upload](https://github.com/dreammis/social-auto-upload) 项目的实现。
