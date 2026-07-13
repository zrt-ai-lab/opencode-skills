---
name: ai-video-script
description: Use when a request asks for a Chinese-first AI video script with shot plans, image prompts, narration, subtitles, or handoff contracts for scene generation, image generation, video assembly, or WeChat draft preparation.
---

# AI 视频脚本

## 用途

把主题、故事、产品资料或知识点整理成可审阅、可生图、可配音、可合成的视频脚本。该 Skill 负责策划和交接，不代替图像生成、视频合成或公众号发布工具。

## 触发场景

- 需要生成短视频、故事视频、知识视频、产品介绍或口播视频脚本。
- 需要把长文本拆成镜头，并为每个镜头准备画面提示词、旁白和字幕。
- 需要把脚本交给 `story-to-scenes`、`image-service`、`video-creator` 或 `wechat-publisher` 继续处理。
- 需要批量生成不同平台、时长或风格的脚本版本。

不因单独的图片生成、视频合成、字幕烧录或公众号发布请求触发本 Skill；这些请求交给对应的兄弟 Skill。

## 安全边界

- 只规划和整理内容，默认不调用外部服务、不发布、不写入凭证。
- 只使用相对路径和占位符，例如 `projects/{project_id}/scenes/scene-01.png`。
- 不写入个人姓名、个人路径、内部品牌、私有配置、Token、Cookie、AppSecret 或固定绝对路径。
- 不修改 `story-to-scenes`、`image-service`、`video-creator`、`wechat-publisher` 的文件；交接只通过约定字段和相对产物路径完成。
- 未得到明确确认时，只输出草稿和待确认项，不执行生图、合成或发布。

## 输入契约

先收集下表字段。缺失非关键字段时使用默认值，并在结果中记录默认值；缺失主题、用途或时长时先提出一个最小澄清问题。

| 字段 | 必填 | 默认值或约束 |
|---|---:|---|
| `topic` | 是 | 主题、故事、产品或知识点 |
| `purpose` | 是 | 共鸣、科普、转化、品牌认知或其他目标 |
| `audience` | 否 | `普通观众` |
| `platform` | 否 | `通用视频`；短视频平台通常使用竖屏 |
| `duration_sec` | 是 | 建议 15–180 秒；未提供时询问，不擅自猜测 |
| `aspect_ratio` | 否 | 通用默认 `16:9`；明确短视频平台时采用 `9:16` |
| `style` | 否 | `清晰、节奏紧凑、视觉统一` |
| `source_material` | 否 | 公开文本、要点、产品资料或故事梗概 |
| `cta` | 否 | 无；仅在确有目标时添加行动号召 |
| `constraints` | 否 | 敏感词、版权、品牌用语、画面禁用项等 |

## 标准输出契约

每次交付都生成一份人类可读脚本，并按需生成结构化交接数据。推荐的脚本交付包如下：

```text
projects/{project_id}/
├── script.md                 # 审阅版脚本，必需
├── script.yaml               # 结构化脚本，需下游自动化时提供
├── prompts/                  # 每个镜头的中文提示词，可选
│   ├── scene-01.txt
│   └── scene-02.txt
└── handoff/                  # 下游交接清单，可选
    ├── scene-manifest.yaml
    ├── image-manifest.yaml
    ├── narration-plan.yaml
    └── wechat-article.md
```

### 项目级字段

```yaml
schema_version: "1.0"
project:
  id: "{project_id}"
  title: "{title}"
  topic: "{topic}"
  purpose: "{purpose}"
  audience: "{audience}"
  platform: "{platform}"
  duration_sec: 30
  aspect_ratio: "16:9"
  style: "{style}"
  cta: "{cta_or_empty}"
  status: draft
global_visual:
  style_prefix_zh: "{全片统一风格前缀}"
  palette: "{色彩基调}"
  continuity_rules:
    - "{角色、道具、场景或镜头连续性规则}"
  negative_prompt_zh: "无水印、无随机文字、无多格拼接"
scenes: []
```

### 镜头级字段

每个镜头至少填写以下字段；时码在未完成 TTS 前只能标记为估算：

