#!/usr/bin/env python3
"""
TTS 语音生成器 - 使用 edge-tts
支持时间戳输出，用于字幕同步和镜头切换
"""

import asyncio
import argparse
import os
import json
import yaml
import edge_tts


async def generate_tts(text: str, voice: str, output_path: str, rate: str = "+0%", pitch: str = "+0Hz", with_timestamps: bool = False):
    """生成单条语音，可选输出时间戳"""
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    
    if with_timestamps:
        timestamps = []
        audio_chunks = []
        
        async for chunk in communicate.stream():
            chunk_type = chunk.get("type", "")
            if chunk_type == "audio":
                audio_chunks.append(chunk.get("data", b""))
            elif chunk_type == "WordBoundary":
                timestamps.append({
                    "text": chunk.get("text", ""),
                    "start": chunk.get("offset", 0) / 10000000,
                    "end": (chunk.get("offset", 0) + chunk.get("duration", 0)) / 10000000
                })
            elif chunk_type == "SentenceBoundary":
                timestamps.append({
                    "text": chunk.get("text", ""),
                    "start": chunk.get("offset", 0) / 10000000,
                    "end": (chunk.get("offset", 0) + chunk.get("duration", 0)) / 10000000,
                    "type": "sentence"
                })
        
        with open(output_path, "wb") as f:
            for data in audio_chunks:
                f.write(data)
        
        ts_path = output_path.rsplit(".", 1)[0] + ".json"
        with open(ts_path, "w", encoding="utf-8") as f:
            json.dump(timestamps, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ 生成: {output_path} + 时间戳")
        return timestamps
    else:
        await communicate.save(output_path)
        print(f"  ✓ 生成: {output_path}")
        return None


async def generate_batch(config_path: str, output_dir: str):
    """批量生成语音"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    os.makedirs(output_dir, exist_ok=True)
    
    voice_config = config.get('voice', {})
    voice_name = voice_config.get('name', 'zh-CN-YunxiNeural')
    rate = voice_config.get('rate', '+0%')
    pitch = voice_config.get('pitch', '+0Hz')
    
    scenes = config.get('scenes', [])
    tasks = []
    
    for i, scene in enumerate(scenes):
        text = scene.get('text', '')
        if not text:
            continue
        output_path = os.path.join(output_dir, f"{i:03d}.mp3")
        tasks.append(generate_tts(text, voice_name, output_path, rate, pitch))
    
    print(f"开始生成 {len(tasks)} 条语音...")
    await asyncio.gather(*tasks)
    print(f"✓ 完成！语音文件保存在: {output_dir}")


async def list_voices():
    """列出所有可用音色"""
    voices = await edge_tts.list_voices()
    zh_voices = [v for v in voices if v['Locale'].startswith('zh')]
    
    print("\n中文可用音色：")
    print("-" * 60)
    for v in zh_voices:
        gender = "♂" if v['Gender'] == 'Male' else "♀"
        print(f"{gender} {v['ShortName']:<30} {v['Locale']}")
    print("-" * 60)
    print(f"共 {len(zh_voices)} 个中文音色")


def main():
    parser = argparse.ArgumentParser(description='Edge-TTS 语音生成器')
    parser.add_argument('--text', type=str, help='要转换的文本')
    parser.add_argument('--voice', type=str, default='zh-CN-YunxiNeural', help='音色名称')
    parser.add_argument('--rate', type=str, default='+0%', help='语速调整')
    parser.add_argument('--pitch', type=str, default='+0Hz', help='音调调整')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--timestamps', action='store_true', help='输出时间戳JSON文件')
    parser.add_argument('--config', type=str, help='配置文件路径(批量生成)')
    parser.add_argument('--output-dir', type=str, default='temp/audio', help='批量输出目录')
    parser.add_argument('--list-voices', action='store_true', help='列出可用音色')
    
    args = parser.parse_args()
    
    if args.list_voices:
        asyncio.run(list_voices())
    elif args.config:
        asyncio.run(generate_batch(args.config, args.output_dir))
    elif args.text and args.output:
        asyncio.run(generate_tts(args.text, args.voice, args.output, args.rate, args.pitch, args.timestamps))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
