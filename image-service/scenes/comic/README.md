# 漫画场景

## 概述

知识漫画生成器，**5画风 × 7基调 × 6布局 = 210种组合**。逐页串行生成，参考上一页保持角色和风格一致。

## 快速使用

```bash
# 日漫风温暖基调
python scenes/comic/zlab_comic.py story.md --art manga --tone warm -o comic/

# 水墨动作风
python scenes/comic/zlab_comic.py story.md --art ink-brush --tone action --layout cinematic -o comic/

# 查看所有选项
python scenes/comic/zlab_comic.py --list
```

## 画风（5种）

| 画风 | 名称 | 描述 |
|------|------|------|
| ligne-claire | 清线 | 统一线条、平涂色彩，欧洲漫画（默认） |
| manga | 日漫 | 大眼睛、表情丰富、速度线 |
| realistic | 写实 | 数字绘画、精致渲染 |
| ink-brush | 水墨 | 中国水墨、笔触晕染 |
| chalk | 粉笔 | 黑板粉笔、温暖童趣 |

## 基调（7种）

| 基调 | 名称 | 描述 |
|------|------|------|
| neutral | 中性 | 平衡理性（默认） |
| warm | 温暖 | 怀旧温馨 |
| dramatic | 戏剧 | 高对比紧张 |
| romantic | 浪漫 | 柔和唯美 |
| energetic | 活力 | 明亮动感 |
| vintage | 复古 | 历史做旧 |
| action | 动作 | 速度线战斗 |

## 布局（6种）

| 布局 | 名称 | 每页格数 | 适用 |
|------|------|---------|------|
| standard | 标准 | 4-6格 | 叙事推进（默认） |
| cinematic | 电影 | 2-4格 | 戏剧时刻 |
| dense | 密集 | 6-9格 | 技术说明 |
| splash | 跨页 | 1-2大图 | 关键揭示 |
| mixed | 混合 | 3-7不等 | 复杂叙事 |
| webtoon | 条漫 | 3-5竖向 | 手机阅读 |

## 参数

| 参数 | 说明 |
|------|------|
| source | 素材Markdown文件（必填） |
| --art | 画风（默认 ligne-claire） |
| --tone | 基调（默认 neutral） |
| --layout | 布局（默认 standard） |
| -r, --ratio | 宽高比（默认 3:4竖版） |
| -o, --output | 输出目录（默认 comic/） |
| --pages | 最大页数（默认 12） |
| --list | 列出所有选项 |

## 生成逻辑

- 首页用 `text_to_image.py` 定调
- 后续页用 `image_to_image.py` 参考上一页，保持角色和风格一致
- 串行生成，不并发
