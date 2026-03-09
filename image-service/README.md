# image-service

多模态图像处理技能，支持 8 大生图场景 + 图生文 + 长图拼接。

## 场景能力

| 场景 | 脚本 | 组合数 |
|------|------|--------|
| 📊 信息图 | `scenes/infographic/zlab_infographic.py` | 20布局×17风格=340 |
| 🖼️ 封面图 | `scenes/cover/zlab_cover.py` | 6×9×6×4×3=3888 |
| 📜 长图 | core引擎串行生成+拼接 | — |
| 📑 幻灯片 | `scenes/slide-deck/zlab_slide_deck.py` | 16种预设 |
| 📖 漫画 | `scenes/comic/zlab_comic.py` | 5×7×6=210 |
| ✏️ 文章插图 | `scenes/article-illust/zlab_article_illustrator.py` | 6×8=48 |
| 📱 小红书图 | `scenes/xhs/zlab_xhs_images.py` | 9×6=54 |
| 🛍️ 营销物料 | `scenes/marketing/templates.md` | 模板库 |

## 核心引擎

| 引擎 | 脚本 | 说明 |
|------|------|------|
| 文生图 | `core/text_to_image.py` | 中文描述→图片，支持10种比例 |
| 图生图 | `core/image_to_image.py` | 基于参考图编辑 |
| 图生文 | `core/image_to_text.py` | 图片分析（describe/ocr/chart等6种模式） |
| 长图拼接 | `core/merge_long_image.py` | 多图垂直拼接，支持融合过渡 |

## 快速开始

### 1. 配置 API

编辑 `config/settings.json`，填入你的 API 地址和密钥。支持任何 OpenAI 兼容的图像生成 API。

### 2. 使用示例

```bash
# 单图
python core/text_to_image.py "信息图风格，AI技术趋势" -r 16:9 -o out.png

# 信息图（金字塔+手绘风）
python scenes/infographic/zlab_infographic.py -l pyramid -s craft-handmade -n "AI技术栈" -c "顶层AGI，中层大模型，底层算力" -o ai.png

# 封面图（五维定制）
python scenes/cover/zlab_cover.py -n "深入AI Agent" --type conceptual --palette dark -o cover.png

# 漫画（日漫+温暖）
python scenes/comic/zlab_comic.py story.md --art manga --tone warm -o comic/

# 幻灯片
python scenes/slide-deck/zlab_slide_deck.py article.md --style blueprint -o slides/

# 文章智能配图
python scenes/article-illust/zlab_article_illustrator.py article.md --style notion -o images/

# 小红书卡片
python scenes/xhs/zlab_xhs_images.py article.md --style cute --layout balanced -o xhs/
```

所有场景脚本支持 `--list` 查看可用选项。

## 目录结构

```
image-service/
├── SKILL.md                 场景路由器（Agent入口）
├── config/settings.json     API配置
├── core/                    底层引擎（4个）
├── scenes/                  8大场景
│   ├── infographic/         信息图（20布局×17风格）
│   ├── cover/               封面图（五维定制）
│   ├── long-image/          长图（串行生成规范）
│   ├── slide-deck/          幻灯片（16预设）
│   ├── comic/               漫画（画风×基调×布局）
│   ├── article-illust/      文章插图（智能匹配）
│   ├── xhs/                 小红书（风格×布局）
│   └── marketing/           营销物料（模板库）
├── guides/                  通用指南
└── presets/                 共享预设
```

## 依赖

- Python 3.10+
- `httpx` — HTTP 请求
- `Pillow` + `numpy` — 长图拼接

```bash
pip install httpx pillow numpy
```

## License

MIT