```yaml
- id: "scene-01"
  title: "{镜头标题}"
  purpose: "hook"
  timecode:
    start_sec_estimate: 0
    end_sec_estimate: 4
    duration_sec_estimate: 4
    final_duration_sec: null
    duration_source: "pending_tts"
  visual:
    description_zh: "主体、动作、环境、细节、构图和光线"
    shot_type: "特写"
    camera_motion: "缓慢推进"
    prompt_zh: "{可直接交给图像 Skill 的中文提示词}"
    negative_prompt_zh: "{中文排除词}"
    reference_assets: []
    output_path: "projects/{project_id}/scenes/scene-01.png"
  audio:
    narration: "{旁白}"
    subtitle: "{屏幕字幕}"
    emotion: "{语气和情绪}"
    sound_design: "{环境声或音效；没有则留空}"
  continuity:
    characters: []
    locations: []
    props: []
  handoff:
    story_to_scenes: false
    image_service: true
    video_creator: true
    wechat_publisher: false
```

硬性要求：最终交给 `video-creator` 的 `final_duration_sec` 必须来自 TTS 生成的 `narration.json` 时间戳，禁止使用估算值、平均分配或 `duration: auto`。

## 标准工作流

### 1. 解析需求

提取主题、目的、受众、平台、时长、比例、风格、资料和行动号召。将不确定项列为“待确认”，不要把猜测写成事实。

### 2. 设计内容结构

按视频目的选择结构：

- 转化类：问题钩子 → 产品或方案 → 证据 → 行动号召。
- 故事类：设定 → 冲突 → 转折 → 结果或余韵。
- 科普类：反常识钩子 → 核心解释 → 示例 → 结论。
- 口播类：一句结论 → 三个要点 → 一句收束。

为每个镜头标注 `purpose`，避免只有画面描述而没有叙事功能。

### 3. 拆分镜头

根据语义变化、动作变化、信息点和节奏切镜，不按字数机械平均。每个镜头必须同时说明：

1. 画面主体和动作；
2. 环境、时间、光线和色彩；
3. 景别、构图和镜头运动；
4. 旁白、字幕和情绪；
5. 角色、道具、地点的连续性；
6. 中文生图提示词、排除词和相对输出路径。

优先保持同一项目的风格前缀、比例、色彩和角色描述一致。画面文字只有在脚本明确需要时才加入；默认排除水印、随机字母、乱码和多格拼接。

### 4. 编写旁白与字幕

- 旁白使用口语化短句，先保证信息完整，再压缩节奏。
- 字幕与旁白保持语义一致，单条字幕只承载一个信息点。
- 不把尚未确认的事实、价格、效果或承诺写成确定结论。
- 将旁白拆成可供 TTS 返回时间戳的句段，并在 `narration-plan.yaml` 中保持句段与镜头映射。

### 5. 执行交接前检查

完成以下检查后再输出交接包：

- 所有镜头都有唯一 `id`，编号连续，顺序与脚本一致。
- 时长估算总和与目标时长一致；最终时长仍标记为 `pending_tts`。
- 每条 `prompt_zh` 都写明主体、动作、环境、细节、风格和色彩。
- 所有画面使用同一比例；存在参考图时记录相对路径。
- 旁白、字幕、画面和音效没有互相矛盾。
- 输出路径全部为相对路径或占位符。
- 删除个人信息、内部信息、凭证和私有配置。

## 与现有 Skill 的交接契约

本 Skill 只提供内容与字段，不复制或修改下游 Skill。按需求选择下表中的一条或多条交接路径。

| 下游 Skill | 触发条件 | 交给它的最小输入 | 它负责的结果 | 本 Skill 的边界 |
|---|---|---|---|---|
| `story-to-scenes` | 输入是故事、课程、绘本或长文本，需要角色和场景一致性 | `scene-manifest.yaml`：角色、地点、场景描述、镜头类型、风格前缀、比例 | 角色胚子、场景图和图集索引 | 不代替角色锁定、场景图生成或断点续传 |
| `image-service` | 需要生成或编辑镜头画面 | `image-manifest.yaml`：`prompt_zh`、排除词、比例、参考图相对路径、输出相对路径 | 图片或编辑后的图片 | 不读取私有配置，不直接调用图像 API |
| `video-creator` | 旁白已确认，需要 TTS、字幕和视频合成 | `narration-plan.yaml`、图片清单、比例、BGM/片尾偏好 | `narration.mp3`、`narration.json`、字幕、校验后的配置和视频 | 不伪造最终时长；TTS 后必须回填时间戳并通过对齐校验 |
| `wechat-publisher` | 明确要求把脚本改成公众号草稿或发布素材 | `wechat-article.md`：标题、摘要、正文、相对图片路径、公开链接 | 排版预览或公众号草稿 | 不在脚本阶段注入凭证，不默认发布 |

