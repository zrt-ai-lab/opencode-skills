#!/usr/bin/env python3
"""
智能文章插图生成器 (zlab Article Illustrator)
分析文章结构，识别需要配图的位置，自动生成插图
类型 × 风格 二维系统

Author: 翟星人
"""

import argparse
import subprocess
import sys
import re
import os
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent.parent
CORE_SCRIPT = SKILL_DIR / "core" / "text_to_image.py"

# === 类型（信息结构）===

TYPES = {
    "infographic": {
        "name": "数据可视化",
        "prompt": "数据可视化信息图，图表、指标、数据展示",
        "trigger_words": ["数据", "统计", "增长", "比例", "百分比", "趋势"]
    },
    "scene": {
        "name": "氛围插图",
        "prompt": "氛围场景插图，情绪渲染，画面感强",
        "trigger_words": ["场景", "想象", "故事", "经历", "感受"]
    },
    "flowchart": {
        "name": "流程图",
        "prompt": "流程步骤可视化，从左到右或从上到下，箭头连接",
        "trigger_words": ["步骤", "流程", "首先", "然后", "最后", "过程"]
    },
    "comparison": {
        "name": "对比图",
        "prompt": "左右并排对比，突出差异，双栏布局",
        "trigger_words": ["对比", "vs", "区别", "不同", "相比", "优劣"]
    },
    "framework": {
        "name": "概念图",
        "prompt": "概念关系图，节点连线，结构化展示",
        "trigger_words": ["架构", "框架", "模型", "体系", "核心", "组成"]
    },
    "timeline": {
        "name": "时间线",
        "prompt": "时间线进展图，横向或纵向轴线，节点标注",
        "trigger_words": ["历史", "阶段", "发展", "演进", "里程碑", "版本"]
    },
}

# === 风格（视觉美学）===

STYLES = {
    "notion": {
        "name": "极简线条",
        "prompt": "极简手绘线条画风格，黑色细线条，少量色彩点缀，白色背景，干净简洁"
    },
    "elegant": {
        "name": "精致优雅",
        "prompt": "精致优雅风格，低饱和配色，细腻渐变，高级质感，留白构图"
    },
    "warm": {
        "name": "友好亲切",
        "prompt": "友好温暖风格，暖色调，圆润造型，亲切感，柔和光线"
    },
    "minimal": {
        "name": "极简禅意",
        "prompt": "极简禅意风格，大面积留白，极少元素，呼吸感强，克制优雅"
    },
    "blueprint": {
        "name": "技术蓝图",
        "prompt": "技术蓝图风格，深蓝背景白色线条，网格坐标，工程制图感"
    },
    "watercolor": {
        "name": "水彩艺术",
        "prompt": "水彩画风格，柔和晕染，颜色自然渗透，艺术感强"
    },
    "editorial": {
        "name": "杂志编辑",
        "prompt": "杂志编辑风格，专业排版感，信息图设计，高对比清晰"
    },
    "scientific": {
        "name": "学术精确",
        "prompt": "学术精确图表风格，数据标注精确，刻度清晰，论文级严谨"
    },
}


def analyze_article(md_content):
    """分析文章结构，识别需要配图的段落"""
    sections = []
    current_title = ""
    current_body = ""

    for line in md_content.split('\n'):
        # h2/h3标题
        h_match = re.match(r'^(#{2,3})\s+(.+)$', line)
        if h_match:
            if current_title and current_body:
                sections.append({"title": current_title, "body": current_body.strip()})
            current_title = h_match.group(2)
            current_body = ""
        else:
            current_body += line + "\n"

    if current_title and current_body:
        sections.append({"title": current_title, "body": current_body.strip()})

    # 为每个章节推荐插图类型
    results = []
    for section in sections:
        text = section["title"] + " " + section["body"]
        best_type = "infographic"  # 默认
        best_score = 0

        for type_key, type_def in TYPES.items():
            score = sum(1 for word in type_def["trigger_words"] if word in text)
            if score > best_score:
                best_score = score
                best_type = type_key

        # 只为有足够内容的章节生成插图（>50字）
        if len(section["body"]) > 50:
            results.append({
                "title": section["title"],
                "body": section["body"][:300],
                "recommended_type": best_type,
                "confidence": best_score,
            })

    return results


