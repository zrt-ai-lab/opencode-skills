---
name: image-service
description: 多模态图像处理技能，支持文生图、图生图、图生文、长图拼接。当用户提到图片、图像、生成图、信息图、OCR 等关键词时触发。
---

# 图像处理技能

## 概述

| 能力 | 说明 | 脚本 |
|-----|------|------|
| 文生图 | 根据中文文本描述生成图片 | `scripts/text_to_image.py` |
| 图生图 | 在已有图片基础上进行编辑 | `scripts/image_to_image.py` |
| 图生文 | 分析图片内容（描述、OCR、图表等） | `scripts/image_to_text.py` |
| 长图拼接 | 将多张图片垂直拼接为微信长图 | `scripts/merge_long_image.py` |
| 调研配图 | 预设手绘风格的调研报告信息图 | `scripts/research_image.py` |

## 配置

配置文件：`config/settings.json`

| 配置项 | 值 |
|-------|-----|
| IMAGE_API_BASE_URL | `${IMAGE_API_BASE_URL}` |
| IMAGE_MODEL | `dall-e-3` |
| VISION_MODEL | `qwen2.5-vl-72b-instruct` |

## 执行规范

**图片默认保存到命令执行时的当前工作目录**：

1. **不要**使用 `workdir` 切换到 skill 目录执行命令
2. **始终**在用户的工作目录下执行，使用脚本的绝对路径
3. 脚本路径：`.opencode/skills/image-service/scripts/`

```bash
# 正确示例
python .opencode/skills/image-service/scripts/text_to_image.py "描述" -r 3:4 -o output.png
```

## 快速使用

### 文生图

```bash
python .opencode/skills/image-service/scripts/text_to_image.py "信息图风格，标题：AI技术趋势" -r 16:9
python .opencode/skills/image-service/scripts/text_to_image.py "竖版海报，产品展示" -r 3:4 -o poster.png
```

参数：`-r` 宽高比 | `-s` 尺寸 | `-o` 输出路径

支持比例：`1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`

### 图生图

```bash
python .opencode/skills/image-service/scripts/image_to_image.py input.png "编辑描述" -r 3:4
```

### 图生文

```bash
python .opencode/skills/image-service/scripts/image_to_text.py image.jpg -m describe
python .opencode/skills/image-service/scripts/image_to_text.py screenshot.png -m ocr
```

模式：`describe` | `ocr` | `chart` | `fashion` | `product` | `scene`

### 长图拼接

```bash
python .opencode/skills/image-service/scripts/merge_long_image.py img1.png img2.png -o output.png --blend 20
python .opencode/skills/image-service/scripts/merge_long_image.py -p "*.png" -o long.png --sort name
```

参数：`-p` 通配符 | `-o` 输出 | `-w` 宽度 | `-g` 间隔 | `--blend` 融合 | `--sort` 排序

### 调研配图

```bash
python .opencode/skills/image-service/scripts/research_image.py -t arch -n "标题" -c "内容" -o output.png
```

类型：`arch` 架构图 | `flow` 流程图 | `compare` 对比图 | `concept` 概念图

## 执行前必做：需求类型判断（铁律）

**收到图片生成需求后，必须先判断是哪种类型，再决定执行方式：**

### 长图识别规则

提示词中出现以下任一特征，即判定为**长图需求**：

| 特征类型 | 识别关键词/模式 |
|---------|---------------|
| **明确声明** | 长图、长图海报、垂直长图、微信长图、Infographic、Long Banner |
| **分段结构** | 提示词包含多个段落（如"第1部分"、"顶部"、"中间"、"底部"）|
| **编号列表** | 使用 `### 1.`、`### 2.` 等编号分段 |
| **多屏内容** | 描述了3个及以上独立画面/模块 |
| **从上至下** | 出现"从上至下"、"从上到下"等描述 |

### 判断后的执行路径

```
识别为长图 → 必须先读取 references/long-image-guide.md → 按长图流程执行
识别为单图 → 直接使用 text_to_image.py 生成
```

**铁律：识别为长图后，禁止直接生成！必须先加载长图指南，按指南流程执行。**

## 详细指南（按需加载）

| 场景 | 触发条件 | 参考文档 |
|------|---------|---------|
| 生成多屏长图 | 命中上述长图识别规则 | `references/long-image-guide.md`（必须加载）|
| 图片含中文文字 | 提示词要求图片包含中文标题/文字 | `references/text-rendering-guide.md` |
| 为 PPT/文档配图 | 用户提供了配色要求或参考文档 | `references/color-sync-guide.md` |
| API 接口细节 | 需要了解底层实现 | `docs/api-reference.md` |
| 提示词技巧 | 需要优化提示词效果 | `docs/prompt-guide.md` |

## 提示词要点

1. **必须使用中文**撰写提示词
2. 图片中的标题、标签**必须为中文**
3. 默认宽高比 **16:9**，可通过 `-r` 参数调整
4. 推荐风格：信息图、数据可视化、手绘文字、科技插画

## 触发关键词

- **生成类**：生成图片、创建图片、文生图、图生图、信息图、数据可视化
- **分析类**：分析图片、OCR、识别文字、图生文
- **拼接类**：长图、微信长图、拼接图片
