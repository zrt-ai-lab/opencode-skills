#!/usr/bin/env python3
"""
长图拼接脚本 (Merge Long Image)
将多张图片按顺序垂直拼接成一张微信长图

Author: 翟星人
"""

import argparse
import os
import glob as glob_module
from pathlib import Path
from typing import List, Optional, Dict, Any

from PIL import Image
import numpy as np


class LongImageMerger:
    """长图拼接器"""
    
    def __init__(self, target_width: int = 1080):
        """
        初始化拼接器
        
        Args:
            target_width: 目标宽度，默认1080（微信推荐宽度）
        """
        self.target_width = target_width
    
    def _blend_images(self, img_top: Image.Image, img_bottom: Image.Image, blend_height: int) -> Image.Image:
        """
        在两张图的接缝处创建渐变融合过渡
        
        Args:
            img_top: 上方图片
            img_bottom: 下方图片
            blend_height: 融合区域高度（像素）
            
        Returns:
            融合后的下方图片（顶部已与上方图片底部融合）
        """
        blend_height = min(blend_height, img_top.height // 4, img_bottom.height // 4)
        
        top_region = img_top.crop((0, img_top.height - blend_height, img_top.width, img_top.height))
        bottom_region = img_bottom.crop((0, 0, img_bottom.width, blend_height))
        
        top_array = np.array(top_region, dtype=np.float32)
        bottom_array = np.array(bottom_region, dtype=np.float32)
        
        alpha = np.linspace(1, 0, blend_height).reshape(-1, 1, 1)
        
        blended_array = top_array * alpha + bottom_array * (1 - alpha)
        blended_array = np.clip(blended_array, 0, 255).astype(np.uint8)
        
        blended_region = Image.fromarray(blended_array)
        
        result = img_bottom.copy()
        result.paste(blended_region, (0, 0))
        
        return result
    
    def merge(
        self,
        image_paths: List[str],
        output_path: str,
        gap: int = 0,
        background_color: str = "white",
        blend: int = 0
    ) -> Dict[str, Any]:
        """
        拼接多张图片为长图
        
        Args:
            image_paths: 图片路径列表，按顺序拼接
            output_path: 输出文件路径
            gap: 图片之间的间隔像素，默认0
            background_color: 背景颜色，默认白色
            blend: 接缝融合过渡区域高度（像素），默认0不融合，推荐30-50
            
        Returns:
            包含拼接结果的字典
        """
        if not image_paths:
            return {"success": False, "error": "没有提供图片路径"}
        
        valid_paths = []
        for p in image_paths:
            if os.path.exists(p):
                valid_paths.append(p)
            else:
                print(f"警告: 文件不存在，跳过 - {p}")
        
        if not valid_paths:
            return {"success": False, "error": "没有有效的图片文件"}
        
        try:
            imgs = [Image.open(p) for p in valid_paths]
            
            resized_imgs = []
            for img in imgs:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                ratio = self.target_width / img.width
                new_height = int(img.height * ratio)
                resized = img.resize((self.target_width, new_height), Image.Resampling.LANCZOS)
                resized_imgs.append(resized)
            
            if blend > 0 and len(resized_imgs) > 1:
                for i in range(1, len(resized_imgs)):
                    resized_imgs[i] = self._blend_images(resized_imgs[i-1], resized_imgs[i], blend)
            
            total_height = sum(img.height for img in resized_imgs) + gap * (len(resized_imgs) - 1)
            
            long_image = Image.new('RGB', (self.target_width, total_height), background_color)
            
            y_offset = 0
            for img in resized_imgs:
                long_image.paste(img, (0, y_offset))
                y_offset += img.height + gap
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            long_image.save(output_path, quality=95)
            
            for img in imgs:
                img.close()
            for img in resized_imgs:
                img.close()
            
            return {
                "success": True,
                "saved_path": output_path,
                "width": self.target_width,
                "height": total_height,
                "image_count": len(resized_imgs)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def merge_from_pattern(
        self,
        pattern: str,
        output_path: str,
        sort_by: str = "name",
        gap: int = 0,
        background_color: str = "white",
        blend: int = 0
    ) -> Dict[str, Any]:
        """
        通过 glob 模式匹配图片并拼接
        
        Args:
            pattern: glob 模式，如 "*.png" 或 "generated_*.png"
            output_path: 输出文件路径
            sort_by: 排序方式 - "name"(文件名) / "time"(修改时间) / "none"(不排序)
            gap: 图片间隔
            background_color: 背景颜色
            blend: 接缝融合过渡高度
            
        Returns:
            包含拼接结果的字典
        """
        image_paths = glob_module.glob(pattern)
        
        if not image_paths:
            return {"success": False, "error": f"没有找到匹配 '{pattern}' 的图片"}
        
        if sort_by == "name":
            image_paths.sort()
        elif sort_by == "time":
            image_paths.sort(key=lambda x: os.path.getmtime(x))
        
        print(f"找到 {len(image_paths)} 张图片:")
        for i, p in enumerate(image_paths, 1):
            print(f"  {i}. {os.path.basename(p)}")
        
        return self.merge(image_paths, output_path, gap, background_color, blend)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='长图拼接工具 - 将多张图片垂直拼接成微信长图',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 拼接指定图片
  python merge_long_image.py img1.png img2.png img3.png -o output.png
  
  # 使用通配符匹配
  python merge_long_image.py -p "generated_*.png" -o long_image.png
  
  # 指定宽度和间隔
  python merge_long_image.py -p "*.png" -o out.png -w 750 -g 20
  
  # 按修改时间排序
  python merge_long_image.py -p "*.png" -o out.png --sort time
  
  # 启用接缝融合过渡（推荐40px）
  python merge_long_image.py img1.png img2.png -o out.png --blend 40
        """
    )
    
    parser.add_argument('images', nargs='*', help='要拼接的图片路径列表')
    parser.add_argument('-p', '--pattern', help='glob 模式匹配图片，如 "*.png"')
    parser.add_argument('-o', '--output', required=True, help='输出文件路径')
    parser.add_argument('-w', '--width', type=int, default=1080, help='目标宽度，默认1080')
    parser.add_argument('-g', '--gap', type=int, default=0, help='图片间隔像素，默认0')
    parser.add_argument('--sort', choices=['name', 'time', 'none'], default='name', 
                        help='排序方式：name(文件名)/time(修改时间)/none')
    parser.add_argument('--bg', default='white', help='背景颜色，默认 white')
    parser.add_argument('--blend', type=int, default=0, 
                        help='接缝融合过渡高度（像素），推荐30-50，默认0不融合')
    
    args = parser.parse_args()
    
    if not args.images and not args.pattern:
        parser.error("请提供图片路径列表或使用 -p 指定匹配模式")
    
    merger = LongImageMerger(target_width=args.width)
    
    if args.pattern:
        result = merger.merge_from_pattern(
            pattern=args.pattern,
            output_path=args.output,
            sort_by=args.sort,
            gap=args.gap,
            background_color=args.bg,
            blend=args.blend
        )
    else:
        result = merger.merge(
            image_paths=args.images,
            output_path=args.output,
            gap=args.gap,
            background_color=args.bg,
            blend=args.blend
        )
    
    if result["success"]:
        print(f"\n拼接成功！")
        print(f"输出文件: {result['saved_path']}")
        print(f"尺寸: {result['width']} x {result['height']}")
        print(f"共 {result['image_count']} 张图片")
    else:
        print(f"\n拼接失败: {result['error']}")


if __name__ == "__main__":
    main()
