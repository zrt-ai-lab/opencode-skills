#!/usr/bin/env python3
"""
图生图脚本 (Image-to-Image)
基于参考图片和中文指令进行图片编辑（OpenAI Images API 兼容）

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


class ImageToImageEditor:
    """图生图编辑器"""
    
    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        初始化编辑器
        
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
        
        # 尝试从配置文件加载
        config_path = Path(__file__).parent.parent / 'config' / 'settings.json'
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                api_config = settings.get('image_api', {})
                config['api_key'] = api_config.get('key')
                config['base_url'] = api_config.get('base_url')
                config['model'] = api_config.get('model')
        
        # 环境变量优先级更高
        config['api_key'] = os.getenv('IMAGE_API_KEY', config.get('api_key'))
        config['base_url'] = os.getenv('IMAGE_API_BASE_URL', config.get('base_url'))
        config['model'] = os.getenv('IMAGE_MODEL', config.get('model'))
        
        return config
    
    @staticmethod
    def image_to_base64(image_path: str, with_prefix: bool = True) -> str:
        """
        将图片文件转换为 base64 编码
        
        Args:
            image_path: 图片文件路径
            with_prefix: 是否添加 data URL 前缀
            
        Returns:
            base64 编码字符串
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
        
        if with_prefix:
            return f"data:{mime_type};base64,{b64_str}"
        return b64_str
    
    def edit(
        self,
        image: Union[str, bytes],
        prompt: str,
        aspect_ratio: Optional[str] = None,
        size: Optional[str] = None,
        output_path: Optional[str] = None,
        response_format: str = "b64_json"
    ) -> Dict[str, Any]:
        """
        编辑图片
        
        Args:
            image: 图片路径或 base64 字符串
            prompt: 中文编辑指令
            aspect_ratio: 宽高比 (如 3:4, 16:9)
            size: 传统尺寸 (如 1024x1792)
            output_path: 输出文件路径
            response_format: 响应格式
            
        Returns:
            包含编辑结果的字典
        """
        # 处理图片输入
        if isinstance(image, str):
            if os.path.isfile(image):
                image_b64 = self.image_to_base64(image)
            elif image.startswith('data:'):
                image_b64 = image
            else:
                # 假设是纯 base64 字符串
                image_b64 = f"data:image/png;base64,{image}"
        else:
            image_b64 = f"data:image/png;base64,{base64.b64encode(image).decode('utf-8')}"
        
        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "image": image_b64,
            "response_format": response_format
        }
        
        # 确定尺寸：优先用 aspect_ratio 映射，其次用 size
        if aspect_ratio:
            payload["size"] = RATIO_TO_SIZE.get(aspect_ratio, "1024x1536")
        elif size:
            payload["size"] = size
        else:
            payload["size"] = "1024x1536"  # 默认 3:4
        
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
                
                # 如果指定了输出路径，保存图片
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
                "error": "编辑失败",
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
        description='图生图编辑工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'''
尺寸参数说明:
  -r/--ratio    宽高比（推荐），支持: {", ".join(VALID_ASPECT_RATIOS)}
  -s/--size     传统尺寸，支持: {", ".join(VALID_SIZES[:4])}...

示例:
  python image_to_image.py input.png "编辑描述" -r 3:4
  python image_to_image.py input.png "编辑描述" -s 1024x1536
'''
    )
    parser.add_argument('image', help='输入图片路径')
    parser.add_argument('prompt', help='中文编辑指令')
    parser.add_argument('-o', '--output', help='输出文件路径（默认保存到当前目录）')
    parser.add_argument('-r', '--ratio', help=f'宽高比（推荐）。可选: {", ".join(VALID_ASPECT_RATIOS)}')
    parser.add_argument('-s', '--size', help='传统尺寸，如 1024x1536')
    
    args = parser.parse_args()
    
    if args.ratio and args.ratio not in VALID_ASPECT_RATIOS:
        print(f"错误: 不支持的宽高比 '{args.ratio}'")
        print(f"支持的宽高比: {', '.join(VALID_ASPECT_RATIOS)}")
        return
    
    if args.size and args.size not in VALID_SIZES:
        print(f"警告: 尺寸 '{args.size}' 可能不被支持")
    
    output_path = args.output
    if not output_path:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_path = f"edited_{timestamp}.png"
    
    editor = ImageToImageEditor()
    result = editor.edit(
        image=args.image,
        prompt=args.prompt,
        aspect_ratio=args.ratio,
        size=args.size,
        output_path=output_path
    )
    
    if result["success"]:
        print(f"编辑成功！")
        if result.get("saved_path"):
            print(f"图片已保存到: {result['saved_path']}")
    else:
        print(f"编辑失败: {result['error']}")
        print(f"详情: {result.get('detail', 'N/A')}")


if __name__ == "__main__":
    main()
