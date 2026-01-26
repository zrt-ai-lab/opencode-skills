---
name: story-to-scenes
description: 长文本拆镜批量生图引擎。将故事、课程、连环画脚本智能拆分场景，批量生成风格统一、角色一致的配图。当用户提到「拆镜生图」「故事配图」「批量场景图」「连环画生成」「绘本生成」时使用此技能。
---

# Story To Scenes

长文本拆镜批量生图引擎，用于将故事、教学课程、连环画脚本等长文本智能拆分成场景，并批量生成风格统一、角色一致的配图。

## 核心流程

```
输入长文本 → 角色提取 → 生成角色胚子图 → 确认锁定
                              ↓
         智能拆镜 → 场景清单 → 确认调整
                              ↓
         风格胚子图（第一张场景）→ 确认锁定
                              ↓
         场景胚子图（复用场景，可选）→ 确认锁定
                              ↓
         批量生成场景图（引用胚子）→ 输出图集
```

## 铁律

1. **单图原则**：每个场景/角色生成独立单图，禁止多格拼接、分镜框、边框组合
2. **先人后景**：必须先生成并锁定角色胚子，再进行场景生图
3. **确认才锁定**：角色胚子、风格胚子必须用户确认后才算锁定
4. **引用生成**：场景中出现已锁定角色时，必须引用其胚子图
5. **提示词记录**：每张图的完整提示词必须记录，方便复用和微调
6. **进度持久化**：生成过程实时保存进度，支持断点续传

## 详细步骤

### Step 1: 项目初始化

收集项目基本信息：

```yaml
project_name: ""           # 项目名称（必填）
style_preset: ""           # 预设风格或自定义描述
aspect_ratio: "3:4"        # 尺寸：3:4 / 16:9 / 1:1
source_text: ""            # 原文内容或文件路径
```

创建项目目录：
```
assets/generated/{项目名}/
├── characters/            # 角色胚子图
├── locations/             # 场景胚子图
├── scenes/                # 场景配图
├── characters.md          # 角色索引
├── progress.json          # 生成进度
└── gallery.md             # 完整图集索引
```

### Step 2: 文本解析与角色提取

1. 自动识别文本类型：故事/课程/脚本/连环画
2. 按语义分割场景（非机械按段落切）
3. 提取所有人物/动物/生物，生成角色清单表

输出角色清单表格式：

| 角色名 | 类型 | 外貌特征 | 性格标签 | 出场场景 |
|--------|------|----------|----------|----------|
| 示例   | 人物/动物 | 详细外貌描述 | 性格关键词 | 1,2,3 |

**交互点**：展示清单，让用户补充/修正角色描述，确认后进入下一步。

### Step 3: 生成角色胚子图

为每个角色生成标准立绘：

- **构图要求**：正面或四分之三侧面，干净纯色背景
- **画面要求**：单图，突出角色本体特征，禁止多角度拼接
- **命名规范**：`{项目名}_char_{角色名}.png`
- **存储位置**：`assets/generated/{项目名}/characters/`

生图提示词结构：
```
[风格关键词], single character portrait of [角色描述], 
[姿态], clean solid [背景色] background, 
full body shot, character design sheet style,
--no multiple views, turnaround, collage, grid, panels, border
```

**交互点**：逐个展示角色胚子图，用户确认"OK"后锁定，不满意则重新生成。

将确认的角色信息写入 `characters.md`：
```markdown
# 角色索引

## {角色名}
- **胚子图**：characters/{角色名}.png
- **外貌描述**：{详细外貌}
- **出场场景**：{场景序号列表}
```

### Step 4: 智能拆镜

根据文本语义划分场景，生成场景清单表：

| 序号 | 场景名称 | 画面描述 | 出场角色 | 镜头类型 | 情绪氛围 |
|------|----------|----------|----------|----------|----------|
| 01   | 场景名   | 具体画面内容 | 角色列表 | 远景/中景/特写 | 情绪关键词 |

**镜头类型说明**：
- **远景**：交代环境，角色较小
- **中景**：角色半身或全身，主体突出
- **特写**：面部表情或关键物品细节

**交互点**：展示拆镜表，让用户调整场景划分、镜头选择，确认后进入下一步。

### Step 5: 生成风格胚子图

用第一个场景生成**风格定调图**：

1. 根据用户选择的风格预设（或自定义描述）构建提示词
2. 生成第一张场景图
3. 展示给用户确认

**交互点**：
- 确认OK → 提取风格关键词，记录到 `progress.json`，全程复用
- 不满意 → 调整风格描述，重新生成

### Step 6: 场景胚子图（可选）

识别文本中**反复出现的重要场景**，如：
- 主角的家
- 重要地标建筑
- 反复出现的场所

为这些场景单独生成环境图：
- **构图要求**：无人物，纯场景环境
- **存储位置**：`assets/generated/{项目名}/locations/`
- **命名规范**：`{场景名}.png`

**交互点**：展示场景胚子图，确认或跳过。

### Step 7: 批量生成场景图

逐场景生成配图，采用**图生图**方式保证角色一致性。

#### 单角色场景

直接基于该角色胚子图做图生图：
```bash
python image_to_image.py "characters/角色A.png" "场景描述，保持角色形象..." -o "scenes/scene_xx.png"
```

