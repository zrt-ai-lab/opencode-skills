#!/usr/bin/env python3
"""
视频生成器 - 图片+音频合成视频
支持：淡入淡出转场、自动拼接片尾、添加BGM

用法:
    python video_maker.py config.yaml
    python video_maker.py config.yaml --no-outro  # 不加片尾
    python video_maker.py config.yaml --no-bgm    # 不加BGM
"""
import argparse
import os
import subprocess
import sys
import yaml
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
ASSETS_DIR = SKILL_DIR / "assets"
BGM_DEFAULT = ASSETS_DIR / "bgm_technology.mp3"
BGM_EPIC = ASSETS_DIR / "bgm_epic.mp3"

VALID_ASPECT_RATIOS = [
    "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
]

RATIO_TO_SIZE = {
    "1:1": (1024, 1024),
    "2:3": (832, 1248),
    "3:2": (1248, 832),
    "3:4": (1080, 1440),
    "4:3": (1440, 1080),
    "4:5": (864, 1080),
    "5:4": (1080, 864),
    "9:16": (1080, 1920),
    "16:9": (1920, 1080),
    "21:9": (1536, 672),
}

def get_outro_path(ratio):
    """根据比例获取片尾路径，优先精确匹配，否则按方向匹配，最后兜底"""
    ratio_file = ASSETS_DIR / f"outro_{ratio.replace(':', 'x')}.mp4"
    if ratio_file.exists():
        return ratio_file
    
    w, h = RATIO_TO_SIZE.get(ratio, (1920, 1080))
    if h > w:
        candidates = ["outro_9x16.mp4", "outro_3x4.mp4"]
    elif w > h:
        candidates = ["outro.mp4", "outro_3x4.mp4"]
    else:
        candidates = ["outro_1x1.mp4", "outro.mp4"]
    
    for name in candidates:
        fallback = ASSETS_DIR / name
        if fallback.exists():
            return fallback
    
    return ASSETS_DIR / "outro.mp4"


def run_cmd(cmd, desc=""):
    """执行命令并返回结果"""
    if desc:
        print(f"  {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"错误: {result.stderr[-1000:]}")
        sys.exit(1)
    return result


def get_duration(file_path):
    """获取音视频时长"""
    result = subprocess.run([
        'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
        '-of', 'csv=p=0', str(file_path)
    ], capture_output=True, text=True)
    return float(result.stdout.strip())


def generate_video_with_transitions(images, durations, output_path, fade_duration=0.5, ratio="16:9"):
    """生成带转场的视频"""
    print(f"\n[1/4] 生成主视频 ({len(images)}张图片, {fade_duration}秒转场)")
    
    width, height = RATIO_TO_SIZE.get(ratio, (1920, 1080))
    
    display_durations = []
    for i, dur in enumerate(durations):
        if i < len(durations) - 1:
            display_durations.append(dur + fade_duration)
        else:
            display_durations.append(dur)
    
    inputs = []
    for img, dur in zip(images, display_durations):
        inputs.extend(['-loop', '1', '-t', str(dur), '-i', str(img)])
    
    filter_parts = []
    for i in range(len(images)):
        filter_parts.append(
            f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v{i}];"
        )
    
    offset = 0
    for i in range(len(images) - 1):
        if i == 0:
            offset = display_durations[0] - fade_duration
            filter_parts.append(
                f"[v0][v1]xfade=transition=fade:duration={fade_duration}:offset={offset}[xf1];"
            )
        else:
            offset += display_durations[i] - fade_duration
            filter_parts.append(
                f"[xf{i}][v{i+1}]xfade=transition=fade:duration={fade_duration}:offset={offset}[xf{i+1}];"
            )
    
    last_xf = f"xf{len(images)-1}"
    filter_complex = ''.join(filter_parts).rstrip(';')
    
    cmd = ['ffmpeg', '-y'] + inputs + [
        '-filter_complex', filter_complex,
        '-map', f'[{last_xf}]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p',
        str(output_path)
    ]
    
    run_cmd(cmd, f"合成{len(images)}张图片")
    print(f"  ✓ 主视频: {get_duration(output_path):.1f}秒")


def merge_audio(audio_files, output_path):
    """合并音频文件"""
    print(f"\n[2/4] 合并音频 ({len(audio_files)}个文件)")
    
    concat_file = output_path.parent / "audio_concat.txt"
    with open(concat_file, 'w') as f:
        for audio in audio_files:
            f.write(f"file '{audio.absolute()}'\n")
    
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_file),
        '-af', 'aresample=44100', '-c:a', 'aac', '-b:a', '192k', str(output_path)
    ]
    run_cmd(cmd, "合并音频")
    concat_file.unlink()
    print(f"  ✓ 音频: {get_duration(output_path):.1f}秒")


