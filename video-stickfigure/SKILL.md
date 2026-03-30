---
name: video-stickfigure
description: 火柴人图片生成技能。使用AI生成粉笔画风格火柴人，并用HSV统一背景色。当需要生成火柴人视频素材时触发。
---

# 火柴人生图技能

## 🚨 核心原则

> **必须使用AI生图！禁止用PIL画线条！**
> 
> 检查标准：生成的图片文件 > 50KB

---

## 🔧 生图工具

**使用 image-service skill：**

```bash
python ~/.openclaw/skills/image-service/scripts/text_to_image.py "[prompt]" -r 9:16 -o stick1.png
```

---

## 📝 Prompt模板

### 深墨绿背景版（推荐·默认）

```
minimalist chalk-style stick figure on dark green chalkboard background #3c5b45,
white chalk line art, simple 5-stroke drawing style,
[动作描述],
exaggerated pose, hand-drawn feel, chalk texture,
no shading, no gradient, stark contrast,
vertical composition 9:16, no text, no watermark
```

### 纯黑背景版（备选）

```
minimalist stick figure, pure black background #000000,
white line art only, simple 5-stroke drawing,
[动作描述],
exaggerated pose, no shading, no gradient, no gray,
stark contrast, cartoon style,
vertical composition 9:16, no text, no watermark
```

**选择建议：**
- 深墨绿版：有黑板质感，视觉更柔和 ✅ 推荐
- 纯黑版：对比度更高，更简洁

### 动作描述 + 氛围元素（必须包含！）

> **火柴人不能孤零零的！必须加氛围元素来衬托情绪！**

| 情绪/概念 | 人物动作 | 🌟 氛围元素（必加！） |
|-----------|----------|----------------------|
| 衰老/疲惫 | person slumped over, tired posture | + withered leaves falling, dim shadows, cracked ground |
| 枯萎/消沉 | person wilting like a dying plant | + dead tree nearby, falling petals, dark clouds |
| 向上/成长 | person climbing stairs upward | + sunlight rays from above, distant mountain peak, stars |
| 扛事/承担 | person lifting heavy weight overhead | + storm clouds, rain drops, lightning in background |
| 看远/远眺 | person standing on cliff, hand over eyes | + vast horizon, clouds below feet, sunrise glow |
| 容人/包容 | person with arms wide open | + small figures approaching, warm light rays, hearts floating |
| 愉悦/快乐 | person jumping with joy, arms raised | + confetti, sparkles, fireworks in sky |
| 成长/蜕变 | person breaking out of shell | + butterfly wings emerging, light beams, blooming flowers |
| 思考/沉思 | person sitting cross-legged, hand on chin | + floating question marks, gears, light bulb above head |
| 行动/奔跑 | person running forward with determination | + motion lines, wind effect, path stretching ahead |

### Prompt组装公式

```
[基础模板] + [人物动作] + [氛围元素] + [后缀]
```

**示例：衰老场景**
```
minimalist chalk-style stick figure on dark green chalkboard background #3c5b45,
white chalk line art, simple 5-stroke drawing style,
person slumped over tired posture aging feeling,
withered leaves falling around, dim shadows, cracked ground beneath,
exaggerated pose, hand-drawn feel, chalk texture,
no shading, no gradient, stark contrast,
vertical composition 9:16, no text, no watermark
```

**示例：爬台阶场景**
```
minimalist chalk-style stick figure on dark green chalkboard background #3c5b45,
white chalk line art, simple 5-stroke drawing style,
person climbing stairs upward with determination,
sunlight rays streaming from above, distant mountain peak visible, glowing stars,
exaggerated pose, hand-drawn feel, chalk texture,
no shading, no gradient, stark contrast,
vertical composition 9:16, no text, no watermark
```

### ⚠️ 氛围元素规则

1. **必须添加** - 不加氛围元素的火柴人图太单调
2. **与情绪匹配** - 消极情绪用暗元素，积极情绪用亮元素
3. **不要太多** - 2-3个氛围元素足够，太多会杂乱
4. **保持简约** - 氛围元素也是粉笔画风格，不要写实

---

## 🎨 HSV背景统一处理（必做！）

> **AI无法精确控制颜色！生图后必须用代码统一背景色！**

### 处理脚本

```python
import cv2
import numpy as np

def unify_background_hsv(input_path, output_path, target_hex="#3c5b45"):
    """
    用HSV范围替换统一背景色
    """
    img = cv2.imread(input_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 绿色系HSV范围（覆盖AI生成的各种绿色）
    lower = np.array([35, 20, 20])
    upper = np.array([85, 255, 255])
    
    # 创建掩码
    mask = cv2.inRange(hsv, lower, upper)
    
    # 目标颜色 BGR
    target_bgr = tuple(int(target_hex.lstrip('#')[i:i+2], 16) for i in (4, 2, 0))
    
    # 替换背景
    result = img.copy()
    result[mask > 0] = target_bgr
    
    cv2.imwrite(output_path, result)
    return output_path

# 批量处理
import glob
for f in glob.glob("stick*.png"):
    if "_unified" not in f:
        out = f.replace(".png", "_unified.png")
        unify_background_hsv(f, out)
        print(f"处理完成: {out}")
```

### 命令行版本

```bash
python3 << 'EOF'
import cv2
import numpy as np
import glob
import sys

target_hex = "#3c5b45"
target_bgr = tuple(int(target_hex.lstrip('#')[i:i+2], 16) for i in (4, 2, 0))

for f in glob.glob("stick*.png"):
    if "_unified" in f:
        continue
    img = cv2.imread(f)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([35,20,20]), np.array([85,255,255]))
    result = img.copy()
    result[mask > 0] = target_bgr
    out = f.replace(".png", "_unified.png")
    cv2.imwrite(out, result)
    print(f"✅ {f} -> {out}")
EOF
```

---

## ✅ 检查清单（必须全部通过！）

在交付图片前，必须确认：

| 检查项 | 标准 | 不通过则 |
|--------|------|----------|
| 文件大小 | 每张 > 50KB | 重新AI生图 |
| 图片数量 | 与场景数量一致 | 补充生成 |
| 背景颜色 | 统一为 #3c5b45 | 执行HSV处理 |
| 火柴人可见 | 白色线条清晰 | 重新生成 |

```bash
# 快速检查文件大小
ls -la stick*_unified.png | awk '{if($5<50000) print "❌ "$9" 太小: "$5"B"; else print "✅ "$9": "$5"B"}'
```

---

## 📁 输出规范

| 文件 | 说明 |
|------|------|
| stick1.png, stick2.png, ... | AI生成的原始图片 |
| stick1_unified.png, ... | HSV处理后的统一背景图片 |

**后续流程只使用 `*_unified.png` 文件！**

---

## 🚫 常见错误

| 错误 | 后果 | 正确做法 |
|------|------|----------|
| 用PIL画线条 | 视频看起来像测试图 | 用image-service AI生图 |
| 跳过HSV处理 | 背景色深浅不一 | 必须执行HSV统一 |
| 文件<50KB | 图片质量差 | 重新生成 |
| 用原图不用unified | 背景不统一 | 只用_unified.png |
| **火柴人没有氛围元素** | 画面单调无感染力 | prompt必须加氛围元素 |
