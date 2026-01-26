---
name: video-creator
description: 视频创作技能。图片+音频合成视频，支持淡入淡出转场、自动拼接片尾、添加BGM。当用户提到「生成视频」「图文转视频」「做视频号」时触发此技能。
---

# Video Creator

图片+音频合成视频工具。

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
│ 第三层：生成配音 + 字幕 + 合成视频                             │
│                                                              │
│   1. tts_generator.py 生成配音 + 时间戳                       │
│   2. 【铁律】根据时间戳精确计算每张图的duration（见下方规范）  │
│   3. 生成 SRT 字幕                                            │
│   4. 生成 video_config.yaml 前必须校验总时长                  │
│   5. video_maker.py 合成：                                    │
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
# 第一层：并发生成场景主图
python .opencode/skills/image-service/scripts/text_to_image.py "风格描述，场景1内容" -r 9:16 -o scene1/main.png &
python .opencode/skills/image-service/scripts/text_to_image.py "风格描述，场景2内容" -r 9:16 -o scene2/main.png &
wait

# 第二层：并发图生图生成细镜头
python .opencode/skills/image-service/scripts/image_to_image.py scene1/main.png "保持角色风格，细镜头描述" -r 9:16 -o scene1/shot_01.png &
python .opencode/skills/image-service/scripts/image_to_image.py scene1/main.png "保持角色风格，细镜头描述" -r 9:16 -o scene1/shot_02.png &
wait

# 第三层：生成配音+合成视频
python .opencode/skills/video-creator/scripts/tts_generator.py --text "完整旁白" --output narration.mp3 --timestamps
python .opencode/skills/video-creator/scripts/video_maker.py video_config.yaml --srt subtitles.srt --bgm epic
```

---

## 视频配置文件格式

```yaml
# video_config.yaml
ratio: "9:16"           # 必须加引号！避免YAML解析错误
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

**注意**：`ratio` 必须用引号包裹，如 `"9:16"`，否则 YAML 会解析成时间格式。

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
3. **生成配置前必须校验**，确保图片总时长 ≈ 音频总时长（误差<1秒）
4. **禁止让脚本自动拉伸**，音画不同步的视频不合格

### 时长分配表模板

生成配置前，先输出分配表让用户确认：

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

| 文件 | 风格 | 适用场景 |
|------|------|----------|
| `bgm_technology.mp3` | 科技感 | 技术教程、产品介绍 |
| `bgm_epic.mp3` | 热血史诗 | 故事、战斗、励志 |

使用：`--bgm epic` 或 `--bgm /path/to/bgm.mp3`

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
│   ├── video_maker.py      # 主脚本：图片+音频→视频
│   ├── tts_generator.py    # TTS 语音生成
│   └── scene_splitter.py   # 场景拆分器（可选）
├── assets/
│   ├── outro.mp4           # 通用片尾（16:9）
│   ├── outro_9x16.mp4      # 竖版片尾
│   ├── outro_3x4.mp4       # 3:4片尾
│   ├── bgm_technology.mp3  # 默认BGM
│   └── bgm_epic.mp3        # 热血BGM
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
