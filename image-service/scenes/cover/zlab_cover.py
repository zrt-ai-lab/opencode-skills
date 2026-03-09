#!/usr/bin/env python3
"""
封面图生成器 (zlab Cover Image Generator)
五维定制系统：类型 × 配色 × 渲染 × 文字 × 氛围
底层调用 core/text_to_image.py

Author: 翟星人
"""

import argparse
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
CORE_SCRIPT = SKILL_DIR / "core" / "text_to_image.py"

# === 五维定义 ===

TYPES = {
    "hero": {"name": "主视觉", "hint": "大气主视觉构图，核心元素居中，视觉冲击力强"},
    "conceptual": {"name": "概念隐喻", "hint": "概念隐喻画面，用视觉符号表达抽象主题"},
    "typography": {"name": "文字排版", "hint": "以文字排版为主的设计，字体艺术化处理"},
    "metaphor": {"name": "视觉比喻", "hint": "具象物体比喻抽象概念，创意视觉表达"},
    "scene": {"name": "场景氛围", "hint": "环境场景渲染，营造沉浸式氛围"},
    "minimal": {"name": "极简留白", "hint": "大面积留白，极简元素点缀，高级感构图"},
}

PALETTES = {
    "warm": {"name": "暖色调", "hint": "暖色调配色，橙红金黄，温暖活力"},
    "elegant": {"name": "优雅", "hint": "优雅配色，低饱和度，灰粉米白，高级质感"},
    "cool": {"name": "冷色调", "hint": "冷色调配色，蓝绿青灰，理性冷静"},
    "dark": {"name": "深色", "hint": "深色系配色，深蓝黑灰，高端神秘"},
    "earth": {"name": "大地色", "hint": "大地色系，棕褐橄榄，自然质朴"},
    "vivid": {"name": "鲜艳", "hint": "高饱和鲜艳配色，强对比撞色，活力四射"},
    "pastel": {"name": "粉彩", "hint": "粉彩马卡龙配色，柔和梦幻"},
    "mono": {"name": "单色", "hint": "单色系配色，同一色相的深浅变化，统一纯净"},
    "retro": {"name": "复古", "hint": "复古做旧配色，怀旧暖黄，胶片质感"},
}

RENDERINGS = {
    "flat-vector": {"name": "扁平矢量", "hint": "扁平矢量插画风格，纯色块填充，简洁线条"},
    "hand-drawn": {"name": "手绘", "hint": "手绘插画风格，线条有手工质感，温暖亲切"},
    "painterly": {"name": "绘画", "hint": "油画/丙烯绘画风格，笔触可见，艺术感强"},
    "digital": {"name": "数字渲染", "hint": "数字3D渲染风格，光影精致，质感细腻"},
    "pixel": {"name": "像素", "hint": "像素艺术风格，8-bit复古感"},
    "chalk": {"name": "粉笔", "hint": "粉笔画风格，黑板或深色纸张背景，粉笔纹理"},
}

TEXT_MODES = {
    "none": {"name": "无文字", "hint": "纯视觉画面，不包含任何文字"},
    "title-only": {"name": "仅标题", "hint": "画面中包含主标题文字，醒目位置"},
    "title-subtitle": {"name": "标题+副标题", "hint": "包含主标题和副标题文字"},
    "text-rich": {"name": "文字丰富", "hint": "包含较多文字内容，标题+副标题+要点"},
}

MOODS = {
    "subtle": {"name": "含蓄", "hint": "含蓄克制的氛围，留白多，呼吸感强"},
    "balanced": {"name": "均衡", "hint": "均衡的视觉表达，不过于张扬也不过于克制"},
    "bold": {"name": "大胆", "hint": "大胆张扬的视觉冲击，高对比，强烈表达"},
}


def build_prompt(title, subtitle, type_key, palette_key, rendering_key, text_key, mood_key):
    parts = [
        f"专业文章封面图，横版16:9构图",
        TYPES[type_key]['hint'],
        PALETTES[palette_key]['hint'],
        RENDERINGS[rendering_key]['hint'],
        MOODS[mood_key]['hint'],
    ]
    if text_key != "none":
        parts.append(f"画面中包含中文标题「{title}」，字号大而醒目，放在画面视觉中心或黄金分割位置")
        if subtitle and text_key in ("title-subtitle", "text-rich"):
            parts.append(f"副标题「{subtitle}」放在主标题下方，字号较小")
        parts.append(TEXT_MODES[text_key]['hint'])
        parts.append("标题文字清晰可读，笔画完整无乱码，与背景有足够对比度")
    else:
        parts.append(f"主题：{title}，用视觉元素表达主题意境，不含文字")

    parts.append("构图平衡，主体突出，背景不喧宾夺主。高清晰度，专业封面设计水准，适合公众号/博客头图")
    return "，".join(parts)


def generate(title, subtitle, type_key, palette_key, rendering_key, text_key, mood_key, ratio, output):
    prompt = build_prompt(title, subtitle, type_key, palette_key, rendering_key, text_key, mood_key)

    print(f"🖼️ 封面图生成")
    print(f"   类型: {TYPES[type_key]['name']} ({type_key})")
    print(f"   配色: {PALETTES[palette_key]['name']} ({palette_key})")
    print(f"   渲染: {RENDERINGS[rendering_key]['name']} ({rendering_key})")
    print(f"   文字: {TEXT_MODES[text_key]['name']} ({text_key})")
    print(f"   氛围: {MOODS[mood_key]['name']} ({mood_key})")
    print(f"   比例: {ratio}")
    print(f"   输出: {output}")

    cmd = [sys.executable, str(CORE_SCRIPT), prompt, "-r", ratio, "-o", output]
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print("生成失败")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="zlab 封面图生成器 — 五维定制系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 自动选择（只需标题）
  python zlab_cover.py -n "AI Agent的前世今生"

  # 指定维度
  python zlab_cover.py -n "深入AI Agent" --type conceptual --palette dark --rendering digital

  # 带副标题
  python zlab_cover.py -n "Prompt工程" --subtitle "从入门到精通" --text title-subtitle

  # 极简风封面
  python zlab_cover.py -n "极简主义" --type minimal --palette mono --mood subtle -o cover.png
        """
    )
    parser.add_argument("-n", "--name", required=True, help="文章/封面标题")
    parser.add_argument("--subtitle", help="副标题")
    parser.add_argument("--type", default="hero", choices=TYPES.keys(), help="类型（默认 hero）")
    parser.add_argument("--palette", default="cool", choices=PALETTES.keys(), help="配色（默认 cool）")
    parser.add_argument("--rendering", default="flat-vector", choices=RENDERINGS.keys(), help="渲染风格（默认 flat-vector）")
    parser.add_argument("--text", default="title-only", choices=TEXT_MODES.keys(), help="文字模式（默认 title-only）")
    parser.add_argument("--mood", default="balanced", choices=MOODS.keys(), help="氛围（默认 balanced）")
    parser.add_argument("-r", "--ratio", default="16:9", help="宽高比（默认 16:9）")
    parser.add_argument("-o", "--output", help="输出文件路径")

    args = parser.parse_args()
    output = args.output or f"cover_{args.name[:10]}.png"
    generate(args.name, args.subtitle, args.type, args.palette, args.rendering, args.text, args.mood, args.ratio, output)


if __name__ == "__main__":
    main()
