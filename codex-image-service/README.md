# codex-image-service

基于 Codex 原生生图工具的工程化图像 Skill。单图任务可以直接生成；物料套图、微信长图、九宫格、卡片系列、分镜和幻灯片等批量任务必须先规划、确认，再逐张生成、后处理和验收。

## 核心行为

- 自动识别“一组、一套、系列、物料、长图、多屏”等批量语义。
- 批量任务先输出逐图清单，并等待用户明确确认。
- 一个独立成品对应一次原生生图调用。
- 串行引用真实定调图，维持角色、品牌和版式一致性。
- 微信长图先分屏生成，再用本地脚本纵向拼接。
- 连续长图为每个相邻屏建立接缝契约，预留安全区并逐条检查 1:1 接缝预览。
- 拼接脚本支持重叠羽化、局部色彩匹配和接缝预览；零重叠硬拼仅用于卡片式版面。
- 独立源图通过后可用 JSON 布局派生九宫格、主视觉加卡片、杂志非对称布局、横版故事板和竖版瀑布流。
- 内置编辑、电商、建筑、时尚、食品和文旅六类行业物料规划。
- 物料套图先交付独立成品，合集预览不计入成品数量。
- 最终核对计划数量、实际数量、质量状态和真实文件。

## 资源

- `SKILL.md`：任务分类、确认硬闸门、状态机和交付规则。
- `templates/batch-project-manifest.md`：项目定义和产物台账。
- `templates/material-kit-plan.md`：物料套图默认结构。
- `templates/custom-grid-plan.md`：自定义网格的源图、布局和裁切规划。
- `templates/wechat-long-image-plan.md`：微信长图分屏与拼接计划。
- `templates/quality-gate.md`：逐张和整批质量检查。
- `scripts/assemble_images.py`：本地纵向拼接、联系表和 JSON 自定义网格制作。
- `references/`：场景流程、提示词、文字、配色和营销参考。

## 本地后处理

脚本依赖 Pillow，只处理已有图片，不调用任何图像服务。

```bash
python scripts/assemble_images.py stitch-vertical \
  --overlap 160 --blend cosine --color-match \
  --seam-preview preview/wechat-seams.png \
  --output final/wechat-long.png source/01.png source/02.png source/03.png

python scripts/assemble_images.py contact-sheet \
  --columns 2 --output preview/material-kit.png final/01.png final/02.png final/03.png final/04.png

python scripts/assemble_images.py custom-grid \
  --layout references/grid-layouts/editorial-asymmetric.json \
  --layout-report preview/editorial-layout.json \
  --output final/editorial.png final/01.png final/02.png final/03.png final/04.png
```

`--overlap` 应落在各屏已规划的无文字、无关键主体过渡安全区内。场景或镜头尺度明显跳变时，先生成或编辑桥接画面，再执行重叠融合；不要用大范围模糊或交叉淡化掩盖结构断裂。

本 Skill 不包含外部图像服务配置、凭证、客户端或自动发布逻辑。
