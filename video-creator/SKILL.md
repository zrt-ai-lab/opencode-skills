---
name: video-creator
description: 视频创作技能。图片+音频合成视频，支持TTS配音、淡入淡出转场、字幕、片尾、BGM。当用户提到「生成视频」「做视频」「教学视频」「图文转视频」「做视频号」「配音视频」「图文结合视频」「古诗视频」「故事视频」时触发。内含生图→配音→合成全流程，无需单独调用image-service。
---

# Video Creator

图片+音频合成视频工具。

---

## ⛔⛔⛔ 最高铁律：音画同步（违反即废片重做！）

**每次生成视频，duration 必须从 narration.json 时间戳精确计算，绝对禁止凭感觉手动填！**

### 强制流程（缺一步都不行）

```
1. TTS 生成配音 → 得到 narration.mp3 + narration.json（时间戳）
2. 读取 narration.json，逐句分析内容语义
3. 确定每张图对应哪些句子（按内容语义匹配，不是平均分！）
4. 每张图的 duration = 对应最后一句的 end - 对应第一句的 start
5. 校验：所有 duration 之和 ≈ 音频总时长（误差 < 1s）
6. ⛔ 运行 verify_alignment.py 校验（必须通过才能合成！）
7. 校验通过才能写 video_config.yaml，否则停止！
```

### 示例（以古诗教学为例）

```
narration.json 时间戳：
  句0 [0.1-2.6]  "静夜思，唐，李白。"
  句1 [2.6-5.7]  "床前明月光，疑是地上霜。"
  句2 [5.7-8.6]  "举头望明月，低头思故乡。"
  句3 [8.6-16.4] "这首诗是唐代大诗人李白..."
  句4 [16.4-20.9] "短短二十个字..."
  句5 [20.9-22.6] "床前明月光。"
  ...

图片分配：
  01_title.png    → 句0-2（全诗朗诵）→ duration = 8.6 - 0.1 = 8.5s
  02_poet.png     → 句3-4（诗人介绍）→ duration = 20.9 - 8.6 = 12.3s
  03_moonlight.png → 句5-8（第一句解读）→ duration = 38.6 - 20.9 = 17.7s
  ...

校验：8.5 + 12.3 + 17.7 + ... = 114.4s ≈ 音频 114.5s ✅
```

### 禁止行为

- ❌ 凭感觉给每张图分配 10s、15s、20s
- ❌ 平均分配（总时长 / 图片数）
- ❌ 不读 narration.json 就写 duration
- ❌ 图片总时长和音频差 5 秒以上还强行合成
- ❌ 让 video_maker.py 自动拉伸超过 1 秒
- ❌ duration: auto（已从代码中彻底删除！）

---

## 生图铁律（违反即重做）

### 0. 默认尺寸（最重要！）

**默认比例：16:9（1920×1080 横版）**

除非以下情况，否则一律用 16:9：
- 用户明确指定其他比例
- 与其他流程协同时，其他流程有明确要求（如小红书要 3:4，抖音要 9:16）

```bash
# ✅ 默认：不指定 -r 参数，或明确写 -r 16:9
python text_to_image.py "提示词" -o output.png
python text_to_image.py "提示词" -r 16:9 -o output.png

# ❌ 禁止：随意切换比例，一会儿竖版一会儿横版
# 同一个视频项目，所有图片必须是同一比例！
```

### 1. 图片密度要求

| 视频时长 | 最少图片数 | 每张图时长 |
|----------|-----------|-----------|
| 30秒 | 8张 | 3-4秒 |
| 60秒 | 15张 | 3-5秒 |
| 90秒 | 22张 | 3-5秒 |
| 120秒 | 30张 | 3-5秒 |

**铁律：每张图最长 7 秒，超过必须拆分！**

计算公式：`图片数量 = ceil(音频时长 / 4)`

### 2. 生图提示词语言要求

**所有生图 prompt 必须用中文写！禁止英文 prompt！**

```bash
# ❌ 错误：用英文写 prompt
python text_to_image.py "modern tech illustration, AI robot, blue gradient background"

# ❌ 错误：英文 prompt 里夹中文
python text_to_image.py "tech style, Chinese text '对决', blue theme"

# ✅ 正确：纯中文 prompt
python text_to_image.py "现代科技插画风格，可爱AI机器人坐在电脑前，蓝紫色渐变背景，霓虹灯光效，多个悬浮的全息UI面板，信息密度高，专业信息图风格"
```

**铁律**：
- prompt 必须是纯中文
- 生成的图片里如果有文字，也必须是中文
- 禁止任何英文出现