### `story-to-scenes` 交接字段

```yaml
project_id: "{project_id}"
source_type: story
aspect_ratio: "16:9"
style_prefix_zh: "{统一风格}"
characters:
  - id: "character-01"
    name: "{角色名}"
    description_zh: "{可复用外貌描述}"
locations:
  - id: "location-01"
    name: "{地点名}"
    description_zh: "{环境描述}"
scenes:
  - id: "scene-01"
    description_zh: "{场景动作和叙事目的}"
    shot_type: "中景"
    mood: "{情绪}"
```

### `image-service` 交接字段

```yaml
project_id: "{project_id}"
aspect_ratio: "16:9"
style_prefix_zh: "{统一风格}"
items:
  - scene_id: "scene-01"
    mode: text_to_image
    prompt_zh: "{中文提示词}"
    negative_prompt_zh: "{中文排除词}"
    reference_assets: []
    output_path: "projects/{project_id}/scenes/scene-01.png"
```

### `video-creator` 交接字段

```yaml
project_id: "{project_id}"
aspect_ratio: "16:9"
narration:
  text: "{完整旁白}"
  segments:
    - id: "narration-01"
      scene_ids: ["scene-01"]
      text: "{句段旁白}"
images:
  - scene_id: "scene-01"
    file: "projects/{project_id}/scenes/scene-01.png"
    duration_source: "narration.json"
    final_duration_sec: null
subtitles_path: "projects/{project_id}/subtitles.srt"
video_config_path: "projects/{project_id}/video_config.yaml"
```

在 TTS 完成后，将 `narration.json` 的句段起止时间映射回 `scene_ids`，计算每张图的最终时长，运行下游的对齐校验，再允许合成。

### `wechat-publisher` 交接字段

只有在明确要求时生成：

```markdown
---
title: {公开标题}
cover: ./assets/cover.jpg
---

# {公开标题}

> {一句话摘要}

## 视频看点

{从脚本整理出的公开内容}

![配图](./assets/scene-01.jpg)

## 观看与行动

{公开链接或行动号召}
```

封面和配图必须使用相对路径；草稿提交前由 `wechat-publisher` 完成内容、安全和权限检查。

## 质量检查单

### 内容

- [ ] 开头在目标平台的首个节奏点提出明确问题、冲突或收益。
- [ ] 每个镜头都推进信息、情绪或动作，删除无功能的空镜。
- [ ] 结尾与 `purpose` 一致；没有 CTA 时不强行添加 CTA。

### 视觉

- [ ] 同一项目统一比例、风格前缀、色彩和角色描述。
- [ ] 提示词包含主体、动作、环境、细节、风格和色彩。
- [ ] 默认排除水印、随机文字、乱码、多格拼接和无关人物。
- [ ] 故事类项目先交给 `story-to-scenes` 处理角色/场景一致性，再交给 `image-service` 生成具体画面。

### 音画

- [ ] 旁白句段可被 TTS 清晰切分。
- [ ] 字幕与旁白语义一致、长度可读。
- [ ] `final_duration_sec` 在 TTS 前为空，TTS 后来自 `narration.json`。
- [ ] 视频合成前已经运行 `video-creator` 的音画对齐校验。

### 脱敏与交付

- [ ] 没有个人姓名、个人路径、内部品牌、私有配置或凭证。
- [ ] 所有资源路径为相对路径或占位符。
- [ ] 仅在明确要求时生成 `wechat-article.md`，且不默认提交或发布。

## 可复用资源

- `templates/video-script.md`：标准中文脚本模板，包含项目字段、镜头字段和交接字段。
- `examples/product-launch.md`：一个脱敏的 30 秒产品介绍示例，用于检查字段是否完整。
