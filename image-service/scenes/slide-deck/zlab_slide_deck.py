#!/usr/bin/env python3
"""
幻灯片图生成器 (zlab Slide Deck Generator)
从Markdown内容生成专业幻灯片图片
4维度组合：纹理 × 氛围 × 字体 × 密度，16种预设

Author: 翟星人
"""

import argparse
import subprocess
import sys
import re
import os
import time
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
CORE_SCRIPT = SKILL_DIR / "core" / "text_to_image.py"

# === 4维度定义 ===

TEXTURES = {
    "clean": "纯净平滑背景，无纹理干扰",
    "grid": "细微网格背景，技术感",
    "organic": "有机纹理，自然柔和的肌理",
    "pixel": "像素化纹理，数字复古感",
    "paper": "纸张纹理，手工质感",
}

ATMOSPHERES = {
    "professional": "专业商务氛围，克制沉稳",
    "warm": "温暖友好氛围，亲和力强",
    "cool": "冷静理性氛围，蓝灰色调",
    "vibrant": "鲜艳活力氛围，高饱和配色",
    "dark": "深色暗色氛围，神秘高端",
    "neutral": "中性氛围，灰白为主，不偏不倚",
}

FONTS = {
    "geometric": "几何感字体风格，现代简洁",
    "humanist": "人文主义字体风格，优雅可读",
    "handwritten": "手写体风格，亲切随意",
    "editorial": "编辑出版字体风格，杂志感",
    "technical": "技术等宽字体风格，代码感",
}

DENSITIES = {
    "minimal": "极简信息密度，大面积留白，每页1-2个要点",
    "balanced": "均衡信息密度，图文搭配，每页3-4个要点",
    "dense": "高信息密度，知识卡片感，每页5-8个要点",
}

# === 16种预设 ===

PRESETS = {
    "blueprint": {
        "name": "技术蓝图",
        "texture": "grid", "atmosphere": "cool", "font": "technical", "density": "balanced",
        "best_for": "架构设计、系统设计"
    },
    "chalkboard": {
        "name": "粉笔黑板",
        "texture": "organic", "atmosphere": "warm", "font": "handwritten", "density": "balanced",
        "best_for": "教育、教程"
    },
    "corporate": {
        "name": "商务专业",
        "texture": "clean", "atmosphere": "professional", "font": "geometric", "density": "balanced",
        "best_for": "投资者演示、提案"
    },
    "minimal": {
        "name": "极简",
        "texture": "clean", "atmosphere": "neutral", "font": "geometric", "density": "minimal",
        "best_for": "高管简报"
    },
    "notion": {
        "name": "Notion风",
        "texture": "clean", "atmosphere": "neutral", "font": "geometric", "density": "dense",
        "best_for": "产品演示、SaaS"
    },
    "dark-atmospheric": {
        "name": "暗色氛围",
        "texture": "clean", "atmosphere": "dark", "font": "editorial", "density": "balanced",
        "best_for": "娱乐、游戏"
    },
    "bold-editorial": {
        "name": "大胆编辑",
        "texture": "clean", "atmosphere": "vibrant", "font": "editorial", "density": "balanced",
        "best_for": "产品发布、主题演讲"
    },
    "pixel-art": {
        "name": "像素艺术",
        "texture": "pixel", "atmosphere": "vibrant", "font": "technical", "density": "balanced",
        "best_for": "游戏、开发者"
    },
    "scientific": {
        "name": "科学学术",
        "texture": "clean", "atmosphere": "cool", "font": "technical", "density": "dense",
        "best_for": "生物、化学、医学"
    },
    "sketch-notes": {
        "name": "手绘笔记",
        "texture": "organic", "atmosphere": "warm", "font": "handwritten", "density": "balanced",
        "best_for": "教育、教程"
    },
    "watercolor": {
        "name": "水彩",
        "texture": "organic", "atmosphere": "warm", "font": "humanist", "density": "minimal",
        "best_for": "生活方式、健康"
    },
    "editorial-infographic": {
        "name": "编辑信息图",
        "texture": "clean", "atmosphere": "cool", "font": "editorial", "density": "dense",
        "best_for": "科技解说、研究"
    },
    "fantasy-animation": {
        "name": "幻想动画",
        "texture": "organic", "atmosphere": "vibrant", "font": "handwritten", "density": "minimal",
        "best_for": "教育故事"
    },
    "vector-illustration": {
        "name": "矢量插画",
        "texture": "clean", "atmosphere": "vibrant", "font": "humanist", "density": "balanced",
        "best_for": "创意、儿童内容"
    },
    "vintage": {
        "name": "复古",
        "texture": "paper", "atmosphere": "warm", "font": "editorial", "density": "balanced",
        "best_for": "历史、传记"
    },
    "intuition-machine": {
        "name": "机器直觉",
        "texture": "clean", "atmosphere": "cool", "font": "technical", "density": "dense",
        "best_for": "技术文档、学术"
    },
}


def parse_markdown_to_slides(md_content, max_slides=20):
    """将Markdown内容拆分为幻灯片页"""
    slides = []

    # 按h2拆分
    sections = re.split(r'^## ', md_content, flags=re.MULTILINE)

    # 第一段作为标题页
    if sections[0].strip():
        # 提取h1标题
        h1_match = re.search(r'^# (.+)$', sections[0], re.MULTILINE)
        title = h1_match.group(1).strip() if h1_match else "标题页"
        body = re.sub(r'^# .+$', '', sections[0], flags=re.MULTILINE).strip()
        slides.append({"type": "title", "title": title, "body": body[:200]})

    # 后续章节
    for section in sections[1:]:
        lines = section.strip().split('\n')
        if not lines:
            continue
        sec_title = lines[0].strip()
        sec_body = '\n'.join(lines[1:]).strip()

        # 提取要点（列表项）
        points = re.findall(r'^[-*]\s+(.+)$', sec_body, re.MULTILINE)
        body_summary = '\n'.join(f"- {p}" for p in points[:6]) if points else sec_body[:300]

        slides.append({"type": "content", "title": sec_title, "body": body_summary})

        if len(slides) >= max_slides:
            break

    # 确保有结尾页
    if slides and slides[-1]["type"] != "ending":
        slides.append({"type": "ending", "title": "谢谢", "body": "感谢观看"})

    return slides


