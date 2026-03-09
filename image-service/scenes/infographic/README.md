# 信息图场景

## 概述

20种布局 × 17种风格 = **340种组合**，覆盖几乎所有信息可视化场景。

## 快速使用

```bash
# 金字塔 + 手绘风
python scenes/infographic/zlab_infographic.py -l pyramid -s craft-handmade -n "标题" -c "内容描述" -o output.png

# 查看所有组合
python scenes/infographic/zlab_infographic.py --list
```

## 布局速查（20种）

| 布局 | 名称 | 适用场景 |
|------|------|---------|
| pyramid | 金字塔 | 层级关系、优先级 |
| funnel | 漏斗图 | 转化漏斗、筛选 |
| fishbone | 鱼骨图 | 根因分析 |
| venn | 韦恩图 | 概念交集 |
| timeline | 时间线 | 历史、项目进度 |
| mind-map | 思维导图 | 知识梳理、头脑风暴 |
| circular-flow | 循环流程 | 迭代、生命周期 |
| comparison | 对比图 | 方案比较、优劣分析 |
| grid-cards | 卡片网格 | 多主题概览 |
| layers-stack | 分层堆叠 | 技术栈、架构层 |
| iceberg | 冰山图 | 表象vs本质 |
| bridge | 桥接图 | 问题→方案 |
| tree-hierarchy | 树状层级 | 组织架构、分类 |
| nested-circles | 嵌套圆 | 影响范围、圈层 |
| quadrants | 四象限 | 优先级矩阵、SWOT |
| scale-balance | 天平图 | 利弊权衡 |
| journey-path | 旅程路径 | 用户旅程、成长路径 |
| flow | 流程图 | 工作流、决策流程 |
| feature-list | 功能列表 | 产品功能、要点 |
| equation | 公式图 | 公式分解、组合 |

## 风格速查（17种）

| 风格 | 名称 | 描述 |
|------|------|------|
| craft-handmade | 手绘插画 | 手绘线条、纸艺质感（默认） |
| claymation | 黏土动画 | 3D黏土、定格动画感 |
| kawaii | 可爱日系 | 大眼Q版、粉彩色 |
| watercolor | 水彩绘本 | 柔和晕染、童话感 |
| chalkboard | 粉笔黑板 | 彩色粉笔、黑板质感 |
| cyberpunk | 赛博朋克 | 霓虹灯光、暗色未来 |
| bold-graphic | 漫画波普 | 粗线条、网点、高对比 |
| aged-academia | 复古学术 | 泛黄素描、手稿感 |
| corporate | 商务扁平 | 矢量人物、鲜艳填充 |
| technical | 技术蓝图 | 蓝图线条、工程图 |
| origami | 折纸 | 几何折面、纸张质感 |
| pixel-art | 像素复古 | 8-bit、怀旧游戏 |
| wireframe | 线框原型 | 灰度、UI原型 |
| subway-map | 地铁线路 | 彩色线路站点图 |
| ikea-manual | 说明书 | 极简线条、步骤图示 |
| knolling | 整齐平铺 | 俯拍、整齐排列 |
| lego | 乐高积木 | 积木拼搭、童趣 |

## 参数

| 参数 | 说明 |
|------|------|
| -l, --layout | 布局类型（必填） |
| -s, --style | 视觉风格（默认 craft-handmade） |
| -n, --name | 标题（必填） |
| -c, --content | 内容描述（必填） |
| -r, --ratio | 宽高比（默认 16:9） |
| -o, --output | 输出路径（必填） |
| --list | 列出所有布局和风格 |
