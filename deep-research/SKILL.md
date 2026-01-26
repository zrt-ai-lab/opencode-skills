---
name: deep-research
description: 当用户要求"调研"、"深度调研"、"帮我研究"、"调研下这个"，或提到需要搜索、整理、汇总指定主题的技术内容时，应使用此技能。
metadata:
  version: "1.0.0"
---

# 深度调研技能（Deep Research Skill）

## 技能概述

此技能用于对技术主题进行深度调研，输出专业的调研报告文档。

| 能力 | 说明 |
|-----|------|
| 内容提取 | 从 URL、文档中提取核心信息 |
| 深度调研 | 联网搜索补充背景、对比、最新进展 |
| 报告生成 | **默认生成 Markdown 和 Word 两个版本** |
| 图解生成 | 为核心概念生成技术信息图 |
| Word 格式化 | 自动处理目录、标题加粗、表格实线等样式 |

## 触发规则

当用户消息包含以下关键词时使用此技能：
- 调研、深度调研、调研报告
- 帮我研究、帮我分析
- 调研下这个、看看这个

## 输出规范

每次调研任务必须同时提供：
1. **Markdown 版本**：用于 Obsidian 知识库沉淀和双链关联
2. **Word 版本**：用于正式汇报和外部分享，需经过脚本格式化处理

## 目录结构

每个调研主题创建独立文件夹，保持整洁：

```
{output_dir}/
├── Ralph-Loop/                    # 主题文件夹（英文短横线命名）
│   ├── images/                    # 该主题的信息图
│   │   ├── architecture.png
│   │   └── comparison.png
│   ├── Ralph-Loop调研报告.md      # Markdown 报告
│   └── Ralph-Loop调研报告.docx    # Word 报告
├── MCP-Protocol/
│   ├── images/
│   ├── MCP-Protocol调研报告.md
│   └── MCP-Protocol调研报告.docx
└── ...
```

命名规范：
- 文件夹名：英文，单词间用短横线连接，如 `Ralph-Loop`、`MCP-Protocol`
- 报告文件：`{主题名}调研报告.md` 和 `{主题名}调研报告.docx`
- 图片目录：每个主题文件夹下单独的 `images/` 目录

## 调研流程

### 第一步：创建主题目录

根据调研主题创建独立文件夹：

```bash
mkdir -p "{output_dir}/{主题名}/images"
```

### 第二步：内容获取

1. 如果用户提供 URL，使用 webfetch 获取内容
2. 提炼核心概念、技术原理、关键信息
3. 识别需要深入调研的点

### 第三步：深度调研

使用 Task 工具进行联网搜索，补充：
- 技术背景和发展历程
- 竞品对比和差异化
- 社区讨论和实际案例
- GitHub 仓库和开源实现
- 最新进展和趋势

### 第四步：图解生成

使用预设风格脚本生成统一手绘风格的信息图。

#### 生图触发规则

| 内容类型 | 是否生图 | 图解类型 | 说明 |
|---------|---------|---------|------|
| 核心架构/原理 | 必须 | arch | 系统结构、技术栈、模块组成 |
| 流程/步骤 | 必须 | flow | 工作流、执行顺序、操作步骤 |
| A vs B 对比 | 必须 | compare | 两种方案/技术的对比 |
| 3个以上要素 | 建议 | concept | 核心概念、多个方面组成 |
| 纯文字表格 | 不需要 | - | 用 Markdown 表格即可 |
| 代码示例 | 不需要 | - | 用代码块即可 |

#### 预设风格模板

所有配图统一使用手绘体可视化风格，保持系列一致性：

| 类型 | 命令参数 | 配色 | 布局 |
|------|---------|------|------|
| 架构图 | `-t arch` | 科技蓝 #4A90D9 | 分层/模块化 |
| 流程图 | `-t flow` | 蓝+绿+橙 | 从上到下 |
| 对比图 | `-t compare` | 蓝 vs 橙 | 左右分栏 |
| 概念图 | `-t concept` | 蓝紫渐变 | 中心发散 |

#### 生成命令

使用 `research_image.py` 脚本生成：

```bash
# 架构图
python .opencode/skills/image-service/scripts/research_image.py \
  -t arch \
  -n "Ralph Loop 核心架构" \
  -c "展示 Prompt、Agent、Stop Hook、Files 四个模块的循环关系" \
  -o "{output_dir}/{主题名}/images/architecture.png"

# 流程图
python .opencode/skills/image-service/scripts/research_image.py \
  -t flow \
  -n "Stop Hook 工作流程" \
  -c "Agent尝试退出、Hook触发、检查条件、允许或阻止退出的完整流程" \
  -o "{output_dir}/{主题名}/images/flow.png"

# 对比图
python .opencode/skills/image-service/scripts/research_image.py \
  -t compare \
  -n "ReAct vs Ralph Loop" \
  -c "左侧ReAct依赖自我评估停止，右侧Ralph使用外部Hook控制" \
  -o "{output_dir}/{主题名}/images/comparison.png"

# 概念图
python .opencode/skills/image-service/scripts/research_image.py \
  -t concept \
  -n "状态持久化要素" \
  -c "中心是Agent，周围是progress.txt、prd.json、Git历史、代码文件" \
  -o "{output_dir}/{主题名}/images/concept.png"
```

