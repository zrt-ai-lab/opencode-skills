---
name: image-service
description: 多模态图像处理技能，支持文生图、图生图、图生文、长图拼接、营销物料包、产品设计图、元素拆解图、社交媒体套图。当用户提到截图，查看,「画图」「生成图片」「画个XX」「图片处理」「图生图」「OCR」「识别图片」「拼长图」「信息图」「配图」「产品图」「物料包」「营销素材」「详情页」「电商图」「设计图」「爆炸图」「拆解」「套图」「九宫格」等关键词时触发。注意：如果用户要求的是视频（含配图+配音），可应使用video-creator技能。
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

| 配置项 | 值                         |
|-------|---------------------------|
| IMAGE_API_BASE_URL | `https://xxx/v1`          |
| IMAGE_MODEL | `Gemini3`                 |
| VISION_MODEL | `qwen2.5-vl-72b-instruct` |

## 执行规范

**图片默认保存到命令执行时的当前工作目录**：

1. **不要**使用 `workdir` 切换到 skill 目录执行命令
2. **始终**在用户的工作目录下执行，使用脚本的绝对路径
3. 脚本路径：skill 目录下的 `scripts/`

```bash
# 正确示例（PYTHON 和 SKILL_DIR 替换为你环境的实际路径）
$PYTHON $SKILL_DIR/scripts/text_to_image.py "描述" -r 3:4 -o output.png
```

## 快速使用

### 文生图

```bash
$PYTHON $SKILL_DIR/scripts/text_to_image.py "信息图风格，标题：AI技术趋势" -r 16:9
$PYTHON $SKILL_DIR/scripts/text_to_image.py "竖版海报，产品展示" -r 3:4 -o poster.png
```

参数：`-r` 宽高比 | `-s` 尺寸 | `-o` 输出路径

支持比例：`1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, `21:9`

### 图生图

```bash
$PYTHON $SKILL_DIR/scripts/image_to_image.py input.png "编辑描述" -r 3:4
```

### 图生文

```bash
$PYTHON $SKILL_DIR/scripts/image_to_text.py image.jpg -m describe
$PYTHON $SKILL_DIR/scripts/image_to_text.py screenshot.png -m ocr
```

模式：`describe` | `ocr` | `chart` | `fashion` | `product` | `scene`

### 长图拼接

```bash
$PYTHON $SKILL_DIR/scripts/merge_long_image.py img1.png img2.png -o output.png --blend 20
$PYTHON $SKILL_DIR/scripts/merge_long_image.py -p "*.png" -o long.png --sort name
```

参数：`-p` 通配符 | `-o` 输出 | `-w` 宽度 | `-g` 间隔 | `--blend` 融合 | `--sort` 排序

### 调研配图

```bash
$PYTHON $SKILL_DIR/scripts/research_image.py -t arch -n "标题" -c "内容" -o output.png
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

---

## 营销物料生成（产品图/物料包/设计图/元素拆解）

当用户提到「产品图」「物料包」「营销素材」「详情页」「元素拆解」「爆炸图」「套图」「多尺寸」「电商图」等关键词时，按以下流程执行。

**提示词模板库**：`references/marketing-templates.md`（必须加载，里面有完整的分类模板）

### 能力矩阵

| 能力 | 触发词 | 流程 | 输出 |
|------|--------|------|------|
| 电商详情长图 | 详情页、长图、商品介绍 | 叠罗汉串行生图 → merge 拼接 | 1张长图 |
| 营销物料包 | 物料包、营销素材、多尺寸 | 拆元素 → 多角度多场景 → zip | 10-15张 + zip |
| 产品设计图 | 产品图、渲染图、效果图 | 基准图 → 多角度/配色变体 | 3-8张 |
| 元素拆解图 | 拆解、爆炸图、分解、特写 | 整体图 → 局部特写/功能拆解 | 4-8张 |
| 社交媒体套图 | 套图、九宫格、朋友圈 | 统一风格 → 多尺寸适配 | 9张（1:1） |
| 多配色/SKU图 | 配色、多色、SKU | 基准图 → 图生图换色 | N张 |

