# 文章插图场景

## 概述

智能文章插图生成器，分析Markdown文章结构，自动识别需要配图的位置和类型，批量生成插图。**6类型 × 8风格 = 48种组合**。

## 快速使用

```bash
# 自动分析+生成（Notion风）
python scenes/article-illust/zlab_article_illustrator.py article.md --style notion -o images/

# 强制所有插图为流程图类型
python scenes/article-illust/zlab_article_illustrator.py article.md --type flowchart --style blueprint -o images/

# 查看选项
python scenes/article-illust/zlab_article_illustrator.py --list
```

## 工作流程

1. **分析文章** → 按h2/h3拆分章节
2. **智能匹配** → 根据关键词自动推荐每个章节的插图类型
3. **输出规划** → 展示配图位置和类型
4. **逐张生成** → 按类型×风格生成插图

## 类型（6种）— 自动匹配

| 类型 | 名称 | 触发关键词 |
|------|------|-----------|
| infographic | 数据可视化 | 数据、统计、增长、比例 |
| scene | 氛围插图 | 场景、想象、故事、感受 |
| flowchart | 流程图 | 步骤、流程、首先、然后 |
| comparison | 对比图 | 对比、vs、区别、优劣 |
| framework | 概念图 | 架构、框架、模型、体系 |
| timeline | 时间线 | 历史、阶段、发展、版本 |

## 风格（8种）

| 风格 | 名称 | 适用 |
|------|------|------|
| notion | 极简线条 | 知识分享（默认） |
| elegant | 精致优雅 | 商业 |
| warm | 友好亲切 | 个人成长 |
| minimal | 极简禅意 | 哲学 |
| blueprint | 技术蓝图 | 架构设计 |
| watercolor | 水彩艺术 | 生活方式 |
| editorial | 杂志编辑 | 科技解说 |
| scientific | 学术精确 | 学术研究 |

## 参数

| 参数 | 说明 |
|------|------|
| article | Markdown文章路径（必填） |
| --style | 视觉风格（默认 notion） |
| --type | 强制指定插图类型（不指定则自动判断） |
| -r, --ratio | 宽高比（默认 16:9） |
| -o, --output | 输出目录（默认 illustrations/） |
| --list | 列出所有选项 |