def build_slide_prompt(slide, slide_num, total, preset_def):
    """为单页幻灯片构建生图提示词"""
    texture = TEXTURES[preset_def['texture']]
    atmosphere = ATMOSPHERES[preset_def['atmosphere']]
    font_style = FONTS[preset_def['font']]
    density = DENSITIES[preset_def['density']]

    slide_type_hint = {
        "title": "演示文稿标题页。大字标题居中偏上，字号最大最醒目。副标题或作者信息在下方较小字号。背景简洁大气，主体元素不超过3个",
        "content": "演示文稿内容页。标题在顶部左对齐或居中（字号适中加粗），下方内容区域清晰排布要点。要点可用编号或图标列表，行距宽松易读。可配一个辅助图形/图标在右侧或下方",
        "ending": "演示文稿结尾页。感谢语或总结语居中放大，简洁收尾。可配一个简约图标或装饰元素。整体留白多，不拥挤",
    }

    type_hint = slide_type_hint.get(slide["type"], slide_type_hint["content"])

    parts = [
        f"专业演示文稿幻灯片，第{slide_num}页（共{total}页），16:9宽屏横版",
        type_hint,
        f"标题内容：「{slide['title']}」",
    ]

    if slide["body"]:
        # 截取关键内容
        body_short = slide["body"][:200]
        parts.append(f"内容要点：{body_short}")

    parts.extend([
        texture,
        atmosphere,
        font_style,
        density,
        "中文排版，所有文字清晰可读笔画完整。版式专业整洁，对齐规整。配色不超过3种主色，主次分明。16:9宽屏比例，适合投屏演示",
    ])

    return "，".join(parts)


def generate_slides(md_path, preset_name, max_slides, output_dir, ratio, outline_only=False):
    """主生成流程"""
    if preset_name not in PRESETS:
        print(f"错误: 未知预设 '{preset_name}'")
        print(f"可用: {', '.join(PRESETS.keys())}")
        sys.exit(1)

    preset_def = PRESETS[preset_name]

    # 读取Markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # 拆分为幻灯片
    slides = parse_markdown_to_slides(md_content, max_slides)
    print(f"📑 幻灯片生成")
    print(f"   预设: {preset_def['name']} ({preset_name})")
    print(f"   页数: {len(slides)}")
    print(f"   输出: {output_dir}/")
    print()

    # 输出大纲
    print("=== 大纲 ===")
    for i, slide in enumerate(slides, 1):
        print(f"  第{i}页 [{slide['type']}] {slide['title']}")
    print()

    if outline_only:
        print("（仅大纲模式，跳过图片生成）")
        return

    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 逐页生成
    for i, slide in enumerate(slides, 1):
        prompt = build_slide_prompt(slide, i, len(slides), preset_def)
        output_path = os.path.join(output_dir, f"slide_{i:02d}.png")

        print(f"  生成第{i}/{len(slides)}页: {slide['title']}")
        cmd = [sys.executable, str(CORE_SCRIPT), prompt, "-r", ratio, "-o", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    ⚠️ 第{i}页生成失败: {result.stderr[:200]}")
        else:
            print(f"    ✅ {output_path}")

    print(f"\n全部完成！{len(slides)}页幻灯片已保存到 {output_dir}/")


def list_presets():
    print("=== 可用预设 (16种) ===\n")
    for key, preset in PRESETS.items():
        dims = f"{preset['texture']}×{preset['atmosphere']}×{preset['font']}×{preset['density']}"
        print(f"  {key:25s} {preset['name']:8s} — {preset['best_for']}")
        print(f"  {'':25s} ({dims})")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="zlab 幻灯片图生成器 — 16种预设风格",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从Markdown生成幻灯片
  python zlab_slide_deck.py article.md --style blueprint -o slides/

  # 仅看大纲
  python zlab_slide_deck.py article.md --outline-only

  # 指定页数上限
  python zlab_slide_deck.py article.md --style corporate --slides 12 -o slides/

  # 查看所有预设
  python zlab_slide_deck.py --list
        """
    )
    parser.add_argument("markdown", nargs="?", help="Markdown文件路径")
    parser.add_argument("--style", default="blueprint", help="预设风格（默认 blueprint，用 --list 查看）")
    parser.add_argument("--slides", type=int, default=20, help="最大页数（默认 20）")
    parser.add_argument("-r", "--ratio", default="16:9", help="宽高比（默认 16:9）")
    parser.add_argument("-o", "--output", default="slides", help="输出目录（默认 slides/）")
    parser.add_argument("--outline-only", action="store_true", help="仅输出大纲，不生成图片")
    parser.add_argument("--list", action="store_true", help="列出所有预设")

    args = parser.parse_args()

    if args.list:
        list_presets()
        return

    if not args.markdown:
        parser.print_help()
        print("\n错误: 请提供Markdown文件路径")
        sys.exit(1)

    if not os.path.exists(args.markdown):
        print(f"错误: 文件不存在 {args.markdown}")
        sys.exit(1)

    generate_slides(args.markdown, args.style, args.slides, args.output, args.ratio, args.outline_only)


if __name__ == "__main__":
    main()