#### 图片命名规范

| 图解类型 | 文件名 |
|---------|--------|
| 架构图 | `architecture.png` 或 `{具体名称}_arch.png` |
| 流程图 | `flow.png` 或 `{具体名称}_flow.png` |
| 对比图 | `comparison.png` 或 `{A}_vs_{B}.png` |
| 概念图 | `concept.png` 或 `{具体名称}_concept.png` |

### 第五步：报告撰写

按标准模板撰写 Markdown 报告，存放到主题文件夹：

```
{output_dir}/{主题名}/{主题名}调研报告.md
```

报告中引用图片使用相对路径：
```markdown
![架构图](images/architecture.png)
```

### 第六步：Word 导出

```bash
# 进入主题目录
cd "{output_dir}/{主题名}"

# 生成 Word（--resource-path=. 确保图片正确引用）
# 注意：不要使用 --toc 参数，因为 Markdown 中已有手写目录
pandoc "{主题名}调研报告.md" -o "{主题名}调研报告.docx" --resource-path=.

# 格式化 Word
python ../../../.opencode/skills/deep-research/scripts/format_docx.py "{主题名}调研报告.docx"
```

## 写作原则

调研报告的核心价值：深入研究、降低团队吸收成本、提供专家级建议。

1. 理解透彻：不能一知半解或大段拷贝，必须消化吸收后用自己的话表达
2. 体现思考：有判断、有建议，而非仅仅陈述现状
3. 细节佐证：有过程和细节支撑结论，不空谈
4. 逻辑清晰：有分段、有结构、有编号
5. 配图说明：核心概念必须配信息图
6. 去除 AI 味：
   - 不使用「」、" " 等特殊符号
   - 不用过多强调符号和 emoji
   - 行文自然流畅，像人写的专业文档
   - 避免"首先、其次、总之"等套话

## 报告模板

```markdown
---
date: YYYY-MM-DD
type: 调研报告
领域: {技术领域}
tags: [调研, {主题关键词}]
---

# XX调研报告

> 调研日期：YYYY年M月D日

---

## 目录

- 一、简介
- 二、启示
- 三、核心介绍
  - 3.1 XXX
  - 3.2 XXX
- 四、附录
  - 4.1 详细文档
  - 4.2 参考资料

---

## 一、简介

（快速说明调研内容，简短重点）

是什么，主要用来做什么，属于什么类别。有哪些能力，有什么特点。和竞品相比，有哪些区别，主打什么。

1. 要点一
2. 要点二
3. 要点三

---

## 二、启示

（调研内容带来的启示、值得学习借鉴之处、与现有产品如何结合、是否值得推荐）

1. 启示一
2. 启示二
3. 启示三

---

## 三、核心介绍

（正文部分，详细说明调研内容的原理/搭建/操作/使用过程，含信息图及流程说明）

### 3.1 XXX

![图解说明](images/xxx.png)

上图展示了...（图解说明，让读者看图就能理解）

详细内容...

### 3.2 XXX

详细内容...

---

## 四、附录

### 4.1 详细文档

（更详细的配置/操作过程）

### 4.2 参考资料

**官方文档**

- 文档名称: https://xxx

**开源实现**

- 项目名称: https://github.com/xxx

**社区讨论**

- 讨论来源: https://xxx
```

## 脚本说明

### format_docx.py

Word 文档格式化脚本，功能包括：

1. 标题居中，黑色字体（去除 pandoc 默认蓝色）
2. "Table of Contents" 替换为中文"目录"
3. 目录页单独一页
4. 一级标题（简介、启示等）前自动分页
5. 表格保持完整不跨页断开
6. 代码块保持完整不断开
7. 日期行居中

用法：
```bash
python .opencode/skills/deep-research/scripts/format_docx.py "输入.docx" ["输出.docx"]
```

## 完整调研示例

用户输入：
> 调研下 Ralph Loop

执行流程：

```bash
# 1. 创建主题目录
mkdir -p "{output_dir}/Ralph-Loop/images"

# 2. 获取内容（如有 URL）
webfetch https://example.com/article

# 3. 深度调研（使用 Task 工具联网搜索）

# 4. 生成信息图
python .opencode/skills/image-service/scripts/text_to_image.py "技术架构图..." --output "{output_dir}/Ralph-Loop/images/architecture.png"

# 5. 撰写报告
# 写入 {output_dir}/Ralph-Loop/Ralph-Loop调研报告.md

# 6. 导出 Word（不使用 --toc，Markdown 已有手写目录）
cd "{output_dir}/Ralph-Loop"
pandoc "Ralph-Loop调研报告.md" -o "Ralph-Loop调研报告.docx" --resource-path=.
python ../../../.opencode/skills/deep-research/scripts/format_docx.py "Ralph-Loop调研报告.docx"
```

输出文件：
```
{output_dir}/Ralph-Loop/
├── images/
│   ├── architecture.png
│   └── comparison.png
├── Ralph-Loop调研报告.md
└── Ralph-Loop调研报告.docx
```

## 依赖

- pandoc：Markdown 转 Word
- python-docx：Word 格式化
- image-service 技能：生成信息图
