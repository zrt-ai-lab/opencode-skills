#!/usr/bin/env python3
"""
小红书信息图生成器 (zlab XHS Images Generator)
将内容拆解为1-10张卡片风格信息图
风格 × 布局 二维系统

Author: 翟星人
"""

import argparse
import subprocess
import sys
import re
import os
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
CORE_T2I = SKILL_DIR / "core" / "text_to_image.py"
CORE_I2I = SKILL_DIR / "core" / "image_to_image.py"

# === 风格（视觉美学）===

XHS_STYLES = {
    "cute": {
        "name": "可爱卡通",
        "prompt": "可爱卡通风格，圆润造型，大眼睛表情包元素，粉色黄色为主，手绘贴纸感"
    },
    "fresh": {
        "name": "清新自然",
        "prompt": "清新自然风格，薄荷绿和天蓝为主，植物叶子装饰，干净白色背景"
    },
    "warm": {
        "name": "温暖治愈",
        "prompt": "温暖治愈风格，暖黄暖橙色调，柔和光线，毛绒质感，慵懒氛围"
    },
    "bold": {
        "name": "大胆撞色",
        "prompt": "大胆撞色风格，高饱和荧光色，强对比色块拼接，视觉冲击力强"
    },
    "minimal": {
        "name": "极简",
        "prompt": "极简风格，黑白灰为主，极少装饰，大面积留白，高级感"
    },
    "retro": {
        "name": "复古",
        "prompt": "复古风格，做旧纸张纹理，泛黄色调，老照片胶片感"
    },
    "pop": {
        "name": "波普",
        "prompt": "波普艺术风格，漫画网点效果，鲜艳原色，粗黑轮廓线"
    },
    "notion": {
        "name": "Notion风",
        "prompt": "Notion简约风格，白色背景，极简线条图标，黑色文字，少量色彩标注"
    },
    "chalkboard": {
        "name": "粉笔黑板",
        "prompt": "粉笔黑板风格，深绿色黑板背景，彩色粉笔手绘，温馨文艺"
    },
}

# === 布局（信息密度）===

XHS_LAYOUTS = {
    "sparse": {
        "name": "稀疏",
        "points": "1-2点",
        "prompt": "稀疏布局，画面中央1到2个大字核心观点，大面积留白",
        "best_for": "封面、金句"
    },
    "balanced": {
        "name": "均衡",
        "points": "3-4点",
        "prompt": "均衡布局，3到4个要点，图文搭配，阅读舒适",
        "best_for": "常规内容"
    },
    "dense": {
        "name": "密集",
        "points": "5-8点",
        "prompt": "密集布局，5到8个要点紧凑排列，知识卡片感，信息量大",
        "best_for": "干货总结"
    },
    "list": {
        "name": "列表",
        "points": "4-7项",
        "prompt": "列表布局，4到7个条目纵向排列，编号或图标标注，清单感",
        "best_for": "清单、排行"
    },
    "comparison": {
        "name": "对比",
        "points": "双栏",
        "prompt": "双栏对比布局，左右分区，中间VS分隔，对比鲜明",
        "best_for": "对比、优劣"
    },
    "flow": {
        "name": "流程",
        "points": "3-6步",
        "prompt": "流程布局，3到6个步骤，箭头连接，从上到下或从左到右",
        "best_for": "教程、流程"
    },
}


def split_content_to_cards(content, layout, max_cards=10):
    """将内容拆分为多张卡片"""
    cards = []

    # 按段落拆
    paragraphs = [p.strip() for p in re.split(r'\n{2,}', content.strip()) if p.strip()]

    # 提取h2/h3标题段
    sections = []
    current = {"title": "", "body": ""}
    for para in paragraphs:
        h_match = re.match(r'^#{1,3}\s+(.+)$', para)
        if h_match:
            if current["title"] or current["body"]:
                sections.append(current)
            current = {"title": h_match.group(1), "body": ""}
        else:
            current["body"] += para + "\n"
    if current["title"] or current["body"]:
        sections.append(current)

    if not sections:
        # 没有标题结构，按段落直接分
        sections = [{"title": f"第{i+1}张", "body": p} for i, p in enumerate(paragraphs)]

    # 第1张：封面
    if sections:
        first = sections[0]
        cards.append({
            "type": "cover",
            "title": first["title"] or "封面",
            "body": first["body"][:100]
        })

    # 中间内容卡片
    for sec in sections[1:]:
        if len(cards) >= max_cards - 1:
            break
        cards.append({
            "type": "content",
            "title": sec["title"],
            "body": sec["body"][:200]
        })

    return cards


