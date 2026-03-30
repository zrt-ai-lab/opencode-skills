# video-subtitle-remover

视频硬字幕/水印去除技能，基于 [YaoFANGUK/video-subtitle-remover](https://github.com/YaoFANGUK/video-subtitle-remover)，自动完成环境配置和执行。

## 核心流程

```
环境检查 → 拉取代码+模型 → 注入 Mac 修复 → ffprobe 评估 → STTN 去字幕 → 输出
```

## 两阶段工作流

### 阶段一：环境准备（首次自动执行）

| 步骤 | 内容 |
|------|------|
| 拉取代码 | 从 GitHub 拉取源码到 `~/.opencode/tools/video-subtitle-remover/`，跳过大文件 |
| 安装依赖 | torch、torchvision、paddleocr 等 Python 包 |
| 下载模型 | STTN 推理模型 + PaddleOCR 文本检测模型（3 分片合并） |
| 注入修复 | MPS 设备支持、ffmpeg 路径修复、移除多余模型校验 |

### 阶段二：执行任务

| 步骤 | 内容 |
|------|------|
| 评估 | ffprobe 获取视频信息，预报处理时间 |
| 处理 | 运行 `run_remove.py`，长视频用 tmux 后台执行 |
| 交付 | 自动打开输出的 `_no_sub.mp4` |

## 使用方式

```bash
export KMP_DUPLICATE_LIB_OK=True
python3 ~/.opencode/tools/video-subtitle-remover/run_remove.py "/path/to/video.mp4"
```

## 触发场景

- "去字幕"、"去除视频字幕"
- "去掉视频里的文字/水印"
- "把这视频的字幕干掉"

## 依赖

- Python 3.10+
- ffmpeg（`brew install ffmpeg`）
- Apple Silicon MPS 或 CUDA GPU（推荐）

## License

MIT