def build_illust_prompt(section, type_key, style_key):
    """构建插图提示词"""
    type_def = TYPES[type_key]
    style_def = STYLES[style_key]

    parts = [
        f"文章配图插图，16:9横版",
        type_def['prompt'],
        f"图解主题：「{section['title']}」",
        f"需要可视化的内容：{section['body'][:200]}",
        style_def['prompt'],
        "所有标注使用中文，文字清晰可读。构图简洁明了，信息层次分明。配色与文章风格协调，不喧宾夺主。适合嵌入Markdown文章中阅读",
    ]
    return "，".join(parts)


def generate_illustrations(md_path, style, ratio, output_dir, type_override=None):
    """主生成流程"""
    if style not in STYLES:
        print(f"错误: 未知风格 '{style}'，可用: {', '.join(STYLES.keys())}")
        sys.exit(1)

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    sections = analyze_article(md_content)

    if not sections:
        print("文章中未找到适合配图的章节")
        sys.exit(0)

    print(f"✏️ 文章插图生成")
    print(f"   文章: {md_path}")
    print(f"   风格: {STYLES[style]['name']} ({style})")
    print(f"   比例: {ratio}")
    print(f"   识别到 {len(sections)} 个配图位置")
    print()

    # 输出分析结果
    print("=== 配图规划 ===")
    for i, sec in enumerate(sections, 1):
        t = type_override or sec['recommended_type']
        print(f"  {i}. [{TYPES[t]['name']}] {sec['title']} (置信度:{sec['confidence']})")
    print()

    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 逐张生成
    for i, sec in enumerate(sections, 1):
        t = type_override or sec['recommended_type']
        prompt = build_illust_prompt(sec, t, style)
        output_path = os.path.join(output_dir, f"illust_{i:02d}_{t}.png")

        print(f"  生成第{i}/{len(sections)}张: {sec['title']} [{TYPES[t]['name']}]")
        cmd = [sys.executable, str(CORE_SCRIPT), prompt, "-r", ratio, "-o", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    ⚠️ 失败: {result.stderr[:200]}")
        else:
            print(f"    ✅ {output_path}")

    print(f"\n全部完成！{len(sections)}张插图已保存到 {output_dir}/")


def list_options():
    print("=== 插图类型 (6种) ===\n")
    for k, v in TYPES.items():
        print(f"  {k:15s} {v['name']:8s} — 触发词: {', '.join(v['trigger_words'][:4])}")
    print("\n=== 视觉风格 (8种) ===\n")
    for k, v in STYLES.items():
        print(f"  {k:15s} {v['name']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="zlab 智能文章插图生成器 — 6类型 × 8风格",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 自动分析文章并生成插图
  python zlab_article_illustrator.py article.md --style notion -o images/

  # 指定所有插图类型为流程图
  python zlab_article_illustrator.py article.md --type flowchart --style blueprint -o images/

  # 查看选项
  python zlab_article_illustrator.py --list
        """
    )
    parser.add_argument("article", nargs="?", help="Markdown文章路径")
    parser.add_argument("--style", default="notion", choices=STYLES.keys(), help="视觉风格（默认 notion）")
    parser.add_argument("--type", choices=TYPES.keys(), help="强制指定所有插图类型（不指定则自动判断）")
    parser.add_argument("-r", "--ratio", default="16:9", help="宽高比（默认 16:9）")
    parser.add_argument("-o", "--output", default="illustrations", help="输出目录（默认 illustrations/）")
    parser.add_argument("--list", action="store_true", help="列出所有选项")

    args = parser.parse_args()

    if args.list:
        list_options()
        return

    if not args.article:
        parser.print_help()
        print("\n错误: 请提供文章文件路径")
        sys.exit(1)

    if not os.path.exists(args.article):
        print(f"错误: 文件不存在 {args.article}")
        sys.exit(1)

    generate_illustrations(args.article, args.style, args.ratio, args.output, args.type)


if __name__ == "__main__":
    main()