### 流程一：电商详情长图

```
输入：产品名 + 卖点 + 风格
  ↓
Step 1：规划分屏（通常5-8屏）
  - 屏1：Hero大图（产品+核心卖点）
  - 屏2-N：逐个卖点展开（功能/材质/场景/参数）
  - 末屏：规格参数表
  ↓
Step 2：叠罗汉串行生图（必须读 references/long-image-guide.md）
  - 第1屏：text_to_image 生成基准
  - 第2-N屏：image_to_image 以上一屏为参考，保持风格一致
  ↓
Step 3：merge_long_image 拼接（--blend 20 融合接缝）
  ↓
Step 4：输出长图 + 各分屏原图
```

### 流程二：营销物料包（重点！）

**铁律：不是同一张图改尺寸！是拆元素、换角度、换场景！**

```
输入：产品名 + 卖点列表 + 风格偏好
  ↓
Step 1：生基准主图（text_to_image，产品全貌 16:9）
  ↓
Step 2：元素拆解（image_to_image × 4-6张）
  - 核心卖点微距特写（1:1）
  - 功能爆炸图/拆解图（3:4）
  - 材质/工艺细节（4:3）
  - 配件全家福（16:9）
  ↓
Step 3：场景变体（text_to_image / image_to_image × 3-4张）
  - 生活使用场景（16:9）
  - 工作使用场景（4:3）
  - 开箱/拆封场景（1:1）
  - 艺术剪影/氛围图（21:9）
  ↓
Step 4：营销创意（text_to_image × 3-4张）
  - 对比评测图（3:4）
  - 数据可视化/声波图（16:9）
  - 多配色SKU展示（16:9）
  - 九宫格社交媒体（1:1）
  ↓
Step 5：全部打包 zip + 逐张预览发送
```

**并发规则**：同一批最多8张并发，超过分批。失败的单独重试。

### 流程三：产品设计图

```
输入：产品名 + 设计要求
  ↓
Step 1：text_to_image 生基准主图（产品正面，16:9）
  ↓
Step 2：image_to_image 生变体（以基准图为参考）
  - 45度角展示
  - 侧面/背面
  - 俯视图
  - 不同配色版本
  - 不同使用场景
```

### 流程四：元素拆解图

```
输入：产品图（已有图片）或产品描述
  ↓
Step 1：如有产品图 → image_to_image 拆解；无图 → text_to_image 先生全貌
  ↓
Step 2：逐元素生成（image_to_image）
  - 爆炸图/分解视角
  - 局部1微距特写 + 功能标注
  - 局部2微距特写 + 工艺标注
  - 局部3微距特写 + 材质标注
  ↓
Step 3：可选拼长图（merge_long_image）
```

### 流程五：社交媒体套图

```
输入：产品/主题 + 平台（小红书/朋友圈/微博）
  ↓
Step 1：确定数量和比例
  - 小红书：6-9张，3:4
  - 朋友圈九宫格：9张，1:1
  - 微博：4-9张，16:9 或 1:1
  ↓
Step 2：规划每张内容（参考 marketing-templates.md 九宫格模板）
  ↓
Step 3：统一风格前缀，并发生成
  ↓
Step 4：按顺序编号输出
```

### 通用规范

1. **提示词必须中文**，加载 `references/marketing-templates.md` 获取模板
2. **同一批次风格统一**：定义风格前缀，所有图片复用
3. **并发≤8张**，失败单独重试
4. **命名规范**：`{类型}_{序号}.png`（如 `detail_01.png`、`scene_gaming.png`）
5. **交付时**：逐张发送预览 + 打包 zip（如有多张）

---

## 触发关键词

- **生成类**：生成图片、创建图片、文生图、图生图、信息图、数据可视化
- **分析类**：分析图片、OCR、识别文字、图生文
- **拼接类**：长图、微信长图、拼接图片
- **营销类**：产品图、物料包、营销素材、详情页、电商图、设计图、渲染图、效果图
- **拆解类**：拆解、爆炸图、分解、特写、微距
- **套图类**：套图、九宫格、朋友圈、多尺寸、多配色、SKU
