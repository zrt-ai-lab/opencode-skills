---
name: video-subtitle-remover
description: 视频硬字幕/水印去除技能。自动配置基于 YaoFANGUK/video-subtitle-remover 的环境并执行去字幕。当用户要求"去除视频字幕"、"去水印"、"把这个视频的字幕干掉"时触发此技能。
---

# 视频字幕去除技能 (Video Subtitle Remover)

## 触发场景
当用户提到以下关键词时触发本技能：
- "去字幕"、"去除视频字幕"
- "去掉视频里的文字/水印"
- "把这视频的字幕干掉"

## 工作流程

这是一个需要本地 GPU/Apple Silicon 加速的重型任务，你需要作为一个完整的执行器，从**环境准备**到**执行**全包揽。

### 第一阶段：环境检查与准备 (非常重要)

在首次运行前，必须检查环境并在用户机器上安装所需组件。工作目录约定为：`~/.opencode/tools/video-subtitle-remover`。

1. **检查目录与代码**
   使用 `bash` 检查 `~/.opencode/tools/video-subtitle-remover/run_remove.py` 是否存在。如果不存在，执行以下初始化操作：
   
   ```bash
   # 1. 创建工作目录
   mkdir -p ~/.opencode/tools/video-subtitle-remover/backend/models/{V4/ch_det,sttn}
   cd ~/.opencode/tools/video-subtitle-remover
   
   # 2. 拉取核心代码 (跳过模型文件)
   curl -sL "https://api.github.com/repos/YaoFANGUK/video-subtitle-remover/git/trees/main?recursive=1" | python3 -c "
   import sys, json, os, urllib.request
   data = json.load(sys.stdin)
   for item in data.get('tree', []):
       if item['type'] != 'blob': continue
       path = item['path']
       ext = os.path.splitext(path)[1].lower()
       if ext in {'.pth', '.onnx', '.pdiparams', '.pdmodel'} or '__pycache__' in path or item.get('size', 0) > 500000: continue
       
       os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
       url = f'https://raw.githubusercontent.com/YaoFANGUK/video-subtitle-remover/main/{path}'
       try:
           content = urllib.request.urlopen(url).read()
           with open(path, 'wb') as f: f.write(content)
       except: pass
   "
   ```

2. **安装 Python 依赖**
   ```bash
   pip3 install torch torchvision
   pip3 install filesplit==3.0.2 scikit-image pyclipper lmdb PyYAML omegaconf tqdm easydict scikit-learn pandas webdataset einops av shapely paddleocr paddle2onnx albumentations imgaug
   ```

3. **下载并合并模型 (STTN 模式必需)**
   如果 `backend/models/sttn/infer_model.pth` 或 `backend/models/V4/ch_det/inference.pdiparams` 不存在，使用 curl 下载：
   ```bash
   cd ~/.opencode/tools/video-subtitle-remover/backend/models
   # 下载 STTN 模型
   curl -L -o sttn/infer_model.pth "https://raw.githubusercontent.com/YaoFANGUK/video-subtitle-remover/main/backend/models/sttn/infer_model.pth"
   
   # 下载并合并 PaddleOCR 文本检测模型 (3个分割包)
   curl -L -o V4/ch_det/inference_1.pdiparams "https://raw.githubusercontent.com/YaoFANGUK/video-subtitle-remover/main/backend/models/V4/ch_det/inference_1.pdiparams"
   curl -L -o V4/ch_det/inference_2.pdiparams "https://raw.githubusercontent.com/YaoFANGUK/video-subtitle-remover/main/backend/models/V4/ch_det/inference_2.pdiparams"
   curl -L -o V4/ch_det/inference_3.pdiparams "https://raw.githubusercontent.com/YaoFANGUK/video-subtitle-remover/main/backend/models/V4/ch_det/inference_3.pdiparams"
   curl -L -o V4/ch_det/fs_manifest.csv "https://raw.githubusercontent.com/YaoFANGUK/video-subtitle-remover/main/backend/models/V4/ch_det/fs_manifest.csv"
   curl -L -o V4/ch_det/inference.pdiparams.info "https://raw.githubusercontent.com/YaoFANGUK/video-subtitle-remover/main/backend/models/V4/ch_det/inference.pdiparams.info"
   curl -L -o V4/ch_det/inference.pdmodel "https://raw.githubusercontent.com/YaoFANGUK/video-subtitle-remover/main/backend/models/V4/ch_det/inference.pdmodel"
   
   # 使用 Python 合并
   python3 -c "from fsplit.filesplit import Filesplit; fs=Filesplit(); fs.merge(input_dir='V4/ch_det')"
   ```

4. **注入修复代码与启动脚本**
   使用 `edit` 工具修改 `backend/config.py`：
   - 修复 Mac 的 MPS 设备支持 (`device = torch.device('mps')`)
   - 修复 FFMPEG_PATH 指向系统 ffmpeg (`shutil.which('ffmpeg')`)
   - 删除不必要的 LAMA 和 ProPainter 模型校验。
   
   并使用 `write` 工具生成 `run_remove.py` 启动脚本。

### 第二阶段：执行任务

1. **提取信息与评估**
   获取用户提供的视频绝对路径，运行 `ffprobe` 或 `ls -lh` 获取帧数，给用户预报处理时间。

2. **执行处理**
   运行处理脚本：
   ```bash
   export KMP_DUPLICATE_LIB_OK=True
   python3 ~/.opencode/tools/video-subtitle-remover/run_remove.py "<视频绝对路径>"
   ```
   *注意：如果视频较长，务必使用 tmux 放后台跑。*

3. **结果交付**
   使用 `open` 命令为用户自动打开输出的 `_no_sub.mp4` 视频。