def combine_video_audio(video_path, audio_path, output_path):
    """合并视频和音频"""
    cmd = [
        'ffmpeg', '-y', '-i', str(video_path), '-i', str(audio_path),
        '-c:v', 'copy', '-c:a', 'copy', '-shortest', str(output_path)
    ]
    run_cmd(cmd, "合并视频音频")


def append_outro(video_path, output_path, fade_duration=0.5, ratio="16:9"):
    """拼接片尾，自动缩放片尾到主视频分辨率"""
    print(f"\n[3/4] 拼接片尾")
    
    outro_file = get_outro_path(ratio)
    if not outro_file.exists():
        print(f"  ⚠ 片尾文件不存在: {outro_file}")
        return video_path
    
    width, height = RATIO_TO_SIZE.get(ratio, (1920, 1080))
    
    outro_ready = output_path.parent / "outro_ready.mp4"
    cmd = [
        'ffmpeg', '-y', '-i', str(outro_file),
        '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-c:a', 'aac', '-ar', '44100', str(outro_ready)
    ]
    run_cmd(cmd, "准备片尾")
    
    video_duration = get_duration(video_path)
    fade_start = video_duration - fade_duration
    
    cmd = [
        'ffmpeg', '-y', '-i', str(video_path), '-i', str(outro_ready),
        '-filter_complex',
        f"[0:v]fade=t=out:st={fade_start}:d={fade_duration}[v0];"
        f"[1:v]fade=t=in:st=0:d={fade_duration}[v1];"
        f"[v0][v1]concat=n=2:v=1:a=0[vout];"
        f"[0:a][1:a]concat=n=2:v=0:a=1[aout]",
        '-map', '[vout]', '-map', '[aout]',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-c:a', 'aac', '-b:a', '192k', str(output_path)
    ]
    run_cmd(cmd, "拼接片尾")
    outro_ready.unlink()
    print(f"  ✓ 含片尾: {get_duration(output_path):.1f}秒")
    return output_path


def burn_subtitles(video_path, srt_path, output_path, ratio="16:9"):
    """烧录字幕到视频：底部居中固定位置"""
    print(f"\n[字幕] 烧录字幕")
    
    if not Path(srt_path).exists():
        print(f"  ⚠ 字幕文件不存在: {srt_path}")
        return video_path
    
    width, height = RATIO_TO_SIZE.get(ratio, (1920, 1080))
    # 字体大小：高度/25，16:9时约43px，9:16时约77px
    font_size = max(36, int(height / 25))
    margin_bottom = int(height / 15)
    
    ass_path = Path(srt_path).with_suffix('.ass')
    srt_to_ass(srt_path, ass_path, width, height, font_size, margin_bottom)
    
    ass_escaped = str(ass_path).replace(":", r"\:").replace("'", r"\'")
    
    cmd = [
        'ffmpeg', '-y', '-i', str(video_path),
        '-vf', f"ass='{ass_escaped}'",
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '20',
        '-c:a', 'copy', str(output_path)
    ]
    run_cmd(cmd, "烧录字幕")
    print(f"  ✓ 含字幕: {get_duration(output_path):.1f}秒")
    return output_path