### 3. 信息密度要求

**信息密度 = 文字要点多 + 视觉元素丰富**

**文字内容要丰富**：
```
# ❌ 错误：文字太少
图片里只写 "AI对比"

# ✅ 正确：文字要点多
图片里包含：
- 标题：QoderWork vs OpenClaw
- 副标题：桌面AI助手对比
- 要点1：开箱即用 vs 自由定制
- 要点2：$19/月 vs 免费开源
- 要点3：普通用户 vs 技术极客
```

**视觉元素要丰富**：
```
# ❌ 错误：太空洞
只有文字，没有图标、图表、装饰

# ✅ 正确：可视化丰富
- 配合图标（对勾、叉、箭头、星星）
- 配合图表（柱状图、饼图、对比条）
- 配合插画（机器人、电脑、用户形象）
- 配合装饰（光效、渐变、边框）
```

**信息密度原则**：
- 每张图要有明确的文字标题和要点
- 文字内容要和配音内容对应
- 更重要的是**可视化**：图标、图表、插画、装饰
- 禁止纯文字图，也禁止纯装饰图

### 4. 生图描述要细致具体

**每张图必须有丰富、具体的视觉元素，禁止笼统空洞！**

```bash
# ❌ 错误：太笼统
"一个机器人"
"科技风格的图"
"对比图"

# ✅ 正确：细致具体
"可爱的蓝色AI机器人吉祥物，圆润金属质感，坐在现代简约办公桌前，
桌上有27寸曲面显示器显示代码，旁边放着咖啡杯和多肉植物，
机器人头顶悬浮三个全息面板分别显示折线图、饼图、进度条，
深蓝色科技感背景，地面有蓝色光带，整体赛博朋克风格，柔和的体积光"
```

**prompt 必备 6 要素**（缺一不可）：

| 要素 | 说明 | 示例 |
|------|------|------|
| 主体 | 谁/什么东西，要具体 | "蓝色圆润金属质感的AI机器人" 而非 "机器人" |
| 动作 | 在做什么，姿态如何 | "双手放在键盘上打字，微微侧头" |
| 环境 | 在哪里，背景是什么 | "现代简约办公室，落地窗外是城市夜景" |
| 细节 | 周围有什么物品/元素 | "桌上有咖啡杯、多肉植物、便签纸" |
| 风格 | 什么画风/光效 | "赛博朋克风格，霓虹灯光，体积光效果" |
| 色彩 | 主色调是什么 | "蓝紫渐变主色调，橙色点缀" |

### 5. 视觉风格一致性

同一个视频的所有图片必须保持风格统一：
- 使用相同的风格前缀
- 使用相同的色彩基调
- 使用相同的比例（禁止混用横竖版！）

```bash
# 定义统一风格前缀（中文！）
STYLE="现代科技插画风格，干净矢量设计，蓝紫渐变配色，专业信息图美感，高信息密度，霓虹发光效果，深色背景"

# 所有图片都用这个前缀 + 相同比例
python text_to_image.py "$STYLE，[具体场景内容]" -r 16:9 -o scene01.png
python text_to_image.py "$STYLE，[具体场景内容]" -r 16:9 -o scene02.png
```

### 6. 比例选择指南

| 场景 | 比例 | 说明 |
|------|------|------|
| **默认/通用** | 16:9 | B站、YouTube、公众号视频、PPT配图 |
| 抖音/视频号/快手 | 9:16 | 竖屏短视频平台，需用户指定或流程要求 |
| 小红书 | 3:4 | 小红书笔记配图，需用户指定或流程要求 |
| 朋友圈 | 1:1 | 正方形，需用户指定 |

**铁律**：不确定用什么比例时，一律用 16:9

---

## 核心流程（铁律）

### 故事类视频生成流程（套娃流程）

当用户提供故事/剧情/剧本时，**必须严格按以下套娃流程执行**：

