#!/usr/bin/env python3
"""
文生图脚本 (Text-to-Image)
根据中文文本描述生成图片（OpenAI Images API 兼容）
支持参考图风格生成

Author: 翟星人
"""

import httpx
import base64
import json
import os
from typing import Dict, Any, Optional, Union
from pathlib import Path

VALID_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
]

VALID_SIZES = [
    "1024x1024",
    "1536x1024", "1792x1024", "1344x768", "1248x832", "1184x864", "1152x896", "1536x672",
    "1024x1536", "1024x1792", "768x1344", "832x1248", "864x1184", "896x1152"
]

RATIO_TO_SIZE = {
    "1:1": "1024x1024",
    "2:3": "832x1248",
    "3:2": "1248x832",
    "3:4": "1024x1536",
    "4:3": "1536x1024",
    "4:5": "864x1184",
    "5:4": "1184x864",
    "9:16": "1024x1792",
    "16:9": "1792x1024",
    "21:9": "1536x672"
}


class TextToImageGenerator:
    """文生图生成器"""
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        初始化生成器
        
        Args:
            config: 配置字典，包含 api_key, base_url, model
                   如果不传则从环境变量或配置文件读取
        """
        if config is None:
            config = self._load_config()
        
        self.api_key = config.get('api_key') or config.get('IMAGE_API_KEY')
        self.base_url = config.get('base_url') or config.get('IMAGE_API_BASE_URL')
        self.model = config.get('model') or config.get('IMAGE_MODEL') or 'dall-e-3'
        
        if not self.api_key or not self.base_url:
            raise ValueError("缺少必要的 API 配置：api_key 和 base_url")
    
    def _load_config(self) -> Dict[str, str]:
        """从配置文件或环境变量加载配置"""
        config = {}
        
        config_path = Path(__file__).parent.parent / 'config' / 'settings.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                api_config = settings.get('image_api', {})
                config['api_key'] = api_config.get('key')
                config['base_url'] = api_config.get('base_url')
                config['model'] = api_config.get('model')
        
        config['api_key'] = os.getenv('IMAGE_API_KEY', config.get('api_key'))
        config['base_url'] = os.getenv('IMAGE_API_BASE_URL', config.get('base_url'))
        config['model'] = os.getenv('IMAGE_MODEL', config.get('model'))
        
        return config
    
    @staticmethod
    def image_to_base64(image_path: str, with_prefix: bool = True) -> str:
        """将图片文件转换为 base64 编码"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")
        
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
        
        if with_prefix:
            return f"data:{mime_type};base64,{b64_str}"
        return b64_str
    
    def generate(
        self,
        prompt: str,
        size: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        image_size: Optional[str] = None,
        output_path: Optional[str] = None,
        response_format: str = "b64_json",
        ref_image: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成图片
        
        Args:
            prompt: 中文图像描述提示词
            size: 图片尺寸 (如 1792x1024)，与 aspect_ratio 二选一
            aspect_ratio: 宽高比 (如 16:9, 3:4)，推荐使用
            image_size: 分辨率 (1K/2K/4K)，仅 gemini-3.0-pro-image-preview 支持
            output_path: 输出文件路径，如果提供则保存图片
            response_format: 响应格式，默认 b64_json
            ref_image: 参考图片路径，用于风格参考
            
        Returns:
            包含生成结果的字典
        """
        if ref_image:
            return self._generate_with_reference(
                prompt=prompt,
                ref_image=ref_image,
                aspect_ratio=aspect_ratio,
                size=size,
                output_path=output_path,
                response_format=response_format
            )
        
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "response_format": response_format
        }
        
        # 确定尺寸：优先用 aspect_ratio 映射，其次用 size
        if aspect_ratio:
            payload["size"] = RATIO_TO_SIZE.get(aspect_ratio, "1024x1024")
        elif size:
            payload["size"] = size
        else:
            payload["size"] = "1792x1024"  # 默认 16:9
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(
                    f"{self.base_url}/images/generations",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                if output_path and result.get("data"):
                    b64_data = result["data"][0].get("b64_json")
                    if b64_data:
                        self._save_image(b64_data, output_path)
                        result["saved_path"] = output_path
                
                return {
                    "success": True,
                    "data": result,
                    "saved_path": output_path if output_path else None
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
                "error": "生成失败",
                "detail": str(e)
            }
    
    def _generate_with_reference(
        self,
        prompt: str,
        ref_image: str,
        aspect_ratio: Optional[str] = None,
        size: Optional[str] = None,
        output_path: Optional[str] = None,
        response_format: str = "b64_json"
    ) -> Dict[str, Any]:
        """
        参考图片风格生成新图
        
        Args:
            prompt: 新图内容描述
            ref_image: 参考图片路径
            aspect_ratio: 宽高比
            size: 尺寸
            output_path: 输出路径
            response_format: 响应格式
        """
        image_b64 = self.image_to_base64(ref_image)
        
        enhanced_prompt = f"参考这张图片的背景风格、配色方案和视觉设计，保持完全一致的风格，生成新内容：{prompt}"
        
        # 确定尺寸：优先用 aspect_ratio 映射，其次用 size
        if size is None:
            size = RATIO_TO_SIZE.get(aspect_ratio, "1024x1792") if aspect_ratio else "1024x1792"
        
        payload = {
            "model": self.model,
            "prompt": enhanced_prompt,
            "image": image_b64,
            "size": size,
            "response_format": response_format
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            with httpx.Client(timeout=180.0) as client:
                response = client.post(
                    f"{self.base_url}/images/edits",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                if output_path and result.get("data"):
                    b64_data = result["data"][0].get("b64_json")
                    if b64_data:
                        self._save_image(b64_data, output_path)
                        result["saved_path"] = output_path
                
                return {
                    "success": True,
                    "data": result,
                    "saved_path": output_path if output_path else None
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
                "error": "生成失败",
                "detail": str(e)
            }
    
    def _save_image(self, b64_data: str, output_path: str) -> None:
        """保存 base64 图片到文件"""
        image_data = base64.b64decode(b64_data)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(image_data)


def main():
    """命令行入口"""
    import argparse
    import time
    
    parser = argparse.ArgumentParser(
        description='文生图工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
尺寸参数说明:
  -r/--ratio  推荐使用，支持: {", ".join(VALID_ASPECT_RATIOS)}
  -s/--size   传统尺寸，支持: {", ".join(VALID_SIZES[:4])}...
  --resolution 分辨率(1K/2K/4K)，仅 gemini-3.0-pro-image-preview 支持
  --ref       参考图片路径，后续图片将参考首图风格生成

示例:
  python text_to_image.py "描述" -r 3:4              # 竖版 3:4
  python text_to_image.py "描述" -r 9:16 -o out.png  # 竖屏 9:16
  python text_to_image.py "描述" -s 1024x1792        # 传统尺寸
  
  # 长图场景：首图定调，后续参考首图风格
  python text_to_image.py "首屏内容" -r 3:4 -o 01.png
  python text_to_image.py "第二屏内容" -r 3:4 --ref 01.png -o 02.png
'''
    )
    parser.add_argument('prompt', help='中文图像描述提示词')
    parser.add_argument('-o', '--output', help='输出文件路径（默认保存到当前目录）')
    parser.add_argument('-r', '--ratio', help=f'宽高比，推荐使用。可选: {", ".join(VALID_ASPECT_RATIOS)}')
    parser.add_argument('-s', '--size', help='图片尺寸 (如 1792x1024)')
    parser.add_argument('--resolution', help='分辨率 (1K/2K/4K)，仅部分模型支持')
    parser.add_argument('--ref', help='参考图片路径，用于风格参考（长图场景）')
    
    args = parser.parse_args()
    
    if args.ratio and args.ratio not in VALID_ASPECT_RATIOS:
        print(f"错误: 不支持的宽高比 '{args.ratio}'")
        print(f"支持的宽高比: {', '.join(VALID_ASPECT_RATIOS)}")
        return
    
    if args.size and args.size not in VALID_SIZES:
        print(f"警告: 尺寸 '{args.size}' 可能不被支持")
        print(f"推荐使用 -r/--ratio 参数指定宽高比")
    
    if args.ref and not os.path.exists(args.ref):
        print(f"错误: 参考图片不存在: {args.ref}")
        return
    
    output_path = args.output
    if not output_path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = f"generated_{timestamp}.png"
    
    generator = TextToImageGenerator()
    result = generator.generate(
        prompt=args.prompt,
        size=args.size,
        aspect_ratio=args.ratio,
        image_size=args.resolution,
        output_path=output_path,
        ref_image=args.ref
    )
    
    if result["success"]:
        print(f"生成成功！")
        if result.get("saved_path"):
            print(f"图片已保存到: {result['saved_path']}")
    else:
        print(f"生成失败: {result['error']}")
        print(f"详情: {result.get('detail', 'N/A')}")


if __name__ == "__main__":
    main()
