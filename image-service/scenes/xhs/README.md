# 小红书图场景

## 概述

小红书信息图系列生成器，将内容拆解为1-10张卡片。**9风格 × 6布局 = 54种组合**。串行生成保持系列风格一致。

## 快速使用

```bash
# 可爱风 + 均衡布局
python scenes/xhs/zlab_xhs_images.py article.md --style cute --layout balanced -o xhs/

# Notion风 + 密集布局
python scenes/xhs/zlab_xhs_images.py article.md --style notion --layout dense -o xhs/

# 查看选项
python scenes/xhs/zlab_xhs_images.py --list
```

## 风格（9种）

| 风格 | 名称 | 描述 |
|------|------|------|
| cute | 可爱卡通 | 圆润造型、粉黄配色（默认） |
| fresh | 清新自然 | 薄荷绿、天蓝、植物装饰 |
| warm | 温暖治愈 | 暖黄暖橙、毛绒质感 |
| bold | 大胆撞色 | 荧光色、强对比 |
| minimal | 极简 | 黑白灰、大留白 |
| retro | 复古 | 做旧、泛黄胶片 |
| pop | 波普 | 漫画网点、鲜艳原色 |
| notion | Notion风 | 白底、线条图标 |
| chalkboard | 粉笔黑板 | 深绿黑板、粉笔手绘 |

## 布局（6种）

| 布局 | 名称 | 密度 | 适用 |
|------|------|------|------|
| sparse | 稀疏 | 1-2点 | 封面、金句 |
| balanced | 均衡 | 3-4点 | 常规内容（默认） |
| dense | 密集 | 5-8点 | 干货总结 |
| list | 列表 | 4-7项 | 清单、排行 |
| comparison | 对比 | 双栏 | 对比、优劣 |
| flow | 流程 | 3-6步 | 教程、流程 |

## 参数

| 参数 | 说明 |
|------|------|
| source | 内容文件路径（必填） |
| --style | 风格（默认 cute） |
| --layout | 布局（默认 balanced） |
| -o, --output | 输出目录（默认 xhs/） |
| --cards | 最大卡片数（默认 10） |
| --list | 列出所有选项 |

## 生成逻辑

- 自动拆分内容为多张卡片（封面+内容）
- 首张用 `text_to_image.py` 定调
- 后续用 `image_to_image.py` 参考上一张，保持系列一致
- 默认比例 3:4 竖版
