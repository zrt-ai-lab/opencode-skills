#!/usr/bin/env python3
"""
知识漫画生成器 (zlab Comic Generator)
画风 × 基调 × 布局，逐页分镜生成
底层调用 core/text_to_image.py + core/image_to_image.py

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

# === 三维定义 ===

ARTS = {
    "ligne-claire": {
        "name": "清线",
        "prompt": "清晰统一线条，平涂色彩填充，欧洲漫画传统风格（丁丁历险记风），干净利落的黑色轮廓线"
    },
    "manga": {
        "name": "日漫",
        "prompt": "日本漫画风格，大眼睛角色，表情丰富夸张，速度线和效果线，网点阴影，动感十足"
    },
    "realistic": {
        "name": "写实",
        "prompt": "数字绘画写实风格，准确人体比例，精致细腻渲染，电影级光影效果"
    },
    "ink-brush": {
        "name": "水墨",
        "prompt": "中国水墨画风格，毛笔笔触，水墨晕染效果，留白意境，黑白灰为主偶有点缀色"
    },
    "chalk": {
        "name": "粉笔",
        "prompt": "粉笔画风格，黑板深色背景，彩色粉笔手绘线条，粗糙质感，温暖童趣"
    },
}

TONES = {
    "neutral": {
        "name": "中性",
        "prompt": "平衡理性的色调，中性明度，教育性氛围，冷静客观"
    },
    "warm": {
        "name": "温暖",
        "prompt": "温暖怀旧色调，暖黄暖橙为主，柔和光线，亲切感人"
    },
    "dramatic": {
        "name": "戏剧",
        "prompt": "高对比戏剧性色调，强烈明暗对比，紧张感，冲击力强"
    },
    "romantic": {
        "name": "浪漫",
        "prompt": "柔和浪漫色调，粉色紫色为主，装饰性花瓣元素，梦幻唯美"
    },
    "energetic": {
        "name": "活力",
        "prompt": "明亮高饱和活力色调，动感构图，充满能量和激情"
    },
    "vintage": {
        "name": "复古",
        "prompt": "复古做旧色调，泛黄胶片质感，历史感，时代真实性"
    },
    "action": {
        "name": "动作",
        "prompt": "动作场面色调，速度线冲击效果，爆炸光效，战斗视觉张力"
    },
}

LAYOUTS = {
    "standard": {
        "name": "标准",
        "panels": "4-6格",
        "prompt": "标准漫画分格，4到6个格子，大小均匀，叙事节奏平稳"
    },
    "cinematic": {
        "name": "电影",
        "panels": "2-4格",
        "prompt": "电影宽银幕分格，2到4个宽幅画面，横向构图，戏剧张力"
    },
    "dense": {
        "name": "密集",
        "panels": "6-9格",
        "prompt": "密集分格，6到9个小格子，信息量大，适合技术说明"
    },
    "splash": {
        "name": "跨页",
        "panels": "1-2大图",
        "prompt": "跨页大图，1到2个超大画面，视觉冲击力极强，关键时刻"
    },
    "mixed": {
        "name": "混合",
        "panels": "3-7不等",
        "prompt": "混合分格，大小不一的格子3到7个，丰富的视觉节奏变化"
    },
    "webtoon": {
        "name": "条漫",
        "panels": "3-5竖向",
        "prompt": "竖向条漫布局，3到5个竖向排列的画面，适合手机阅读"
    },
}


def parse_source_to_pages(content, max_pages=12):
    """将文字素材拆分为漫画页"""
    pages = []

    # 按段落/章节拆分
    paragraphs = re.split(r'\n{2,}', content.strip())

    # 合并短段落，拆分长段落
    buffer = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # h2/h3标记作为分页点
        if re.match(r'^#{2,3}\s', para):
            if buffer:
                pages.append(buffer.strip())
                buffer = ""
            buffer = para + "\n"
        else:
            buffer += para + "\n"
            # 超过200字分一页
            if len(buffer) > 200:
                pages.append(buffer.strip())
                buffer = ""

    if buffer:
        pages.append(buffer.strip())

    return pages[:max_pages]


def build_comic_prompt(page_content, page_num, total, art_def, tone_def, layout_def):
    """构建单页漫画的生图提示词"""
    parts = [
        f"知识漫画，第{page_num}页（共{total}页），竖版3:4",
        art_def['prompt'],
        tone_def['prompt'],
        layout_def['prompt'],
        f"本页剧情内容：{page_content[:300]}",
        "对话气泡中使用中文，文字清晰可读。角色造型一致，表情生动夸张。画面构图饱满但不拥挤，留出气泡空间。分格之间有清晰的边框线分隔。背景适当简化突出人物和对话",
    ]
    return "，".join(parts)


def generate_comic(source_path, art, tone, layout, ratio, output_dir, max_pages):
    """主生成流程"""
    if art not in ARTS:
        print(f"错误: 未知画风 '{art}'，可用: {', '.join(ARTS.keys())}")
        sys.exit(1)
    if tone not in TONES:
        print(f"错误: 未知基调 '{tone}'，可用: {', '.join(TONES.keys())}")
        sys.exit(1)
    if layout not in LAYOUTS:
        print(f"错误: 未知布局 '{layout}'，可用: {', '.join(LAYOUTS.keys())}")
        sys.exit(1)

    art_def = ARTS[art]
    tone_def = TONES[tone]
    layout_def = LAYOUTS[layout]

    # 读取素材
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 拆分为页
    pages = parse_source_to_pages(content, max_pages)

    print(f"📖 漫画生成")
    print(f"   画风: {art_def['name']} ({art})")
    print(f"   基调: {tone_def['name']} ({tone})")
    print(f"   布局: {layout_def['name']} ({layout})，{layout_def['panels']}")
    print(f"   页数: {len(pages)}")
    print(f"   比例: {ratio}")
    print(f"   输出: {output_dir}/")
    print()

    # 输出分镜大纲
    print("=== 分镜大纲 ===")
    for i, page in enumerate(pages, 1):
        summary = page[:60].replace('\n', ' ')
        print(f"  第{i}页: {summary}...")
    print()

    # 创建输出目录
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 逐页串行生成（首页text_to_image，后续image_to_image参考上一页）
    prev_page_path = None
    for i, page in enumerate(pages, 1):
        prompt = build_comic_prompt(page, i, len(pages), art_def, tone_def, layout_def)
        output_path = os.path.join(output_dir, f"page_{i:02d}.png")

        print(f"  生成第{i}/{len(pages)}页...")

        if i == 1 or prev_page_path is None:
            # 首页：文生图定调
            cmd = [sys.executable, str(CORE_T2I), prompt, "-r", ratio, "-o", output_path]
        else:
            # 后续页：参考上一页，保持角色和风格一致
            ref_prompt = f"参考模板图的角色造型、画风和色调，保持完全一致。{prompt}"
            cmd = [sys.executable, str(CORE_I2I), prev_page_path, ref_prompt, "-r", ratio, "-o", output_path]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"    ⚠️ 第{i}页失败: {result.stderr[:200]}")
        else:
            print(f"    ✅ {output_path}")
            prev_page_path = output_path

    print(f"\n全部完成！{len(pages)}页漫画已保存到 {output_dir}/")


def list_options():
    print("=== 画风 (5种) ===\n")
    for k, v in ARTS.items():
        print(f"  {k:15s} {v['name']}")
    print("\n=== 基调 (7种) ===\n")
    for k, v in TONES.items():
        print(f"  {k:15s} {v['name']}")
    print("\n=== 布局 (6种) ===\n")
    for k, v in LAYOUTS.items():
        print(f"  {k:15s} {v['name']:6s} {v['panels']}")
    print(f"\n共 {len(ARTS)} × {len(TONES)} × {len(LAYOUTS)} = {len(ARTS)*len(TONES)*len(LAYOUTS)} 种组合")


def main():
    parser = argparse.ArgumentParser(
        description="zlab 知识漫画生成器 — 5画风 × 7基调 × 6布局",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 日漫风温暖基调
  python zlab_comic.py story.md --art manga --tone warm -o comic/

  # 水墨动作风
  python zlab_comic.py story.md --art ink-brush --tone action --layout cinematic -o comic/

  # 查看所有选项
  python zlab_comic.py --list
        """
    )
    parser.add_argument("source", nargs="?", help="文字素材Markdown文件")
    parser.add_argument("--art", default="ligne-claire", choices=ARTS.keys(), help="画风（默认 ligne-claire）")
    parser.add_argument("--tone", default="neutral", choices=TONES.keys(), help="基调（默认 neutral）")
    parser.add_argument("--layout", default="standard", choices=LAYOUTS.keys(), help="布局（默认 standard）")
    parser.add_argument("-r", "--ratio", default="3:4", help="宽高比（默认 3:4竖版）")
    parser.add_argument("-o", "--output", default="comic", help="输出目录（默认 comic/）")
    parser.add_argument("--pages", type=int, default=12, help="最大页数（默认 12）")
    parser.add_argument("--list", action="store_true", help="列出所有选项")

    args = parser.parse_args()

    if args.list:
        list_options()
        return

    if not args.source:
        parser.print_help()
        print("\n错误: 请提供素材文件路径")
        sys.exit(1)

    if not os.path.exists(args.source):
        print(f"错误: 文件不存在 {args.source}")
        sys.exit(1)

    generate_comic(args.source, args.art, args.tone, args.layout, args.ratio, args.output, args.pages)


if __name__ == "__main__":
    main()
