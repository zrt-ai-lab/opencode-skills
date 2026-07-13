---
schema_version: "1.0"
project_id: "{project_id}"
title: "{标题}"
topic: "{主题}"
purpose: "{共鸣 / 科普 / 转化 / 品牌认知}"
audience: "{受众}"
platform: "{平台}"
duration_sec: 30
aspect_ratio: "16:9"
style: "清晰、节奏紧凑、视觉统一"
cta: "{行动号召，可留空}"
---

# {标题}

## 项目概览

| 字段 | 内容 |
|---|---|
| 主题 | {主题} |
| 目的 | {目的} |
| 受众 | {受众} |
| 平台 | {平台} |
| 目标时长 | {秒数} 秒 |
| 画面比例 | {16:9 / 9:16 / 其他} |
| 视觉风格 | {风格} |
| CTA | {行动号召或无} |

## 全片统一规则

- **风格前缀**：{每条画面提示词都要复用的中文风格描述}
- **色彩基调**：{主色、辅助色、对比度}
- **连续性**：{角色、服装、道具、地点和时间的固定规则}
- **统一排除词**：无水印、无随机文字、无乱码、无多格拼接、无边框

## 分镜脚本

### scene-01｜{镜头标题}

| 字段 | 内容 |
|---|---|
| 叙事目的 | hook / explain / turn / close |
| 时码估算 | {开始}–{结束} 秒，估算 {时长} 秒 |
| 最终时长 | 待 TTS 时间戳确认 |
| 画面描述 | {主体 + 动作 + 环境 + 细节 + 构图 + 光线} |
| 景别 | {远景 / 中景 / 近景 / 特写} |
| 镜头运动 | {固定 / 推 / 拉 / 摇 / 移 / 跟拍} |
| 旁白 | {口语化旁白} |
| 字幕 | {该镜头屏幕文字} |
| 情绪与音效 | {情绪；环境声或音效} |
| 角色/地点/道具 | {连续性信息} |
| 输出路径 | `projects/{project_id}/scenes/scene-01.png` |

**中文画面提示词**

```text
{风格前缀}，{主体}正在{动作}，位于{环境}，画面包含{关键细节}，{景别和构图}，{光线和色彩}，画面干净、视觉统一
```

**中文排除词**

```text
无水印、无随机文字、无乱码、无多格拼接、无边框、无无关人物
```

**下游标记**

```yaml
handoff:
  story_to_scenes: false
  image_service: true
  video_creator: true
  wechat_publisher: false
reference_assets: []
```

### scene-02｜{镜头标题}

复制 `scene-01` 的字段结构，替换为新的叙事目的、时码估算、画面、旁白、字幕和交接标记。保持全片统一规则不变。

## 旁白句段映射

```yaml
segments:
  - id: "narration-01"
    scene_ids: ["scene-01"]
    text: "{句段旁白}"
    final_start_sec: null
    final_end_sec: null
  - id: "narration-02"
    scene_ids: ["scene-02"]
    text: "{句段旁白}"
    final_start_sec: null
    final_end_sec: null
duration_source: "narration.json"
```

TTS 完成后，将 `final_start_sec`、`final_end_sec` 和每个镜头的 `final_duration_sec` 回填；未回填前禁止把估算时长当作视频配置时长。

## 交接清单

- [ ] 故事类项目已整理 `scene-manifest.yaml`，包含角色、地点、风格和场景顺序。
- [ ] 图片项目已整理 `image-manifest.yaml`，每条包含中文提示词、排除词、比例和相对输出路径。
- [ ] 配音项目已整理 `narration-plan.yaml`，句段与镜头一一对应。
- [ ] 视频合成前将使用 `narration.json` 计算最终时长并通过音画对齐检查。
- [ ] 需要公众号素材时，另行生成带 frontmatter 和相对图片路径的 `wechat-article.md`。
- [ ] 已删除个人信息、内部信息、凭证、私有配置和固定绝对路径。
