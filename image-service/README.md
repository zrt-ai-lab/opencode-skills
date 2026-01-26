# Image Service

图像生成/编辑/分析服务。

## 依赖

```bash
pip install httpx pillow numpy
```

## 配置

编辑 `config/settings.json` 或设置环境变量：

```bash
export IMAGE_API_KEY="your_key"
export IMAGE_API_BASE_URL="https://api.openai.com/v1"
export VISION_API_KEY="your_key"
export VISION_API_BASE_URL="https://api.openai.com/v1"
```

## 功能

- 文生图 (text_to_image.py)
- 图生图 (image_to_image.py)
- 图片理解 (image_to_text.py)
- 长图拼接 (merge_long_image.py)
