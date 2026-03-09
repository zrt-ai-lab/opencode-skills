#!/usr/bin/env python3
"""
信息图生成器 (zlab Infographic Generator)
支持 20 种布局 × 17 种风格 = 340 种组合
底层调用 core/text_to_image.py

Author: 翟星人
"""

import argparse
import json
import subprocess
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
SKILL_DIR = BASE_DIR.parent.parent
CORE_SCRIPT = SKILL_DIR / "core" / "text_to_image.py"
LAYOUTS_FILE = BASE_DIR / "layouts.json"
STYLES_FILE = BASE_DIR / "styles.json"


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def list_options(layouts, styles):
    print("=== 可用布局 (20种) ===\n")
    for key, layout in layouts.items():
        print(f"  {key:20s} {layout['name']:8s} — {layout['best_for']}")
    print(f"\n=== 可用风格 (17种) ===\n")
    for key, style in styles.items():
        print(f"  {key:20s} {style['name']:8s} — {style['description']}")
    print(f"\n共 {len(layouts)} × {len(styles)} = {len(layouts) * len(styles)} 种组合")


def build_prompt(title, content, layout_def, style_def):
    """组装完整提示词"""
    prompt_parts = [
        f"专业信息图，{layout_def['name']}布局",
        layout_def['prompt_hint'],
        f"大标题「{title}」放在画面顶部居中位置，字号醒目",
        f"信息内容：{content}",
        style_def['prompt_suffix'],
        "所有文字使用中文，标注清晰可读，笔画完整无乱码。信息层级分明，主次有序。配色协调统一，不超过3-4种主色。高清晰度，专业信息图设计水准"
    ]
    return "。".join(prompt_parts)


def generate(title, content, layout, style, ratio, output):
    layouts = load_json(LAYOUTS_FILE)['layouts']
    styles = load_json(STYLES_FILE)['styles']

    if layout not in layouts:
        print(f"错误: 未知布局 '{layout}'")
        print(f"可用: {', '.join(layouts.keys())}")
        sys.exit(1)

    if style not in styles:
        print(f"错误: 未知风格 '{style}'")
        print(f"可用: {', '.join(styles.keys())}")
        sys.exit(1)

    layout_def = layouts[layout]
    style_def = styles[style]
    prompt = build_prompt(title, content, layout_def, style_def)

    print(f"📊 信息图生成")
    print(f"   布局: {layout_def['name']} ({layout})")
    print(f"   风格: {style_def['name']} ({style})")
    print(f"   比例: {ratio}")
    print(f"   输出: {output}")
    print(f"   提示词: {prompt[:100]}...")

    cmd = [
        sys.executable,
        str(CORE_SCRIPT),
        prompt,
        "-r", ratio,
        "-o", output
    ]

    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print("生成失败")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="zlab 信息图生成器 — 20种布局 × 17种风格",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 金字塔 + 手绘风
  python zlab_infographic.py -l pyramid -s craft-handmade -n "AI技术栈" -c "顶层AGI，中层大模型，底层算力" -o ai_stack.png

  # 鱼骨图 + 技术蓝图风
  python zlab_infographic.py -l fishbone -s technical -n "性能瓶颈分析" -c "CPU、内存、IO、网络四大分支" -o perf.png

  # 韦恩图 + 水彩风
  python zlab_infographic.py -l venn -s watercolor -n "全栈工程师" -c "前端、后端、DevOps三圈交集" -o fullstack.png

  # 查看所有布局和风格
  python zlab_infographic.py --list
        """
    )

    parser.add_argument("-l", "--layout", help="布局类型（20种可选，用 --list 查看）")
    parser.add_argument("-s", "--style", default="craft-handmade", help="视觉风格（17种可选，默认 craft-handmade）")
    parser.add_argument("-n", "--name", help="信息图标题")
    parser.add_argument("-c", "--content", help="信息图内容描述")
    parser.add_argument("-r", "--ratio", default="16:9", help="宽高比（默认 16:9）")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("--list", action="store_true", help="列出所有布局和风格")

    args = parser.parse_args()

    if args.list:
        layouts = load_json(LAYOUTS_FILE)['layouts']
        styles = load_json(STYLES_FILE)['styles']
        list_options(layouts, styles)
        return

    if not all([args.layout, args.name, args.content, args.output]):
        parser.print_help()
        print("\n错误: 必须提供 -l, -n, -c, -o 参数")
        sys.exit(1)

    generate(args.name, args.content, args.layout, args.style, args.ratio, args.output)


if __name__ == "__main__":
    main()
