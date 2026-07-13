# ai-video-script

中文优先的 AI 视频脚本规划 Skill。它把主题、故事、产品资料或知识点整理为镜头表、中文画面提示词、旁白、字幕和下游交接数据。

## 能做什么

- 生成 15–180 秒的短视频、故事、科普、口播和产品介绍脚本。
- 把长文本拆成有叙事目的的镜头，而不是按字数平均切分。
- 为每个镜头提供主体、动作、环境、构图、镜头运动、光线、旁白、字幕和中文提示词。
- 输出可交给 `story-to-scenes`、`image-service`、`video-creator` 和 `wechat-publisher` 的相对路径契约。
- 保留人工确认点，并强制最终视频时长以 TTS 时间戳为准。

## 不负责什么

- 不直接生成图片、调用 TTS、合成视频或发布公众号。
- 不读取、保存或展示任何凭证、Cookie、Token 或私有配置。
- 不修改其他 Skill；下游执行由对应 Skill 完成。

## 使用方式

将以下信息作为请求输入：

```text
主题：{主题或故事}
目的：{共鸣 / 科普 / 转化 / 品牌认知}
受众：{目标受众}
平台：{平台，可省略}
时长：{秒数}
比例：{16:9 / 9:16 / 其他，可省略}
风格：{视觉和叙事风格，可省略}
资料：{公开资料或要点，可省略}
行动号召：{可省略}
限制：{版权、敏感词、禁用画面，可省略}
```

建议先复制 [标准模板](templates/video-script.md)，再参考 [产品示例](examples/product-launch.md)。

## 输出结构

```text
projects/{project_id}/
├── script.md
├── script.yaml
├── prompts/                  # 可选：每镜头一个中文提示词文件
└── handoff/                  # 可选：下游交接清单
```

`script.md` 面向审阅；`script.yaml` 面向自动化；`handoff/` 只在确实需要下游执行时生成。所有文件中的资源路径必须是相对路径或占位符。

## 下游协作

| 阶段 | 调用 Skill | 交接文件 | 关键约束 |
|---|---|---|---|
| 故事拆镜与角色一致性 | `story-to-scenes` | `handoff/scene-manifest.yaml` | 先锁定角色和风格，再批量生成场景 |
| 具体图片生成或编辑 | `image-service` | `handoff/image-manifest.yaml` | 中文提示词；统一比例；记录参考图 |
| TTS、字幕和视频合成 | `video-creator` | `handoff/narration-plan.yaml` | 最终时长必须来自 `narration.json`，先校验再合成 |
| 公众号文章或草稿 | `wechat-publisher` | `handoff/wechat-article.md` | 仅按请求生成；图片相对路径；凭证由发布 Skill 管理 |

`ai-video-script` 只负责生成这些交接数据，不复制下游实现。

## 默认规则

- 未指定平台时使用 `16:9`；明确短视频平台时使用 `9:16`。
- 未指定风格时保持清晰、节奏紧凑、视觉统一。
- 未完成 TTS 时只填写 `duration_sec_estimate`，将 `final_duration_sec` 保持为空。
- 提示词默认使用中文，并排除水印、随机文字、乱码和多格拼接。
- 缺少主题、用途或时长时只询问最小必要信息，不将猜测写入脚本。

## 验证

在仓库根目录运行：

```bash
python3 .opencode/skills/tests/test_candidate_skills.py
python3 .opencode/skills/skill-creator/scripts/package_skill.py .opencode/skills/ai-video-script ./dist
unzip -l ./dist/ai-video-script.zip
```

打包脚本只应收录本目录内的公开文件；不要把 `_meta.json`、凭证、运行时配置或本机路径放入包中。
