---
name: image-service
description: 多模态图像处理技能，支持信息图、封面图、长图、幻灯片、漫画、文章插图、小红书图、营销物料等多场景生图，以及图生图、图生文、长图拼接。
---

# zlab 图像处理技能

## 配置

| 配置项 | 值 |
|-------|-----|
| API | `配置文件中设置` |
| 生图模型 | `配置文件中设置` |
| 视觉模型 | `配置文件中设置` |
| 配置文件 | `config/settings.json` |

## 执行规范

- 脚本使用**绝对路径**调用，图片保存到**当前工作目录**
- 提示词**必须使用中文**，图中标题标签**必须中文**
- 含中文文字时，追加 `guides/text-rendering.md` 中的文字清晰后缀
- 默认宽高比 **16:9**，竖版场景（小红书/漫画）默认 **3:4**

## 🔀 场景路由（铁律：收到需求后第一步）

```
收到生图需求
  │
  ├─ 信息图/数据可视化/架构图/流程图/对比图/鱼骨图/思维导图/金字塔/漏斗/韦恩图/冰山图
  │  → 📊 信息图 → scenes/infographic/
  │
  ├─ 封面/头图/banner/公众号封面/文章封面
  │  → 🖼️ 封面图 → scenes/cover/
  │
  ├─ 长图/微信长图/多屏/从上到下/竖版长图/分段/多个段落
  │  → 📜 长图 → scenes/long-image/
  │
  ├─ 幻灯片/PPT图/slides/演示文稿
  │  → 📑 幻灯片 → scenes/slide-deck/
  │
  ├─ 漫画/连环画/分镜/绘本/知识漫画/故事图
  │  → 📖 漫画 → scenes/comic/
  │
  ├─ 文章插图/自动配图/智能插图/给文章配图
  │  → ✏️ 文章插图 → scenes/article-illust/
  │
  ├─ 小红书/笔记配图/种草图/卡片系列
  │  → 📱 小红书图 → scenes/xhs/
  │
  ├─ 海报/主图/电商/促销/九宫格/产品图/营销/物料
  │  → 🛍️ 营销物料 → scenes/marketing/
  │
  ├─ 改图/编辑图片/风格转换/基于这张图
  │  → 🔄 图生图 → core/image_to_image.py（直接执行）
  │
  ├─ 分析图片/OCR/识别文字/描述图片/图生文
  │  → 👁️ 图生文 → core/image_to_text.py（直接执行）
  │
  └─ 其他单图需求（一张图，无特殊场景）
     → 🎨 单图 → core/text_to_image.py（直接执行）
```

路由到场景后 → 加载该场景的 **README.md** 获取详细参数和用法 → 按下方执行流程操作。

---

## 📋 通用执行流程（所有场景共用）

### 第一步：分析需求

- 明确要生什么（主题、内容要点）
- 确定场景类型（已由路由判断）
- 确定数量（几张图）
- 确定比例（16:9 / 3:4 / 1:1 等）

### 第二步：规划方案（多图场景必须）

**单图**：可跳过直接生成。
**多图场景（长图/幻灯片/漫画/小红书/文章插图）**：必须先输出规划，等用户确认后再执行。

规划输出格式：
```
| 序号 | 内容概要 | 类型/布局 |
|-----|---------|----------|
| 1   | xxx     | xxx      |
| 2   | xxx     | xxx      |

**场景**：xx | **风格**：xx | **比例**：xx | **预计**：N张
```

### 第三步：执行生成