def srt_to_ass(srt_path, ass_path, width, height, font_size, margin_bottom):
    """将 SRT 转换为 ASS 格式，固定底部居中，自动换行"""
    import re
    
    with open(srt_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    
    # 每行字数规则表（按分辨率宽度固定）
    CHARS_PER_LINE_MAP = {
        1024: 20,  # 1:1
        832: 14,   # 2:3
        1248: 32,  # 3:2
        1080: 16,  # 3:4, 4:5, 5:4, 9:16 (竖版统一16字)
        1440: 28,  # 4:3
        864: 17,   # 4:5
        1920: 38,  # 16:9
        1536: 48,  # 21:9
    }
    # 查表，找不到则按公式计算
    MAX_CHARS = CHARS_PER_LINE_MAP.get(width)
    if MAX_CHARS is None:
        # 兜底：按宽度和字体大小估算
        MAX_CHARS = max(12, int(width / (font_size * 1.2)))
    
    # 标点符号（不能放行首）
    PUNCTUATION = '，。、：；？！,.:;?!）】」》\'\"'
    
    def find_break_point(text, max_pos):
        """找到合适的断点位置，优先在空格处断开"""
        if max_pos >= len(text):
            return len(text)
        
        # 从max_pos往前找空格断点
        for i in range(max_pos, max(max_pos // 2, 1), -1):
            if text[i] == ' ':
                return i
        # 没找到空格就直接断
        return max_pos
    
    def wrap_text_2lines(text):
        """换行：严格2行，返回单个2行字幕块"""
        text = text.strip()
        if len(text) <= MAX_CHARS:
            return text + r'\N '
        
        # 找第一行断点
        break1 = find_break_point(text, MAX_CHARS)
        line1 = text[:break1].strip()
        line2 = text[break1:].strip()
        
        # 第二行也限制长度
        if len(line2) > MAX_CHARS:
            break2 = find_break_point(line2, MAX_CHARS)
            line2 = line2[:break2].strip()
        
        return line1 + r'\N' + line2
    
    def split_long_text(text, start_sec, end_sec):
        """长文本拆成多条字幕，每条严格2行，时间均分"""
        text = text.strip()
        
        # 先模拟换行，计算实际需要几条字幕
        blocks = []
        remaining = text
        while remaining:
            # 第一行
            if len(remaining) <= MAX_CHARS:
                blocks.append(remaining)
                break
            break1 = find_break_point(remaining, MAX_CHARS)
            line1 = remaining[:break1].strip()
            rest = remaining[break1:].strip()
            
            # 第二行
            if len(rest) <= MAX_CHARS:
                blocks.append(line1 + ' ' + rest)
                break
            break2 = find_break_point(rest, MAX_CHARS)
            line2 = rest[:break2].strip()
            blocks.append(line1 + ' ' + line2)
            remaining = rest[break2:].strip()
        
        # 时间均分
        duration = end_sec - start_sec
        time_per_block = duration / len(blocks)
        
        result = []
        for i, block in enumerate(blocks):
            block_start = start_sec + i * time_per_block
            block_end = start_sec + (i + 1) * time_per_block
            result.append((block, block_start, block_end))
        
        return result
    
    ass_header = f"""[Script Info]
Title: Subtitles
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,PingFang SC,{font_size},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,{margin_bottom},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    def sec_to_ass_time(sec):
        """秒数转ASS时间格式"""
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        cs = int((sec % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"
    
    events = []
    blocks = re.split(r'\n\n+', srt_content.strip())
    
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) >= 3:
            time_line = lines[1]
            text = ' '.join(lines[2:]).replace('\n', ' ')
            # 标点符号替换为空格，便于换行分割
            text = re.sub(r'[，。、：；？！,.:;?!""''「」『』【】（）()《》]', ' ', text)
            # 合并多个空格为一个
            text = re.sub(r'\s+', ' ', text).strip()
            
            match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> (\d{2}):(\d{2}):(\d{2}),(\d{3})', time_line)
            if match:
                sh, sm, ss, sms = match.groups()[:4]
                eh, em, es, ems = match.groups()[4:]
                start_sec = int(sh) * 3600 + int(sm) * 60 + int(ss) + int(sms) / 1000
                end_sec = int(eh) * 3600 + int(em) * 60 + int(es) + int(ems) / 1000
                
                # 长文本拆成多条字幕
                sub_blocks = split_long_text(text, start_sec, end_sec)
                for sub_text, sub_start, sub_end in sub_blocks:
                    formatted_text = wrap_text_2lines(sub_text)
                    start = sec_to_ass_time(sub_start)
                    end = sec_to_ass_time(sub_end)
                    events.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{formatted_text}")
    
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.write(ass_header + '\n'.join(events))


def add_bgm(video_path, output_path, volume=0.08, bgm_path=None):
    """添加背景音乐"""
    print(f"\n[4/4] 添加BGM")
    
    if bgm_path is None:
        bgm_path = BGM_DEFAULT
    bgm_path = Path(bgm_path)
    
    if not bgm_path.exists():
        print(f"  ⚠ BGM文件不存在: {bgm_path}")
        return video_path
    
    cmd = [
        'ffmpeg', '-y', '-i', str(video_path),
        '-stream_loop', '-1', '-i', str(bgm_path),
        '-filter_complex',
        f"[1:a]volume={volume}[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]",
        '-map', '0:v', '-map', '[aout]',
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', str(output_path)
    ]
    run_cmd(cmd, "添加BGM")
    print(f"  ✓ 最终视频: {get_duration(output_path):.1f}秒")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='视频生成器')
    parser.add_argument('config', help='配置文件路径 (YAML)')
    parser.add_argument('--no-outro', action='store_true', help='不添加片尾')
    parser.add_argument('--no-bgm', action='store_true', help='不添加BGM')
    parser.add_argument('--fade', type=float, default=0.5, help='转场时长(秒)')
    parser.add_argument('--bgm-volume', type=float, default=0.08, help='BGM音量')
    parser.add_argument('--bgm', type=str, default=None, help='自定义BGM路径，可选: epic')
    parser.add_argument('--ratio', type=str, default='16:9', 
                        help=f'视频比例，支持: {", ".join(VALID_ASPECT_RATIOS)}')
    parser.add_argument('--srt', type=str, default=None, help='字幕文件路径(SRT格式)')
    args = parser.parse_args()
    
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"配置文件不存在: {config_path}")
        sys.exit(1)
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    work_dir = config_path.parent
    output_path = work_dir / config.get('output', 'output.mp4')
    
    if args.ratio == '16:9' and 'ratio' in config:
        args.ratio = config['ratio']
    
    if 'bgm_volume' in config and args.bgm_volume == 0.08:
        args.bgm_volume = config['bgm_volume']
    
    if args.ratio not in VALID_ASPECT_RATIOS:
        print(f"错误: 不支持的比例 '{args.ratio}'")
        print(f"支持的比例: {', '.join(VALID_ASPECT_RATIOS)}")
        sys.exit(1)
    
    scenes = config.get('scenes', [])
    if not scenes:
        print("配置文件中没有 scenes")
        sys.exit(1)
    
    images = []
    durations = []
    audio_files = []
    
    for scene in scenes:
        audio = work_dir / scene['audio']
        if not audio.exists():
            print(f"音频不存在: {audio}")
            sys.exit(1)
        audio_files.append(audio)
        
        if 'images' in scene:
            for img_cfg in scene['images']:
                img = work_dir / img_cfg['file']
                if not img.exists():
                    print(f"图片不存在: {img}")
                    sys.exit(1)
                images.append(img)
                durations.append(img_cfg['duration'])
        else:
            img = work_dir / scene['image']
            if not img.exists():
                print(f"图片不存在: {img}")
                sys.exit(1)
            images.append(img)
            durations.append(get_duration(audio))
    
    total_audio_duration = sum(get_duration(af) for af in audio_files)
    total_image_duration = sum(durations)
    
    if total_image_duration < total_audio_duration:
        gap = total_audio_duration - total_image_duration + 0.5
        durations[-1] += gap
        print(f"\n⚠ 图片时长({total_image_duration:.1f}s) < 音频时长({total_audio_duration:.1f}s)")
        print(f"  自动拉伸最后一张图片 +{gap:.1f}s")
    
    print(f"\n{'='*50}")
    print(f"视频生成器")
    print(f"{'='*50}")
    print(f"场景数: {len(scenes)}")
    print(f"音频时长: {total_audio_duration:.1f}秒")
    print(f"视频时长: {sum(durations):.1f}秒")
    print(f"转场: {args.fade}秒 淡入淡出")
    print(f"片尾: {'是' if not args.no_outro else '否'}")
    print(f"BGM: {'是' if not args.no_bgm else '否'}")
    
    temp_dir = work_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    
    video_only = temp_dir / "video_only.mp4"
    generate_video_with_transitions(images, durations, video_only, args.fade, args.ratio)
    
    audio_merged = temp_dir / "audio_merged.m4a"
    merge_audio(audio_files, audio_merged)
    
    video_with_audio = temp_dir / "video_with_audio.mp4"
    combine_video_audio(video_only, audio_merged, video_with_audio)
    
    current_video = video_with_audio
    
    if args.srt:
        srt_path = work_dir / args.srt if not Path(args.srt).is_absolute() else Path(args.srt)
        video_with_subs = temp_dir / "video_with_subs.mp4"
        current_video = burn_subtitles(current_video, srt_path, video_with_subs, args.ratio)
    
    if not args.no_outro:
        video_with_outro = temp_dir / "video_with_outro.mp4"
        current_video = append_outro(current_video, video_with_outro, args.fade, args.ratio)
    
    if not args.no_bgm:
        bgm_path = None
        if args.bgm:
            if args.bgm == 'epic':
                bgm_path = BGM_EPIC
            else:
                bgm_path = Path(args.bgm)
        add_bgm(current_video, output_path, args.bgm_volume, bgm_path)
    else:
        subprocess.run(['cp', str(current_video), str(output_path)])
    
    print(f"\n{'='*50}")
    print(f"✅ 完成: {output_path}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    main()
