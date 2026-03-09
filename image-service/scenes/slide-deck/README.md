# 幻灯片图场景

## 概述

从Markdown内容生成专业幻灯片图片。4维度组合：**纹理 × 氛围 × 字体 × 密度**，16种预设风格。

## 快速使用

```bash
# 从Markdown生成
python scenes/slide-deck/zlab_slide_deck.py article.md --style blueprint -o slides/

# 仅看大纲
python scenes/slide-deck/zlab_slide_deck.py article.md --outline-only

# 查看所有预设
python scenes/slide-deck/zlab_slide_deck.py --list
```

## 预设风格（16种）

| 预设 | 名称 | 适用 | 维度组合 |
|------|------|------|---------|
| blueprint | 技术蓝图 | 架构、系统设计 | grid×cool×technical×balanced |
| chalkboard | 粉笔黑板 | 教育、教程 | organic×warm×handwritten×balanced |
| corporate | 商务专业 | 投资演示、提案 | clean×professional×geometric×balanced |
| minimal | 极简 | 高管简报 | clean×neutral×geometric×minimal |
| notion | Notion风 | 产品演示、SaaS | clean×neutral×geometric×dense |
| dark-atmospheric | 暗色氛围 | 娱乐、游戏 | clean×dark×editorial×balanced |
| bold-editorial | 大胆编辑 | 产品发布、主题演讲 | clean×vibrant×editorial×balanced |
| pixel-art | 像素艺术 | 游戏、开发者 | pixel×vibrant×technical×balanced |
| scientific | 科学学术 | 医学、化学 | clean×cool×technical×dense |
| sketch-notes | 手绘笔记 | 教育、教程 | organic×warm×handwritten×balanced |
| watercolor | 水彩 | 生活、健康 | organic×warm×humanist×minimal |
| editorial-infographic | 编辑信息图 | 科技解说 | clean×cool×editorial×dense |
| fantasy-animation | 幻想动画 | 教育故事 | organic×vibrant×handwritten×minimal |
| vector-illustration | 矢量插画 | 创意、儿童 | clean×vibrant×humanist×balanced |
| vintage | 复古 | 历史、传记 | paper×warm×editorial×balanced |
| intuition-machine | 机器直觉 | 技术文档 | clean×cool×technical×dense |

## 参数

| 参数 | 说明 |
|------|------|
| markdown | Markdown文件路径（必填） |
| --style | 预设风格（默认 blueprint） |
| --slides | 最大页数（默认 20） |
| -r, --ratio | 宽高比（默认 16:9） |
| -o, --output | 输出目录（默认 slides/） |
| --outline-only | 仅输出大纲不生成图 |
| --list | 列出所有预设 |

## 工作流程

1. 读取Markdown文件
2. 按h2标题拆分为幻灯片页（自动生成标题页+结尾页）
3. 提取每页要点
4. 按预设风格逐页生成图片
5. 输出到指定目录