```
┌─────────────────────────────────────────────────────────────┐
│ 第一层：故事 → 拆分场景 → 并发生成场景主图（文生图）            │
│                                                              │
│   大闹天宫 →  场景1：弼马温受辱                                │
│              场景2：筋斗云回花果山                             │
│              场景3：玉帝派兵                                   │
│              ...                                              │
│              → 并发调用 text_to_image.py 生成每个场景主图      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 第二层：每个场景主图 → 图生图拆出细镜头（保持角色一致）         │
│                                                              │
│   场景1主图 → 细镜头1：悟空看官印疑惑                          │
│              细镜头2：悟空踢翻马槽                             │
│   场景2主图 → 细镜头1：踏筋斗云腾空                            │
│              细镜头2：花果山自封大圣                           │
│              → 并发调用 image_to_image.py，以主图为参考        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ 第三层：生成配音 + 字幕 + 校验 + 合成视频                      │
│                                                              │
│   1. tts_generator.py 生成配音 + 时间戳                       │
│   2. 【铁律】根据时间戳精确计算每张图的duration                │
│   3. 生成 SRT 字幕                                            │
│   4. 生成 video_config.yaml                                   │
│   5. ⛔ verify_alignment.py 校验（必须通过！）                │
│   6. video_maker.py 合成：                                    │
│      → 图片合成（带转场）                                      │
│      → 合并音频                                               │
│      → 烧录字幕（ASS格式，底部居中固定）                       │
│      → 自动拼接片尾（二维码+"点关注不迷路"）                   │
│      → 添加BGM                                                │
└─────────────────────────────────────────────────────────────┘

**铁律：所有视频必须自动拼接片尾！**
```

### 目录结构规范

```
assets/generated/{project_name}/
├── scene1/
│   ├── main.png         # 场景1主图（文生图）
│   ├── shot_01.png      # 细镜头1（图生图）
│   └── shot_02.png      # 细镜头2（图生图）
├── scene2/
│   ├── main.png
│   ├── shot_01.png
│   └── shot_02.png
├── ...
├── narration.mp3        # 配音
├── narration.json       # 时间戳
├── subtitles.srt        # 字幕
├── video_config.yaml    # 视频配置
└── {project_name}.mp4   # 最终视频
```

### 执行命令示例

```bash
# 第一层：并发生成场景主图（默认 16:9）
python .opencode/skills/image-service/scripts/text_to_image.py "风格描述，场景1内容" -r 16:9 -o scene1/main.png &
python .opencode/skills/image-service/scripts/text_to_image.py "风格描述，场景2内容" -r 16:9 -o scene2/main.png &
wait

# 第二层：并发图生图生成细镜头（保持相同比例）
python .opencode/skills/image-service/scripts/image_to_image.py scene1/main.png "保持角色风格，细镜头描述" -r 16:9 -o scene1/shot_01.png &
python .opencode/skills/image-service/scripts/image_to_image.py scene1/main.png "保持角色风格，细镜头描述" -r 16:9 -o scene1/shot_02.png &
wait

# 第三层：生成配音+校验+合成视频
python .opencode/skills/video-creator/scripts/tts_generator.py --text "完整旁白" --output narration.mp3 --timestamps

# ⛔ 强制校验（必须通过才能合成！）
python .opencode/skills/video-creator/scripts/verify_alignment.py video_config.yaml

# 校验通过后才能合成
python .opencode/skills/video-creator/scripts/video_maker.py video_config.yaml --srt subtitles.srt --bgm epic
```

---

## 视频配置文件格式

```yaml
# video_config.yaml
ratio: "16:9"           # 默认横版！必须加引号避免YAML解析错误
bgm_volume: 0.12
outro: true

scenes:
  - audio: narration.mp3
    images:
      # 按场景顺序排列所有细镜头
      - file: scene1/shot_01.png
        duration: 4.34
      - file: scene1/shot_02.png
        duration: 4.88
      - file: scene2/shot_01.png
        duration: 2.15
      # ...
```

**注意**：`ratio` 必须用引号包裹，如 `"16:9"`，否则 YAML 会解析成时间格式。

---

## 时长分配规范（铁律！）

**生成 video_config.yaml 前，必须严格按以下流程计算 duration：**

### 步骤1：读取时间戳文件

```python
import json
with open("narration.json", "r") as f:
    timestamps = json.load(f)
audio_duration = timestamps[-1]["end"]
print(f"音频总时长: {audio_duration:.1f}s")
```

### 步骤2：按内容语义划分场景

根据解说词内容，确定每张图对应的时间段：

```python
# 示例：根据解说词内容划分
# 找到每个主题切换点的时间戳
scenes = [
    ("cover.png", 0, 12.5),      # 开场到第一个主题切换
    ("scene01.png", 12.5, 26),   # 第二段内容
    # ...根据 narration.json 中的句子边界精确划分
]
```

### 步骤3：计算每张图的 duration

```python
for file, start, end in scenes:
    duration = end - start
    print(f"{file}: {duration:.1f}s")
```

### 步骤4：校验总时长