def build_xhs_prompt(card, card_num, total, style_def, layout_def):
    """构建单张小红书图的提示词"""
    card_type_hint = {
        "cover": "小红书封面卡片。标题特大号字居中偏上，视觉冲击力强，吸引点击。下方可配1-2行副标题或关键词标签。背景有风格化装饰但不喧宾夺主",
        "content": "小红书内容卡片。顶部放小标题，下方将知识点用图标+文字或编号列表清晰展示。信息密度适中，每条要点配小图标辅助理解。底部留出翻页提示空间",
    }

    parts = [
        f"小红书信息图卡片，第{card_num}张（共{total}张），竖版3:4比例",
        card_type_hint.get(card["type"], card_type_hint["content"]),
        style_def['prompt'],
        layout_def['prompt'],
        f"标题内容：「{card['title']}」",
    ]

    if card["body"]:
        parts.append(f"卡片展示的信息：{card['body'][:150]}")

    parts.append("中文排版，文字清晰可读笔画完整。卡片四周留出安全边距，不贴边。整体视觉统一，适合小红书竖屏浏览")
    return "，".join(parts)


def generate_xhs(source_path, style, layout, output_dir, max_cards):
    """主生成流程"""
    if style not in XHS_STYLES:
        print(f"错误: 未知风格 '{style}'，可用: {', '.join(XHS_STYLES.keys())}")
        sys.exit(1)
    if layout not in XHS_LAYOUTS:
        print(f"错误: 未知布局 '{layout}'，可用: {', '.join(XHS_LAYOUTS.keys())}")
        sys.exit(1)

    style_def = XHS_STYLES[style]
    layout_def = XHS_LAYOUTS[layout]

    # 读取内容
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 拆分卡片
    cards = split_content_to_cards(content, layout, max_cards)

    print(f"📱 小红书图生成")
    print(f"   风格: {style_def['name']} ({style})")
    print(f"   布局: {layout_def['name']} ({layout})，{layout_def['points']}")
    print(f"   张数: {len(cards)}")
    print(f"   输出: {output_dir}/")
    print()

    # 大纲
    print("=== 卡片规划 ===")
    for i, card in enumerate(cards, 1):
        print(f"  第{i}张 [{card['type']}] {card['title']}")
    print()

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 串行生成（参考上一张保持风格一致）
    prev_path = None
    for i, card in enumerate(cards, 1):
        prompt = build_xhs_prompt(card, i, len(cards), style_def, layout_def)
        output_path = os.path.join(output_dir, f"xhs_{i:02d}.png")

        print(f"  生成第{i}/{len(cards)}张: {card['title']}")

        if i == 1 or prev_path is None:
            cmd = [sys.executable, str(CORE_T2I), prompt, "-r", "3:4", "-o", output_path]
        else:
            ref_prompt = f"参考模板图的配色、风格和排版，保持系列一致性。{prompt}"
            cmd = [sys.executable, str(CORE_I2I), prev_path, ref_prompt, "-r", "3:4", "-o", output_path]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    ⚠️ 失败: {result.stderr[:200]}")
        else:
            print(f"    ✅ {output_path}")
            prev_path = output_path

    print(f"\n全部完成！{len(cards)}张小红书图已保存到 {output_dir}/")


def list_options():
    print("=== 风格 (9种) ===\n")
    for k, v in XHS_STYLES.items():
        print(f"  {k:15s} {v['name']}")
    print("\n=== 布局 (6种) ===\n")
    for k, v in XHS_LAYOUTS.items():
        print(f"  {k:15s} {v['name']:6s} {v['points']:8s} — {v['best_for']}")
    print(f"\n共 {len(XHS_STYLES)} × {len(XHS_LAYOUTS)} = {len(XHS_STYLES)*len(XHS_LAYOUTS)} 种组合")


def main():
    parser = argparse.ArgumentParser(
        description="zlab 小红书信息图生成器 — 9风格 × 6布局",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 可爱风 + 均衡布局
  python zlab_xhs_images.py article.md --style cute --layout balanced -o xhs/

  # Notion风 + 密集布局
  python zlab_xhs_images.py article.md --style notion --layout dense -o xhs/

  # 查看选项
  python zlab_xhs_images.py --list
        """
    )
    parser.add_argument("source", nargs="?", help="内容文件路径")
    parser.add_argument("--style", default="cute", choices=XHS_STYLES.keys(), help="风格（默认 cute）")
    parser.add_argument("--layout", default="balanced", choices=XHS_LAYOUTS.keys(), help="布局（默认 balanced）")
    parser.add_argument("-o", "--output", default="xhs", help="输出目录（默认 xhs/）")
    parser.add_argument("--cards", type=int, default=10, help="最大卡片数（默认 10）")
    parser.add_argument("--list", action="store_true", help="列出所有选项")

    args = parser.parse_args()

    if args.list:
        list_options()
        return

    if not args.source:
        parser.print_help()
        print("\n错误: 请提供内容文件路径")
        sys.exit(1)

    if not os.path.exists(args.source):
        print(f"错误: 文件不存在 {args.source}")
        sys.exit(1)

    generate_xhs(args.source, args.style, args.layout, args.output, args.cards)


if __name__ == "__main__":
    main()