#### 多角色场景（串行替换规则）

当场景包含多个角色时，必须**串行轮流替换**，逐步锁定每个角色：

```
步骤1：基于角色A胚子图 + 场景描述 → 生成 role1.png（角色A锁定，其他角色可能不一致）
步骤2：基于角色B胚子图 + role1.png → 生成 role2.png（角色A+B锁定）
步骤3：基于角色C胚子图 + role2.png → 生成 role3.png（角色A+B+C锁定）
...依此类推，直到所有角色都替换完成
最终输出：role{n}.png 作为该场景的最终图
```

**执行示例**（3角色场景）：
```bash
# 第1轮：锁定孙悟空
python image_to_image.py "characters/孙悟空.png" "场景描述，孙悟空xxx，唐僧xxx，猪八戒xxx..." -o "scenes/scene_xx_role1.png"

# 第2轮：基于role1锁定唐僧
python image_to_image.py "characters/唐僧.png" "保持场景和其他角色，替换唐僧形象与参考图一致" --ref "scenes/scene_xx_role1.png" -o "scenes/scene_xx_role2.png"

# 第3轮：基于role2锁定猪八戒
python image_to_image.py "characters/猪八戒.png" "保持场景和其他角色，替换猪八戒形象与参考图一致" --ref "scenes/scene_xx_role2.png" -o "scenes/scene_xx_role3.png"

# 最终重命名
mv "scenes/scene_xx_role3.png" "scenes/scene_xx_场景名.png"
# 清理中间文件
rm "scenes/scene_xx_role1.png" "scenes/scene_xx_role2.png"
```

**角色替换顺序**：按重要性或画面占比从大到小排序

#### 提示词规范

提示词结构：
```
[风格关键词], [场景描述], 
[角色A描述], [角色B描述],
[镜头构图], [情绪氛围],
--no multiple panels, comic layout, grid, collage, split frame, border, manga panels, text, caption, title, subtitle, watermark, signature, letters, words, writing
```

**铁律**：
- 禁止输出任何文字、标题、水印、签名
- 排除词必须包含 `text, caption, title, subtitle, watermark, signature, letters, words, writing`

**命名规范**：`scene_{序号}_{场景名}.png`
**存储位置**：`assets/generated/{项目名}/scenes/`

**进度追踪**：
- 每生成一张，更新 `progress.json`
- 失败自动重试（最多3次）

### Step 8: 输出整理

生成完成后，创建图集索引文档 `gallery.md`：

```markdown
# {项目名} 场景图集

## 项目信息
- **风格**：{风格描述}
- **尺寸**：{尺寸}
- **场景数**：{总数}
- **生成日期**：{日期}

## 角色一览
| 角色 | 胚子图 |
|------|--------|
| {角色名} | ![[characters/{角色名}.png]] |

## 场景图集

### Scene 01：{场景名}
![[scenes/scene_01_{场景名}.png]]
> {场景描述}

<details>
<summary>提示词</summary>
{完整提示词}
</details>
```

## 特殊操作命令

| 命令 | 说明 |
|------|------|
| `重新生成 {角色名}` | 重新生成指定角色胚子图 |
| `重新生成 scene_{序号}` | 重新生成指定场景图 |
| `从 scene_{序号} 继续` | 断点续传，从指定场景继续 |
| `更换风格` | 重新选择风格，需重新生成风格胚子 |
| `导出图集` | 生成最终索引文档 |

## 预设风格

可选择以下预设风格，或提供自定义风格描述：

### 日系治愈绘本
```
soft watercolor illustration, warm pastel colors, gentle lighting, 
Studio Ghibli inspired, dreamy atmosphere, delicate linework
```

### 国风水墨淡彩
```
traditional Chinese ink wash painting, subtle watercolor tints,
elegant brushwork, Song dynasty aesthetic, zen atmosphere
```

### 欧美儿童插画
```
vibrant children's book illustration, bold colors, expressive characters,
playful style, Pixar-inspired, warm and inviting
```

### 赛博朋克
```
cyberpunk aesthetic, neon lights, dark atmosphere, 
high contrast, futuristic cityscape, Blade Runner inspired
```

### 扁平矢量风
```
flat vector illustration, clean geometric shapes, 
modern minimalist, limited color palette, graphic design style
```

### 水彩手绘风
```
traditional watercolor painting, visible brush strokes,
organic textures, artistic imperfections, soft edges
```

## 文件结构

生成项目的完整目录结构：

```
assets/generated/{项目名}/
├── characters/              # 角色胚子图
│   ├── {角色A}.png
│   └── {角色B}.png
├── locations/               # 场景胚子图（可选）
│   └── {场景名}.png
├── scenes/                  # 场景配图
│   ├── scene_01_{场景名}.png
│   ├── scene_02_{场景名}.png
│   └── ...
├── characters.md            # 角色索引表
├── progress.json            # 生成进度
└── gallery.md               # 完整图集索引
```

## 依赖技能

- `image-service`：实际生图执行
- `obsidian-markdown`：生成索引文档（可选）

## References

- `references/prompt_templates.md`：提示词模板库
- `references/style_presets.md`：风格预设详情

## Assets

- `assets/templates/gallery_template.md`：图集索引模板
- `assets/templates/characters_template.md`：角色索引模板