```python
total_duration = sum(duration for _, _, duration in scenes)
assert abs(total_duration - audio_duration) < 1.0, \
    f"时长不匹配！图片总时长{total_duration}s vs 音频{audio_duration}s"
```

### 铁律

1. **必须先读取 narration.json 时间戳**，不能凭感觉估算
2. **按句子语义边界划分**，不能平均分配
3. **生成配置前必须校验**，确保图片总时长 = 音频总时长（误差<0.5秒）
4. **禁止让脚本自动拉伸**，音画不同步的视频不合格
5. **禁止 duration=0**，每张图最少 1 秒
6. **生成 yaml 后必须用 verify_alignment.py 校验再合成**

### 校验脚本（强制执行！合成前必须通过！）

```bash
# ⛔ 合成视频前必须先运行校验脚本，不通过禁止合成！
python .opencode/skills/video-creator/scripts/verify_alignment.py video_config.yaml

# 校验内容：
# 1. 所有图片文件是否存在
# 2. duration 是否为精确数值（非数字直接拒绝！）
# 3. 图片总时长 vs 音频总时长（误差 < 1s）
# 4. 每张图时长是否在合理范围（1-7s）
# 5. 图片文件名关键词 vs 语音内容关键词 语义交叉比对
# 6. 输出完整对照表（图片 + 时长 + 语义✅/❌ + 对应语音文字）

# 退出码 0 = 通过，1 = 失败
# 失败时禁止合成，必须修复后重新校验！
```

**注意：video_maker.py 也内置了硬校验——duration 必须是精确正数浮点数，缺失或非数字直接拒绝执行并 exit(1)！duration: auto 已被彻底删除！**

### 时长分配表模板

生成配置前，先输出分配表确认：

```markdown
| 场景图 | 对应内容 | 开始 | 结束 | 时长 |
|--------|----------|------|------|------|
| cover.png | 开场引入 | 0s | 12.5s | 12.5s |
| scene01.png | AI Agent时代 | 12.5s | 26s | 13.5s |
| ... | ... | ... | ... | ... |
| **合计** | | | | **{total}s** |

音频总时长：{audio_duration}s
差值：{diff}s ✅/❌
```

---

## 字幕规范

字幕使用 ASS 格式，**强制底部居中固定位置**：

- 位置：底部居中（Alignment=2）
- 字体：PingFang SC
- 大小：屏幕高度 / 40
- 描边：2px 黑色描边 + 1px 阴影
- 底边距：屏幕高度 / 20

**禁止**：字幕乱跑、大小不一、位置不固定

---

## 脚本参数说明

### video_maker.py

```bash
python video_maker.py config.yaml [options]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--no-outro` | 不添加片尾 | 添加 |
| `--no-bgm` | 不添加BGM | 添加 |
| `--fade` | 转场时长(秒) | 0.5 |
| `--bgm-volume` | BGM音量 | 0.08 |
| `--bgm` | 自定义BGM（可选: epic） | 默认科技风 |
| `--ratio` | 视频比例 | 16:9（会被配置文件覆盖） |
| `--srt` | 字幕文件路径 | 无 |

### verify_alignment.py

```bash
python verify_alignment.py video_config.yaml
```

| 校验项 | 说明 |
|--------|------|
| 图片存在性 | 所有图片文件必须存在 |
| duration 精确性 | 必须是正数浮点数，禁止 auto/空值/非数字 |
| 总时长匹配 | 图片总时长 vs 音频总时长，误差 < 1s |
| 单图时长范围 | 每张图 1-7 秒，超出警告 |
| 语义交叉比对 | 总结段图片文件名关键词 vs 语音内容关键词匹配 |

### tts_generator.py

```bash
python tts_generator.py --text "文本" --output audio.mp3 [options]
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--voice` | 音色 | zh-CN-YunxiNeural |
| `--rate` | 语速 | +0% |
| `--timestamps` | 输出时间戳JSON | 否 |

---

## 支持的视频比例

与 `image-service` 生图服务保持一致，支持 **10 种比例**：

| 比例 | 分辨率 | 适用场景 |
|------|--------|----------|
| 1:1 | 1024×1024 | 正方形，朋友圈 |
| 2:3 | 832×1248 | 竖版海报 |
| 3:2 | 1248×832 | 横版海报 |
| 3:4 | 1080×1440 | 小红书、朋友圈 |
| 4:3 | 1440×1080 | 传统显示器 |
| 4:5 | 864×1080 | Instagram |
| 5:4 | 1080×864 | 横版照片 |
| 9:16 | 1080×1920 | 抖音、视频号、竖屏 |
| 16:9 | 1920×1080 | B站、YouTube、横屏 |
| 21:9 | 1536×672 | 超宽屏电影 |