| 场景 | 执行方式 | 规则 |
|------|---------|------|
| 📊 信息图 | 场景脚本直接调用 | 单张可并发 |
| 🖼️ 封面图 | 场景脚本直接调用 | 单张 |
| 📜 长图 | core引擎串行 | **铁律：必须串行！** 首屏text_to_image，后续image_to_image参考上一屏，最后merge拼接 |
| 📑 幻灯片 | 场景脚本逐页 | 串行逐页生成 |
| 📖 漫画 | 场景脚本逐页 | **串行！** 首页text_to_image定调，后续image_to_image参考上一页 |
| ✏️ 文章插图 | 场景脚本批量 | 各章节独立，可并发（≤8张） |
| 📱 小红书 | 场景脚本逐张 | **串行！** 首张定调，后续参考上一张保风格一致 |
| 🛍️ 营销物料 | core引擎+模板 | 同风格可并发（≤8张） |
| 🔄 图生图 | core直接调用 | 单张 |
| 🎨 单图 | core直接调用 | 单张 |

### 第四步：质量校验

1. 生成完成后，**含中文文字的图**用 `core/image_to_text.py -m ocr` 校验文字是否清晰
2. OCR结果与预期不符 → 用 `core/image_to_image.py` 迭代修复（参考 `guides/text-rendering.md`）
3. 多图场景完成后，逐张展示给用户确认，不满意的单张重新生成

---

## 🛠️ 脚本速查

### 场景脚本

```bash
# 📊 信息图 — 20布局×17风格=340种
python3 scenes/infographic/zlab_infographic.py -l {布局} -s {风格} -n "标题" -c "内容" -o out.png
python3 scenes/infographic/zlab_infographic.py --list  # 查看所有选项

# 🖼️ 封面图 — 五维定制=3888种
python3 scenes/cover/zlab_cover.py -n "标题" --type {类型} --palette {配色} --rendering {渲染} --text {文字} --mood {氛围} -o out.png

# 📑 幻灯片 — 16种预设
python3 scenes/slide-deck/zlab_slide_deck.py article.md --style {预设} -o slides/
python3 scenes/slide-deck/zlab_slide_deck.py article.md --outline-only  # 仅看大纲

# 📖 漫画 — 5画风×7基调×6布局=210种
python3 scenes/comic/zlab_comic.py source.md --art {画风} --tone {基调} --layout {布局} -o comic/

# ✏️ 文章插图 — 6类型×8风格=48种
python3 scenes/article-illust/zlab_article_illustrator.py article.md --style {风格} -o images/

# 📱 小红书 — 9风格×6布局=54种
python3 scenes/xhs/zlab_xhs_images.py content.md --style {风格} --layout {布局} -o xhs/
```

所有场景脚本支持 `--list` 查看可用选项。

### 核心引擎

```bash
# 文生图
python3 core/text_to_image.py "中文描述" -r 16:9 -o output.png
python3 core/text_to_image.py "描述" -r 3:4 --ref ref.png -o output.png  # 参考图风格

# 图生图
python3 core/image_to_image.py input.png "编辑描述" -r 3:4 -o output.png

# 图生文
python3 core/image_to_text.py image.jpg -m describe|ocr|chart|fashion|product|scene

# 长图拼接
python3 core/merge_long_image.py img1.png img2.png -o output.png --blend 20
python3 core/merge_long_image.py -p "*.png" -o output.png --sort name
```

支持比例：`1:1` `2:3` `3:2` `3:4` `4:3` `4:5` `5:4` `9:16` `16:9` `21:9`

---

## 📚 通用指南（按需加载）

| 触发条件 | 文件 | 何时加载 |
|---------|------|---------|
| 图片含中文文字 | `guides/text-rendering.md` | 提示词要求含中文标题/标签时**必须加载** |
| 为PPT/文档配图 | `guides/color-sync.md` | 需要与其他载体配色协同时加载 |
| 需要优化生图效果 | `guides/prompt-guide.md` | 生图效果不理想需要改进时加载 |
| API接口问题 | `guides/api-reference.md` | 调试底层接口时加载 |
| 生成多屏长图 | `scenes/long-image/README.md` | 路由到长图场景时**必须加载** |
| 营销物料模板 | `scenes/marketing/templates.md` | 路由到营销场景时**必须加载** |
