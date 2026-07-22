# codex-image-service

基于 Codex 原生生图工具的批量图像工程 Skill。单图任务可以直接生成；物料套图、九宫格、卡片系列、分镜、轮播、幻灯片、全景、局部植入和长图等批量任务必须先规划、确认，再逐张生成、选择合成策略、后处理和验收。长图只是其中一种交付形态。

## 核心行为

- 自动识别“一组、一套、系列、物料、长图、多屏”等批量语义。
- 批量任务先输出逐图清单，并等待用户明确确认。
- 一个独立成品对应一次原生生图调用。
- 串行引用真实定调图，维持角色、品牌和版式一致性。
- 根据交付场景选择 `material-kit`、`grid`、`storyboard`、`carousel`、`document`、`generated-continuous`、`panorama` 或 `object-blend`。
- 独立物料和页面使用确定性布局，不做无意义的像素融合。
- 连续生成图使用接口传递、平移校正、真实重叠检测和多频段融合。
- 实拍全景支持特征点、单应性、Graph Cut 和多频段融合；蒙版植入支持 Poisson。
- 普通“长图”默认采用连续模式；卡片式必须由用户明确指定。
- 连续长图为每个相邻屏建立接缝契约，提取真实接口图并校验接口相似度。
- 拼接脚本自动检测可信重叠区，默认执行多频段融合和局部色彩匹配，并输出接缝预览和 JSON 报告。
- 找不到可信接口时拒绝拼接；零重叠硬拼仅允许显式 `cards` 模式。
- 独立源图通过后可用 JSON 布局派生九宫格、主视觉加卡片、杂志非对称布局、横版故事板和竖版瀑布流。
- 内置编辑、电商、建筑、时尚、食品和文旅六类行业物料规划。
- 物料套图先交付独立成品，合集预览不计入成品数量。
- 最终核对计划数量、实际数量、质量状态和真实文件。

## 资源

- `SKILL.md`：任务分类、确认硬闸门、状态机和交付规则。
- `templates/batch-project-manifest.md`：项目定义和产物台账。
- `templates/composition-project.json`：所有批量项目的交付形态、资产和算法计划。
- `templates/material-kit-plan.md`：物料套图默认结构。
- `templates/custom-grid-plan.md`：自定义网格的源图、布局和裁切规划。
- `templates/wechat-long-image-plan.md`：微信长图分屏与拼接计划。
- `templates/quality-gate.md`：逐张和整批质量检查。
- `scripts/assemble_images.py`：本地纵向拼接、联系表和 JSON 自定义网格制作。
- `scripts/long_image_pipeline.py`：项目清单校验、接口提取和接口相似度检查。
- `scripts/adaptive_compositor.py`：场景路由、多频段融合、平移校正，以及可选的单应性、光流、Graph Cut、全景和 Poisson 合成。
- `references/composition-routing.md`：不同批量交付场景的算法边界和失败策略。
- `references/`：场景流程、提示词、文字、配色和营销参考。

## 本地后处理

基础规划、排版和多频段融合依赖 Pillow、NumPy；高级几何对齐、Graph Cut、全景、光流和 Poisson 使用可选 OpenCV 运行时。脚本自动发现 `CODEX_IMAGE_RUNTIME` 指定目录或 `~/.codex/image-runtime`。脚本只处理已有图片，不调用任何图像服务。高级运行时缺失时明确失败，不会回退硬拼。

```bash
python scripts/adaptive_compositor.py validate-project composition-project.json

python scripts/adaptive_compositor.py plan \
  --intent "把室内实拍照片拼成建筑全景" \
  --output preview/composition-routing.json

python scripts/adaptive_compositor.py blend-pair source/a.png source/b.png \
  --alignment translation --seam straight --blend multiband \
  --output final/blended.png --report preview/blended.json

python scripts/adaptive_compositor.py panorama source/01.jpg source/02.jpg \
  --output final/panorama.jpg --report preview/panorama.json

python scripts/long_image_pipeline.py validate-project project.json

python scripts/long_image_pipeline.py extract-interface source/01.png \
  --edge bottom --ratio 0.15 --output interfaces/01-bottom.png

python scripts/long_image_pipeline.py compare-interfaces \
  source/01.png source/02.png --ratio 0.15 \
  --report preview/interface-01-02.json

python scripts/assemble_images.py stitch-vertical \
  --mode continuous --project project.json --overlap auto --blend multiband \
  --seam-preview preview/wechat-seams.png \
  --seam-report preview/wechat-seams.json \
  --output final/wechat-long.png source/01.png source/02.png source/03.png

python scripts/assemble_images.py contact-sheet \
  --columns 2 --output preview/material-kit.png final/01.png final/02.png final/03.png final/04.png

python scripts/assemble_images.py custom-grid \
  --layout references/grid-layouts/editorial-asymmetric.json \
  --layout-report preview/editorial-layout.json \
  --output final/editorial.png final/01.png final/02.png final/03.png final/04.png
```

连续模式强制提供已确认的项目 JSON。拼接前会核对分屏顺序、接口文件和每条接缝的比对报告，再自动检测真实重叠量；任一证据缺失、报告未通过或检测低于可信阈值时直接失败。场景或镜头尺度明显跳变时，先生成或编辑桥接画面，再执行重叠融合；不要降低阈值或用大范围模糊掩盖结构断裂。

卡片式长图必须显式执行：

```bash
python scripts/assemble_images.py stitch-vertical --mode cards \
  --gap 32 --output final/cards-long.png source/01.png source/02.png
```

`--overlap` 应落在各屏已规划的无文字、无关键主体过渡安全区内。场景或镜头尺度明显跳变时，先生成或编辑桥接画面，再执行重叠融合；不要用大范围模糊或交叉淡化掩盖结构断裂。

本 Skill 不包含外部图像服务配置、凭证、客户端或自动发布逻辑。
