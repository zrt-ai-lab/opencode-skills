#!/usr/bin/env python3
"""
场景拆分器 - 将口播文本拆分成细镜头
基于时间戳对齐图片和字幕
"""

import json
import re
import argparse
from pathlib import Path
from typing import List, Dict


def split_by_sentence_timestamps(timestamps: List[Dict]) -> List[Dict]:
    """
    直接使用 TTS 的 SentenceBoundary 时间戳作为镜头分割
    
    Args:
        timestamps: TTS 输出的时间戳（包含 sentence 类型）
    
    Returns:
        每个镜头的信息：text, start, end, duration
    """
    shots = []
    for ts in timestamps:
        if ts.get("type") == "sentence":
            shots.append({
                "text": ts["text"],
                "start": ts["start"],
                "end": ts["end"],
                "duration": round(ts["end"] - ts["start"], 2)
            })
    
    if not shots and timestamps:
        total_start = timestamps[0]["start"]
        total_end = timestamps[-1]["end"]
        full_text = "".join(ts["text"] for ts in timestamps)
        shots.append({
            "text": full_text,
            "start": total_start,
            "end": total_end,
            "duration": round(total_end - total_start, 2)
        })
    
    return shots


def split_long_shots(shots: List[Dict], max_duration: float = 6.0) -> List[Dict]:
    """
    将过长的镜头按标点符号进一步拆分
    
    Args:
        shots: 镜头列表
        max_duration: 最大镜头时长
    
    Returns:
        拆分后的镜头列表
    """
    result = []
    
    for shot in shots:
        if shot["duration"] <= max_duration:
            result.append(shot)
            continue
        
        text = shot["text"]
        splits = re.split(r'([，。！？,!?])', text)
        
        sub_texts = []
        current = ""
        for i, part in enumerate(splits):
            current += part
            if i % 2 == 1 and current.strip():
                sub_texts.append(current.strip())
                current = ""
        if current.strip():
            sub_texts.append(current.strip())
        
        if len(sub_texts) <= 1:
            result.append(shot)
            continue
        
        total_chars = sum(len(t) for t in sub_texts)
        current_time = shot["start"]
        
        for sub_text in sub_texts:
            ratio = len(sub_text) / total_chars
            sub_duration = shot["duration"] * ratio
            result.append({
                "text": sub_text,
                "start": round(current_time, 2),
                "end": round(current_time + sub_duration, 2),
                "duration": round(sub_duration, 2)
            })
            current_time += sub_duration
    
    return result


def merge_short_shots(shots: List[Dict], min_duration: float = 2.5) -> List[Dict]:
    """合并过短的镜头"""
    if not shots:
        return shots
    
    merged = []
    current = shots[0].copy()
    
    for shot in shots[1:]:
        if current["duration"] < min_duration:
            current["text"] += shot["text"]
            current["end"] = shot["end"]
            current["duration"] = round(current["end"] - current["start"], 2)
        else:
            merged.append(current)
            current = shot.copy()
    
    merged.append(current)
    return merged


def generate_shot_prompts(shots: List[Dict], style: str, context: str = "") -> List[Dict]:
    """
    为每个镜头生成图片提示词
    
    Args:
        shots: 镜头列表
        style: 画风描述
        context: 上下文（如角色描述）
    
    Returns:
        带有图片提示词的镜头列表
    """
    for i, shot in enumerate(shots):
        shot["image_prompt"] = f"{style}，{context}，画面：{shot['text']}。禁止出现任何文字"
        shot["index"] = i + 1
    
    return shots


def generate_srt(shots: List[Dict], output_path: str):
    """生成 SRT 字幕文件"""
    def format_time(seconds: float) -> str:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    with open(output_path, "w", encoding="utf-8") as f:
        for i, shot in enumerate(shots, 1):
            f.write(f"{i}\n")
            f.write(f"{format_time(shot['start'])} --> {format_time(shot['end'])}\n")
            f.write(f"{shot['text']}\n\n")
    
    print(f"  ✓ 字幕: {output_path}")


def process_scene(text: str, timestamps_path: str, style: str, context: str = "", output_dir: str = ".") -> Dict:
    """
    处理单个场景，输出镜头配置
    
    Args:
        text: 场景口播文本
        timestamps_path: TTS 时间戳 JSON 文件
        style: 画风
        context: 上下文
        output_dir: 输出目录
    
    Returns:
        场景配置字典
    """
    with open(timestamps_path, "r", encoding="utf-8") as f:
        timestamps = json.load(f)
    
    shots = split_by_sentence_timestamps(timestamps)
    
    shots = split_long_shots(shots, max_duration=6.0)
    
    shots = merge_short_shots(shots, min_duration=2.5)
    
    shots = generate_shot_prompts(shots, style, context)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    srt_path = output_path / "subtitles.srt"
    generate_srt(shots, str(srt_path))
    
    config_path = output_path / "shots.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(shots, f, ensure_ascii=False, indent=2)
    print(f"  ✓ 镜头配置: {config_path}")
    
    return {"shots": shots, "srt_path": str(srt_path)}


def main():
    parser = argparse.ArgumentParser(description='场景拆分器')
    parser.add_argument('--text', type=str, required=True, help='口播文本')
    parser.add_argument('--timestamps', type=str, required=True, help='TTS时间戳JSON文件')
    parser.add_argument('--style', type=str, default='', help='画风描述')
    parser.add_argument('--context', type=str, default='', help='上下文（角色等）')
    parser.add_argument('--output-dir', type=str, default='.', help='输出目录')
    
    args = parser.parse_args()
    
    result = process_scene(
        text=args.text,
        timestamps_path=args.timestamps,
        style=args.style,
        context=args.context,
        output_dir=args.output_dir
    )
    
    print(f"\n拆分完成，共 {len(result['shots'])} 个镜头：")
    for shot in result["shots"]:
        print(f"  [{shot['duration']:.1f}s] {shot['text']}")


if __name__ == "__main__":
    main()
