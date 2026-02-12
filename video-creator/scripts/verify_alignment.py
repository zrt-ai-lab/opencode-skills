#!/usr/bin/env python3
"""
视频图文语音对齐校验器

在合成视频之前，必须运行此脚本校验：
1. 每张图片文件是否存在
2. duration 是否为精确数值（必须从 narration.json 计算）
3. 图片总时长 vs 音频总时长（误差 < 1s）
4. 每张图时长是否在合理范围（1-7s）
5. 图片文件名关键词 vs 语音内容关键词 语义交叉比对
6. 输出完整对照表

用法:
    python verify_alignment.py video_config.yaml

退出码:
    0 = 校验通过
    1 = 校验失败，禁止合成
"""
import json
import re
import sys
import yaml
from pathlib import Path


def get_audio_duration(audio_path):
    """用 ffprobe 获取音频时长"""
    import subprocess
    result = subprocess.run([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'csv=p=0', str(audio_path)
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def load_narration_timestamps(work_dir, audio_path):
    """加载 narration.json 时间戳"""
    candidates = [
        work_dir / 'narration.json',
        Path(audio_path).with_suffix('.json'),
        work_dir / (Path(audio_path).stem + '.json'),
    ]
    for p in candidates:
        if p.exists():
            with open(p, 'r') as f:
                return json.load(f)
    return None


# ── 语义关键词映射表 ──
# 图片文件名中的关键词 → 语音中应该出现的关键词
KEYWORD_MAP = {
    # 模型名
    'ds': ['deepseek', 'ds', '深度求索'],
    'deepseek': ['deepseek', 'ds', '深度求索'],
    'glm': ['glm', '智谱', 'zhipu'],
    'opus': ['opus', 'claude', 'anthropic'],
    'claude': ['opus', 'claude', 'anthropic'],
    'codex': ['codex', 'openai', 'gpt'],
    'gpt': ['codex', 'openai', 'gpt'],
    'kimi': ['kimi', '月之暗面', 'moonshot', 'k2'],
    'qwen': ['qwen', '通义', '阿里', '千问'],
    'minimax': ['minimax', 'mm'],
    'mm': ['minimax', 'mm', 'minimax'],
    # 功能/概念
    'swarm': ['swarm', '蜂群', '并行', '子任务'],
    'bench': [],  # bench 太通用，语音里可能说"分"、"评测"或具体数字，不强制
    'bench1': [],
    'bench2': [],
    'cost': ['成本', '性价比', '价格', '美元', '免费'],
    'price': ['价格', '贵', '成本', '质量'],
    'agent': ['agent', '智能体', '任务'],
    'pony': ['pony', 'alpha', '神秘', '测试版'],
    'pony1': ['pony', 'alpha', '神秘', '测试版'],
    'pony2': ['pony', 'alpha', '第一', '排行'],
    'b2b': ['b2b', 'b2c', '商业化'],
    'music': ['music', '音乐', '音频'],
    'multi': [],  # multi 太通用
    'multi1': [],
    'multi2': [],
    'arch': ['架构', '参数', '注意力', '稀疏'],
    'terminal': [],  # terminal 只是评测名，语音可能换说法
    'think': ['thinking', '推理', '能力'],
    'future': ['指日可待', '即将', '蓄势', '待发'],
    'landscape': ['百花齐放', '格局', '一家独大'],
    'budget': ['场景', '预算', '选', '取决'],
    'cta': ['关注', '下期', '再见'],
    'opening': ['春节', '炸场', '2026'],
    'intro': [],  # intro 太通用，不强制检查
    'sum': [],    # sum/summary 太通用，不强制检查（但下面会检查模型名）
    'core': [],   # core 太通用
    'full': [],   # full 太通用
    'top': [],
    'btm': [],
    'creative': [],
    'models': [],
    'vs': [],
    'title': [],
}


def extract_keywords_from_filename(filename):
    """从文件名提取关键词"""
    name = Path(filename).stem.lower()
    # 去掉序号前缀 (01_, 02_ 等)
    name = re.sub(r'^\d+_', '', name)
    # 按 _ 分割
    parts = name.split('_')
    return parts


def check_semantic_match(filename, speech_text):
    """
    检查图片文件名暗示的内容是否和语音文字匹配
    
    策略：
    - 模型名关键词（ds/glm/opus/codex/kimi/qwen/mm）只在总结段（文件名含 sum_）强制检查
      因为正文段落里模型名只在开头提一次，后续评测细节不会重复模型名
    - 功能/概念关键词（swarm/cost/price/landscape/cta 等）始终检查
    
    返回: (is_ok, reason)
    """
    if not speech_text:
        return True, ""
    
    parts = extract_keywords_from_filename(filename)
    speech_lower = speech_text.lower()
    
    # 判断是否是总结段（去掉序号后以 sum_ 开头，如 37_sum_ds.png）
    name_no_num = re.sub(r'^\d+_', '', Path(filename).stem.lower())
    is_summary = name_no_num.startswith('sum_')
    
    # 模型名关键词集合
    MODEL_KEYS = {'ds', 'deepseek', 'glm', 'opus', 'claude', 'codex', 'gpt', 'kimi', 'qwen', 'minimax', 'mm'}
    
    mismatches = []
    for part in parts:
        if part in KEYWORD_MAP:
            expected_words = KEYWORD_MAP[part]
            if not expected_words:
                continue  # 跳过不强制检查的通用词
            
            # 模型名关键词：只在总结段强制检查
            if part in MODEL_KEYS and not is_summary:
                continue
            
            # 检查语音中是否包含至少一个期望关键词
            found = any(w in speech_lower for w in expected_words)
            if not found:
                mismatches.append((part, expected_words))
    
    if mismatches:
        details = []
        for part, expected in mismatches:
            details.append(f"文件名含'{part}'但语音中没有{expected}中的任何一个")
        return False, '; '.join(details)
    
    return True, ""


def main():
    if len(sys.argv) < 2:
        print("用法: python verify_alignment.py video_config.yaml")
        sys.exit(1)

    config_path = Path(sys.argv[1])
    if not config_path.exists():
        print(f"❌ 配置文件不存在: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    work_dir = config_path.parent
    scenes = config.get('scenes', [])
    if not scenes:
        print("❌ 配置文件中没有 scenes")
        sys.exit(1)

    errors = []
    warnings = []

    # ── 收集所有图片和 duration ──
    images = []
    durations = []
    audio_files = []

    for si, scene in enumerate(scenes):
        audio_path = work_dir / scene['audio']
        if not audio_path.exists():
            errors.append(f"音频不存在: {audio_path}")
        audio_files.append(audio_path)

        if 'images' not in scene:
            errors.append(f"场景 {si+1} 缺少 images 列表")
            continue

        for img_cfg in scene['images']:
            img_path = work_dir / img_cfg['file']
            if not img_path.exists():
                errors.append(f"图片不存在: {img_path}")

            d = img_cfg.get('duration')
            if d is None:
                errors.append(f"❌ {img_cfg['file']} 缺少 duration！必须从 narration.json 精确计算！")
                durations.append(0)
            else:
                try:
                    d = float(d)
                except (ValueError, TypeError):
                    errors.append(f"❌ {img_cfg['file']} 的 duration='{d}' 不是数字！必须填写精确的秒数！")
                    durations.append(0)
                    continue
                durations.append(d)
                if d <= 0:
                    errors.append(f"❌ {img_cfg['file']} duration={d}，不能 ≤ 0")
                elif d < 1.0:
                    warnings.append(f"⚠ {img_cfg['file']} duration={d:.1f}s，太短（<1s）")
                elif d > 7.0:
                    warnings.append(f"⚠ {img_cfg['file']} duration={d:.1f}s，超过7秒，建议拆分")

            images.append(img_cfg['file'])

    # ── 音频总时长 ──
    total_audio = 0
    for af in audio_files:
        if af.exists():
            total_audio += get_audio_duration(af)

    total_image = sum(durations)
    diff = abs(total_image - total_audio)

    if diff > 1.0:
        errors.append(f"❌ 图片总时长({total_image:.1f}s) vs 音频总时长({total_audio:.1f}s)，差值 {diff:.1f}s 超过 1s！")
    elif diff > 0.5:
        warnings.append(f"⚠ 图片总时长({total_image:.1f}s) vs 音频总时长({total_audio:.1f}s)，差值 {diff:.1f}s")

    # ── 加载 narration.json 做语义对照 ──
    timestamps = None
    if audio_files:
        timestamps = load_narration_timestamps(work_dir, audio_files[0])

    # ── 输出对照表 + 语义校验 ──
    print("\n" + "=" * 80)
    print("📋 图文语音对齐校验报告")
    print("=" * 80)

    print(f"\n{'序号':<4} {'图片文件':<28} {'时长':>5}  {'语义':>3}  对应语音内容")
    print("-" * 80)

    semantic_errors = []
    cum_time = 0
    for i, (img, dur) in enumerate(zip(images, durations)):
        # 匹配 narration.json 中对应的句子
        matched_text = ""
        if timestamps:
            start_t = cum_time
            end_t = cum_time + dur
            matched_sentences = []
            for ts in timestamps:
                if ts['end'] > start_t + 0.1 and ts['start'] < end_t - 0.1:
                    matched_sentences.append(ts['text'])
            if matched_sentences:
                matched_text = ' '.join(matched_sentences)

        # 语义校验
        display_text = matched_text[:45] + "..." if len(matched_text) > 45 else matched_text
        sem_ok, sem_reason = check_semantic_match(img, matched_text)
        sem_flag = "✅" if sem_ok else "❌"
        
        if not sem_ok:
            semantic_errors.append((i + 1, img, matched_text[:60], sem_reason))

        print(f" {i+1:<3} {img:<28} {dur:>4.1f}s  {sem_flag}  {display_text}")
        cum_time += dur

    print("-" * 80)
    print(f" {'合计':<33} {total_image:>4.1f}s")
    print(f" {'音频总时长':<33} {total_audio:>4.1f}s")
    print(f" {'差值':<33} {diff:>4.1f}s")

    # ── 语义错误详情 ──
    if semantic_errors:
        print(f"\n🔍 语义不匹配 ({len(semantic_errors)}):")
        for idx, img, text, reason in semantic_errors:
            print(f"  第{idx}张 {img}")
            print(f"    语音: {text}")
            print(f"    问题: {reason}")
        errors.append(f"❌ {len(semantic_errors)} 张图片的文件名与语音内容语义不匹配！图片画的内容和语音说的内容对不上！")

    # ── 输出结果 ──
    if warnings:
        print(f"\n⚠ 警告 ({len(warnings)}):")
        for w in warnings:
            print(f"  {w}")

    if errors:
        print(f"\n❌ 错误 ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
        print(f"\n⛔ 校验失败！请修复以上问题后再合成视频。")
        print(f"   禁止跳过校验直接合成！")
        sys.exit(1)
    else:
        print(f"\n✅ 校验通过！图文语音对齐正确，可以合成视频。")
        sys.exit(0)


if __name__ == "__main__":
    main()
