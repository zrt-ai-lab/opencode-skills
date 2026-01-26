#!/usr/bin/env python3
"""
调研报告专用信息图生成脚本
预设手绘风格可视化模板，保持系列配图风格统一

Author: 翟星人
"""

import argparse
import subprocess
import sys
import os

# 预设风格模板 - 手绘体可视化风格
STYLE_TEMPLATES = {
    "arch": {
        "name": "架构图",
        "prefix": "手绘风格技术架构信息图，简洁扁平设计，",
        "suffix": "手绘线条感，柔和的科技蓝配色(#4A90D9)，浅灰白色背景，模块化分层布局，圆角矩形框，手写体中文标签，简约图标，整体清新专业。",
        "trigger": "核心架构、系统结构、技术栈、模块组成"
    },
    "flow": {
        "name": "流程图",
        "prefix": "手绘风格流程信息图，简洁扁平设计，",
        "suffix": "手绘线条和箭头，科技蓝(#4A90D9)主色调，浅绿色(#81C784)表示成功节点，浅橙色(#FFB74D)表示判断节点，浅灰白色背景，从上到下或从左到右布局，手写体中文标签，步骤清晰。",
        "trigger": "流程、步骤、工作流、执行顺序"
    },
    "compare": {
        "name": "对比图",
        "prefix": "手绘风格对比信息图，左右分栏设计，",
        "suffix": "手绘线条感，左侧用柔和蓝色(#4A90D9)，右侧用柔和橙色(#FF8A65)，中间VS分隔，浅灰白色背景，手写体中文标签，对比项目清晰列出，简约图标点缀。",
        "trigger": "对比、vs、区别、差异"
    },
    "concept": {
        "name": "概念图",
        "prefix": "手绘风格概念信息图，中心发散设计，",
        "suffix": "手绘线条感，中心主题用科技蓝(#4A90D9)，周围要素用柔和的蓝紫渐变色系，浅灰白色背景，连接线条有手绘感，手写体中文标签，布局均衡美观。",
        "trigger": "核心概念、要素组成、多个方面"
    }
}

# 基础路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT_TO_IMAGE_SCRIPT = os.path.join(BASE_DIR, "scripts", "text_to_image.py")


def generate_image(style: str, title: str, content: str, output: str):
    """
    使用预设风格生成信息图
    
    Args:
        style: 风格类型 (arch/flow/compare/concept)
        title: 图表标题
        content: 图表内容描述
        output: 输出路径
    """
    if style not in STYLE_TEMPLATES:
        print(f"错误: 未知风格 '{style}'")
        print(f"可用风格: {', '.join(STYLE_TEMPLATES.keys())}")
        sys.exit(1)
    
    template = STYLE_TEMPLATES[style]
    
    # 组装完整提示词
    prompt = f"{template['prefix']}标题：{title}，{content}，{template['suffix']}"
    
    print(f"生成 {template['name']}: {title}")
    print(f"风格: 手绘体可视化")
    print(f"输出: {output}")
    
    # 调用 text_to_image.py
    cmd = [
        sys.executable,
        TEXT_TO_IMAGE_SCRIPT,
        prompt,
        "--output", output
    ]
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode != 0:
        print(f"生成失败")
        sys.exit(1)


def list_styles():
    """列出所有可用风格"""
    print("可用风格模板（手绘体可视化）:\n")
    for key, template in STYLE_TEMPLATES.items():
        print(f"  {key:10} - {template['name']}")
        print(f"             触发场景: {template['trigger']}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="调研报告专用信息图生成（手绘风格）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成架构图
  python research_image.py -t arch -n "Ralph Loop 核心架构" -c "展示 Prompt、Agent、Stop Hook、Files 四个模块的循环关系" -o images/arch.png

  # 生成流程图
  python research_image.py -t flow -n "Stop Hook 工作流程" -c "Agent尝试退出、Hook触发、检查条件、允许或阻止退出" -o images/flow.png

  # 生成对比图
  python research_image.py -t compare -n "ReAct vs Ralph Loop" -c "左侧ReAct自我评估停止，右侧Ralph外部Hook控制" -o images/compare.png

  # 生成概念图
  python research_image.py -t concept -n "状态持久化" -c "中心是Agent，周围是progress.txt、prd.json、Git历史、代码文件四个要素" -o images/concept.png

  # 查看所有风格
  python research_image.py --list
        """
    )
    
    parser.add_argument("-t", "--type", choices=list(STYLE_TEMPLATES.keys()),
                        help="图解类型: arch(架构图), flow(流程图), compare(对比图), concept(概念图)")
    parser.add_argument("-n", "--name", help="图表标题")
    parser.add_argument("-c", "--content", help="图表内容描述")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("--list", action="store_true", help="列出所有可用风格")
    
    args = parser.parse_args()
    
    if args.list:
        list_styles()
        return
    
    if not all([args.type, args.name, args.content, args.output]):
        parser.print_help()
        print("\n错误: 必须提供 -t, -n, -c, -o 参数")
        sys.exit(1)
    
    generate_image(args.type, args.name, args.content, args.output)


if __name__ == "__main__":
    main()
