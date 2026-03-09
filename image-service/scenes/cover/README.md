# 封面图场景

## 概述

五维定制系统：**类型(6) × 配色(9) × 渲染(6) × 文字(4) × 氛围(3) = 3888种组合**

专为文章、公众号、博客封面设计。

## 快速使用

```bash
# 只需标题，其他自动选择
python scenes/cover/zlab_cover.py -n "AI Agent的前世今生"

# 深色科技风
python scenes/cover/zlab_cover.py -n "深入AI Agent" --type conceptual --palette dark --rendering digital

# 极简风
python scenes/cover/zlab_cover.py -n "极简主义" --type minimal --palette mono --mood subtle
```

## 五维参数

### 类型 (--type)
| 值 | 名称 | 说明 |
|---|------|------|
| hero | 主视觉 | 大气居中，视觉冲击（默认） |
| conceptual | 概念隐喻 | 视觉符号表达抽象主题 |
| typography | 文字排版 | 以字体设计为主 |
| metaphor | 视觉比喻 | 具象物体比喻抽象概念 |
| scene | 场景氛围 | 环境渲染，沉浸感 |
| minimal | 极简留白 | 大面积留白，高级感 |

### 配色 (--palette)
| 值 | 名称 | 说明 |
|---|------|------|
| warm | 暖色调 | 橙红金黄 |
| elegant | 优雅 | 低饱和，灰粉米白 |
| cool | 冷色调 | 蓝绿青灰（默认） |
| dark | 深色 | 深蓝黑灰，高端 |
| earth | 大地色 | 棕褐橄榄 |
| vivid | 鲜艳 | 高饱和撞色 |
| pastel | 粉彩 | 马卡龙色 |
| mono | 单色 | 同色相深浅 |
| retro | 复古 | 怀旧暖黄 |

### 渲染 (--rendering)
| 值 | 名称 | 说明 |
|---|------|------|
| flat-vector | 扁平矢量 | 纯色块，简洁线条（默认） |
| hand-drawn | 手绘 | 手工线条感 |
| painterly | 绘画 | 油画笔触 |
| digital | 数字渲染 | 3D光影 |
| pixel | 像素 | 8-bit复古 |
| chalk | 粉笔 | 黑板粉笔 |

### 文字 (--text)
| 值 | 名称 | 说明 |
|---|------|------|
| none | 无文字 | 纯视觉 |
| title-only | 仅标题 | 含主标题（默认） |
| title-subtitle | 标题+副标题 | 主副标题 |
| text-rich | 文字丰富 | 标题+要点 |

### 氛围 (--mood)
| 值 | 名称 | 说明 |
|---|------|------|
| subtle | 含蓄 | 克制，留白多 |
| balanced | 均衡 | 不张扬不克制（默认） |
| bold | 大胆 | 强烈视觉冲击 |