---

## 片尾规范

**铁律：所有视频必须自动拼接对应尺寸的片尾！**

片尾匹配顺序：
1. 精确匹配：`outro_{ratio}.mp4`
2. 方向匹配：竖版→`outro_9x16.mp4`，横版→`outro_16x9.mp4`
3. 兜底：`outro.mp4`

---

## BGM 资源

### 按风格分类

| 风格 | 文件 | 快捷参数 | 适用场景 |
|------|------|----------|----------|
| **古风/中国风** | `bgm_ancient_tale.mp3` | `ancient` | 水浒、三国、历史故事 |
| | `bgm_asian_drums.mp3` | `asian` | 武侠、动作、战斗 |
| | `bgm_meditation.mp3` | `meditation` | 禅意、冥想、国学 |
| | `bgm_garden.mp3` | `garden` | 田园、悠闲、风景 |
| **治愈/轻松** | `bgm_carefree.mp3` | `carefree` | Vlog、日常、生活 |
| | `bgm_dreamy.mp3` | `dreamy` | 梦幻、回忆、温馨 |
| | `bgm_happybee.mp3` | `happybee` | 欢快、明亮、阳光 |
| **热血/史诗** | `bgm_epic.mp3` | `epic` | 励志、战斗、高燃 |
| | `bgm_heroic.mp3` | `heroic` | 英雄、胜利、荣耀 |
| | `bgm_crusade.mp3` | `crusade` | 战争、史诗、宏大 |
| | `bgm_allthis.mp3` | `allthis` | 电影感、叙事、情感 |
| **科技/未来** | `bgm_technology.mp3` | `tech` | AI、产品、教程 |
| | `bgm_digital.mp3` | `digital` | 数码、网络、互联网 |
| | `bgm_chasm.mp3` | `chasm` | 科幻、太空、神秘 |
| **悬疑/紧张** | `bgm_anxiety.mp3` | `anxiety` | 推理、紧张、危机 |
| | `bgm_darkfog.mp3` | `darkfog` | 恐怖、黑暗、悬疑 |
| **欢快/活泼** | `bgm_funky.mp3` | `funky` | 搞笑、轻松、节奏感 |
| | `bgm_happyboy.mp3` | `happyboy` | 可爱、儿童、动画 |
| | `bgm_doh.mp3` | `doh` | 俏皮、有趣、短视频 |
| **电子/节奏** | `bgm_edm.mp3` | `edm` | 动感、剪辑、卡点 |
| | `bgm_electro.mp3` | `electro` | 电子、现代、潮流 |
| | `bgm_bitshift.mp3` | `bitshift` | 游戏、8-bit、复古电子 |
| | `bgm_hiphop.mp3` | `hiphop` | 说唱、街头、潮酷 |

### 使用方式

```bash
# 方式1：快捷参数（推荐）
python video_maker.py config.yaml --bgm epic
python video_maker.py config.yaml --bgm ancient
python video_maker.py config.yaml --bgm edm

# 方式2：完整文件名
python video_maker.py config.yaml --bgm bgm_ancient_tale.mp3

# 方式3：自定义路径
python video_maker.py config.yaml --bgm /path/to/custom.mp3
```

---

## 常用音色

| 音色 ID | 风格 |
|---------|------|
| zh-CN-YunyangNeural | 男声，新闻播报 |
| zh-CN-YunxiNeural | 男声，阳光活泼 |
| zh-CN-XiaoxiaoNeural | 女声，温暖自然 |
| zh-CN-XiaoyiNeural | 女声，活泼可爱 |

---

## 目录结构

```
video-creator/
├── SKILL.md
├── scripts/
│   ├── video_maker.py        # 主脚本：图片+音频→视频（内置duration硬卡）
│   ├── verify_alignment.py   # 合成前强制校验（时长+语义交叉比对）
│   ├── tts_generator.py      # TTS 语音生成
│   └── scene_splitter.py     # 场景拆分器（可选）
├── assets/
│   ├── outro.mp4             # 通用片尾（16:9）
│   ├── outro_9x16.mp4        # 竖版片尾
│   ├── outro_3x4.mp4         # 3:4片尾
│   └── bgm_*.mp3             # 22首BGM（详见BGM资源表）
└── references/
    └── edge_tts_voices.md
```

---

## 依赖

```bash
# 系统依赖
brew install ffmpeg  # Mac

# Python 依赖
pip install edge-tts pyyaml
```
