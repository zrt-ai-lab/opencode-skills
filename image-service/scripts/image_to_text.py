#!/usr/bin/env python3
"""
图生文脚本 (Image-to-Text) - 视觉识别
使用 Qwen2.5-VL 模型分析图片内容并生成文字描述

Author: 翟星人
"""

import httpx
import base64
import json
import os
from typing import Dict, Any, Optional, Union, List
from pathlib import Path


class ImageToTextAnalyzer:
    """图生文分析器 - 视觉识别"""
    
    # 预定义的分析模式
    ANALYSIS_MODES = {
        "describe": "请详细描述这张图片的内容，包括：人物、场景、物品、颜色、布局等所有细节。",
        "ocr": "请仔细识别这张图片中的所有文字内容，按照文字在图片中的位置顺序输出。如果是中文，请保持原文输出。",
        "chart": "请分析这张图表的内容，包括：图表类型、数据趋势、关键数据点、标题标签、以及数据的结论或洞察。",
        "fashion": "请分析这张图片中人物的穿搭，包括：服装款式、颜色搭配、配饰、整体风格等。",
        "product": "请分析这张产品图片，包括：产品类型、外观特征、功能特点、品牌信息等。",
        "scene": "请描述这张图片的场景，包括：地点、环境、氛围、时间（白天/夜晚）等。"
    }
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        初始化分析器
        
        Args:
            config: 配置字典，包含 api_key, base_url, model
                   如果不传则从环境变量或配置文件读取
        """
        if config is None:
            config = self._load_config()
        
        self.api_key = config.get('api_key') or config.get('VISION_API_KEY') or config.get('IMAGE_API_KEY')
        self.base_url = config.get('base_url') or config.get('VISION_API_BASE_URL') or config.get('IMAGE_API_BASE_URL')
        self.model = config.get('model') or config.get('VISION_MODEL') or 'qwen2.5-vl-72b-instruct'
        
        if not self.api_key or not self.base_url:
            raise ValueError("缺少必要的 API 配置：api_key 和 base_url")
    
    def _load_config(self) -> Dict[str, str]:
        """从配置文件或环境变量加载配置"""
        config = {}
        
        # 尝试从配置文件加载
        config_path = Path(__file__).parent.parent / 'config' / 'settings.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # 优先使用 vision_api 配置
                vision_config = settings.get('vision_api', {})
                if vision_config:
                    config['api_key'] = vision_config.get('key')
                    config['base_url'] = vision_config.get('base_url')
                    config['model'] = vision_config.get('model')
                else:
                    # 回退到 image_api 配置
                    api_config = settings.get('image_api', {})
                    config['api_key'] = api_config.get('key')
                    config['base_url'] = api_config.get('base_url')
        
        # 环境变量优先级更高
        config['api_key'] = os.getenv('VISION_API_KEY', os.getenv('IMAGE_API_KEY', config.get('api_key')))
        config['base_url'] = os.getenv('VISION_API_BASE_URL', os.getenv('IMAGE_API_BASE_URL', config.get('base_url')))
        config['model'] = os.getenv('VISION_MODEL', config.get('model', 'qwen2.5-vl-72b-instruct'))
        
        return config
    
    @staticmethod
    def image_to_base64(image_path: str) -> str:
        """
        将图片文件转换为 base64 编码（带 data URL 前缀）
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            base64 编码字符串（含 data URL 前缀）
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
        # 获取 MIME 类型
        suffix = path.suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        mime_type = mime_types.get(suffix, 'image/png')
        
        with open(image_path, 'rb') as f:
            b64_str = base64.b64encode(f.read()).decode('utf-8')
        
        return f"data:{mime_type};base64,{b64_str}"
    
    def analyze(
        self,
        image: Union[str, bytes],
        prompt: Optional[str] = None,
        mode: str = "describe",
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        分析图片并生成文字描述
        
        Args:
            image: 图片路径、URL 或 base64 字符串
            prompt: 自定义分析提示词（如果提供则忽略 mode）
            mode: 分析模式 (describe/ocr/chart/fashion/product/scene)
            max_tokens: 最大输出 token 数
            temperature: 温度参数
            
        Returns:
            包含分析结果的字典
        """
        # 确定使用的提示词
        if prompt is None:
            prompt = self.ANALYSIS_MODES.get(mode, self.ANALYSIS_MODES["describe"])
        
        # 处理图片输入
        if isinstance(image, str):
            if os.path.isfile(image):
                image_url = self.image_to_base64(image)
            elif image.startswith('data:') or image.startswith('http'):
                image_url = image
            else:
                # 假设是纯 base64 字符串
                image_url = f"data:image/png;base64,{image}"
        else:
            image_url = f"data:image/png;base64,{base64.b64encode(image).decode('utf-8')}"
        
        # 构建请求
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                # 提取文本内容
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                return {
                    "success": True,
                    "content": content,
                    "mode": mode,
                    "usage": result.get("usage", {})
                }
                
        except httpx.HTTPStatusError as e:
            return {
                "success": False,
                "error": f"HTTP 错误: {e.response.status_code}",
                "detail": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "error": "分析失败",
                "detail": str(e)
            }
    
    def describe(self, image: Union[str, bytes]) -> Dict[str, Any]:
        """通用图片描述"""
        return self.analyze(image, mode="describe")
    
    def ocr(self, image: Union[str, bytes]) -> Dict[str, Any]:
        """文字识别 (OCR)"""
        return self.analyze(image, mode="ocr")
    
    def analyze_chart(self, image: Union[str, bytes]) -> Dict[str, Any]:
        """图表分析"""
        return self.analyze(image, mode="chart")
    
    def analyze_fashion(self, image: Union[str, bytes]) -> Dict[str, Any]:
        """穿搭分析"""
        return self.analyze(image, mode="fashion")
    
    def analyze_product(self, image: Union[str, bytes]) -> Dict[str, Any]:
        """产品分析"""
        return self.analyze(image, mode="product")
    
    def analyze_scene(self, image: Union[str, bytes]) -> Dict[str, Any]:
        """场景分析"""
        return self.analyze(image, mode="scene")
    
    def batch_analyze(
        self,
        images: List[str],
        mode: str = "describe"
    ) -> List[Dict[str, Any]]:
        """
        批量分析多张图片
        
        Args:
            images: 图片路径列表
            mode: 分析模式
            
        Returns:
            分析结果列表
        """
        results = []
        for image in images:
            result = self.analyze(image, mode=mode)
            result["image"] = image
            results.append(result)
        return results


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='图生文分析工具（视觉识别）')
    parser.add_argument('image', help='输入图片路径')
    parser.add_argument('-m', '--mode', default='describe',
                       choices=['describe', 'ocr', 'chart', 'fashion', 'product', 'scene'],
                       help='分析模式')
    parser.add_argument('-p', '--prompt', help='自定义分析提示词')
    parser.add_argument('--max-tokens', type=int, default=2000, help='最大输出 token 数')
    
    args = parser.parse_args()
    
    analyzer = ImageToTextAnalyzer()
    result = analyzer.analyze(
        image=args.image,
        prompt=args.prompt,
        mode=args.mode,
        max_tokens=args.max_tokens
    )
    
    if result["success"]:
        print(f"\n=== 分析结果 ({result['mode']}) ===\n")
        print(result["content"])
        print(f"\n=== Token 使用 ===")
        print(f"输入: {result['usage'].get('prompt_tokens', 'N/A')}")
        print(f"输出: {result['usage'].get('completion_tokens', 'N/A')}")
    else:
        print(f"分析失败: {result['error']}")
        print(f"详情: {result.get('detail', 'N/A')}")


if __name__ == "__main__":
    main()
