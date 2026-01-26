#!/usr/bin/env python3
"""
生成通用片尾动画
支持三种尺寸：16:9、3:4、9:16

用法:
    # 16:9 横版（默认）
    manim -qh --format=mp4 --fps=30 -o outro.mp4 outro_generator.py OutroAnimation
    
    # 3:4 竖版
    manim -qh --format=mp4 --fps=30 -o outro_3x4.mp4 outro_generator.py OutroAnimation3x4
    
    # 9:16 竖版（手机全屏）
    manim -qh --format=mp4 --fps=30 -o outro_9x16.mp4 outro_generator.py OutroAnimation9x16

加语音（每种尺寸都要加）:
    edge-tts --text "点关注，不迷路！" --voice zh-CN-YunxiNeural --rate="+10%" --write-media outro_voice.mp3
    ffmpeg -y -i outro.mp4 -i outro_voice.mp3 -filter_complex "[1:a]adelay=1000|1000,apad=whole_dur=5.2[aout]" -map 0:v -map "[aout]" -c:v copy -c:a aac outro_with_voice.mp4
    mv outro_with_voice.mp4 outro.mp4
"""
from manim import *
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(SCRIPT_DIR, "logo.jpg")


class OutroAnimation(Scene):
    """16:9 横版片尾"""
    def construct(self):
        self.camera.background_color = "#1a1a2e"
        
        qr_code = ImageMobject(LOGO_PATH)
        qr_code.scale(1.8)
        qr_code.shift(UP * 0.8)
        
        title = Text("点点关注  一起学 AI", font="PingFang SC", font_size=48, color=WHITE)
        title.next_to(qr_code, DOWN, buff=0.6)
        
        self.play(GrowFromCenter(qr_code), run_time=0.8)
        self.play(Write(title), run_time=1.0)
        self.play(qr_code.animate.scale(1.05), rate_func=there_and_back, run_time=0.4)
        self.wait(3)


class OutroAnimation3x4(Scene):
    """3:4 竖版片尾"""
    def construct(self):
        config.pixel_width = 1080
        config.pixel_height = 1440
        config.frame_width = 8
        config.frame_height = 10.67
        
        self.camera.background_color = "#1a1a2e"
        
        qr_code = ImageMobject(LOGO_PATH)
        qr_code.scale(2.2)
        qr_code.shift(UP * 1.5)
        
        title = Text("点点关注  一起学 AI", font="PingFang SC", font_size=42, color=WHITE)
        title.next_to(qr_code, DOWN, buff=0.8)
        
        self.play(GrowFromCenter(qr_code), run_time=0.8)
        self.play(Write(title), run_time=1.0)
        self.play(qr_code.animate.scale(1.05), rate_func=there_and_back, run_time=0.4)
        self.wait(3)


class OutroAnimation9x16(Scene):
    """9:16 竖版片尾（手机全屏）"""
    def construct(self):
        config.pixel_width = 1080
        config.pixel_height = 1920
        config.frame_width = 8
        config.frame_height = 14.22
        
        self.camera.background_color = "#1a1a2e"
        
        qr_code = ImageMobject(LOGO_PATH)
        qr_code.scale(2.5)
        qr_code.shift(UP * 2)
        
        title = Text("点点关注  一起学 AI", font="PingFang SC", font_size=40, color=WHITE)
        title.next_to(qr_code, DOWN, buff=1.0)
        
        self.play(GrowFromCenter(qr_code), run_time=0.8)
        self.play(Write(title), run_time=1.0)
        self.play(qr_code.animate.scale(1.05), rate_func=there_and_back, run_time=0.4)
        self.wait(3)


class OutroAnimation1x1(Scene):
    """1:1 正方形片尾"""
    def construct(self):
        config.pixel_width = 1024
        config.pixel_height = 1024
        config.frame_width = 8
        config.frame_height = 8
        
        self.camera.background_color = "#1a1a2e"
        
        qr_code = ImageMobject(LOGO_PATH)
        qr_code.scale(2.0)
        qr_code.shift(UP * 0.5)
        
        title = Text("点点关注  一起学 AI", font="PingFang SC", font_size=44, color=WHITE)
        title.next_to(qr_code, DOWN, buff=0.6)
        
        self.play(GrowFromCenter(qr_code), run_time=0.8)
        self.play(Write(title), run_time=1.0)
        self.play(qr_code.animate.scale(1.05), rate_func=there_and_back, run_time=0.4)
        self.wait(3)


class OutroAnimation2x3(Scene):
    """2:3 竖版片尾"""
    def construct(self):
        config.pixel_width = 832
        config.pixel_height = 1248
        config.frame_width = 8
        config.frame_height = 12
        
        self.camera.background_color = "#1a1a2e"
        
        qr_code = ImageMobject(LOGO_PATH)
        qr_code.scale(2.0)
        qr_code.shift(UP * 1.2)
        
        title = Text("点点关注  一起学 AI", font="PingFang SC", font_size=38, color=WHITE)
        title.next_to(qr_code, DOWN, buff=0.8)
        
        self.play(GrowFromCenter(qr_code), run_time=0.8)
        self.play(Write(title), run_time=1.0)
        self.play(qr_code.animate.scale(1.05), rate_func=there_and_back, run_time=0.4)
        self.wait(3)


class OutroAnimation3x2(Scene):
    """3:2 横版片尾"""
    def construct(self):
        config.pixel_width = 1248
        config.pixel_height = 832
        config.frame_width = 12
        config.frame_height = 8
        
        self.camera.background_color = "#1a1a2e"
        
        qr_code = ImageMobject(LOGO_PATH)
        qr_code.scale(1.6)
        qr_code.shift(UP * 0.6)
        
        title = Text("点点关注  一起学 AI", font="PingFang SC", font_size=46, color=WHITE)
        title.next_to(qr_code, DOWN, buff=0.5)
        
        self.play(GrowFromCenter(qr_code), run_time=0.8)
        self.play(Write(title), run_time=1.0)
        self.play(qr_code.animate.scale(1.05), rate_func=there_and_back, run_time=0.4)
        self.wait(3)


class OutroAnimation4x3(Scene):
    """4:3 横版片尾"""
    def construct(self):
        config.pixel_width = 1440
        config.pixel_height = 1080
        config.frame_width = 10.67
        config.frame_height = 8
        
        self.camera.background_color = "#1a1a2e"
        
        qr_code = ImageMobject(LOGO_PATH)
        qr_code.scale(1.8)
        qr_code.shift(UP * 0.7)
        
        title = Text("点点关注  一起学 AI", font="PingFang SC", font_size=46, color=WHITE)
        title.next_to(qr_code, DOWN, buff=0.6)
        
        self.play(GrowFromCenter(qr_code), run_time=0.8)
        self.play(Write(title), run_time=1.0)
        self.play(qr_code.animate.scale(1.05), rate_func=there_and_back, run_time=0.4)
        self.wait(3)


class OutroAnimation4x5(Scene):
    """4:5 竖版片尾（Instagram）"""
    def construct(self):
        config.pixel_width = 864
        config.pixel_height = 1080
        config.frame_width = 8
        config.frame_height = 10
        
        self.camera.background_color = "#1a1a2e"
        
        qr_code = ImageMobject(LOGO_PATH)
        qr_code.scale(2.0)
        qr_code.shift(UP * 1.0)
        
        title = Text("点点关注  一起学 AI", font="PingFang SC", font_size=36, color=WHITE)
        title.next_to(qr_code, DOWN, buff=0.7)
        
        self.play(GrowFromCenter(qr_code), run_time=0.8)
        self.play(Write(title), run_time=1.0)
        self.play(qr_code.animate.scale(1.05), rate_func=there_and_back, run_time=0.4)
        self.wait(3)


class OutroAnimation5x4(Scene):
    """5:4 横版片尾"""
    def construct(self):
        config.pixel_width = 1080
        config.pixel_height = 864
        config.frame_width = 10
        config.frame_height = 8
        
        self.camera.background_color = "#1a1a2e"
        
        qr_code = ImageMobject(LOGO_PATH)
        qr_code.scale(1.7)
        qr_code.shift(UP * 0.6)
        
        title = Text("点点关注  一起学 AI", font="PingFang SC", font_size=44, color=WHITE)
        title.next_to(qr_code, DOWN, buff=0.5)
        
        self.play(GrowFromCenter(qr_code), run_time=0.8)
        self.play(Write(title), run_time=1.0)
        self.play(qr_code.animate.scale(1.05), rate_func=there_and_back, run_time=0.4)
        self.wait(3)


class OutroAnimation21x9(Scene):
    """21:9 超宽屏片尾"""
    def construct(self):
        config.pixel_width = 1536
        config.pixel_height = 672
        config.frame_width = 18.29
        config.frame_height = 8
        
        self.camera.background_color = "#1a1a2e"
        
        qr_code = ImageMobject(LOGO_PATH)
        qr_code.scale(1.3)
        qr_code.shift(LEFT * 4)
        
        title = Text("点点关注  一起学 AI", font="PingFang SC", font_size=52, color=WHITE)
        title.shift(RIGHT * 2)
        
        self.play(GrowFromCenter(qr_code), run_time=0.8)
        self.play(Write(title), run_time=1.0)
        self.play(qr_code.animate.scale(1.05), rate_func=there_and_back, run_time=0.4)
        self.wait(3)


if __name__ == "__main__":
    print("生成片尾动画...")
    print("\n16:9 横版:")
    print("  manim -qh --format=mp4 --fps=30 -o outro.mp4 outro_generator.py OutroAnimation")
    print("\n3:4 竖版:")
    print("  manim -qh --format=mp4 --fps=30 -o outro_3x4.mp4 outro_generator.py OutroAnimation3x4")
    print("\n9:16 竖版:")
    print("  manim -qh --format=mp4 --fps=30 -o outro_9x16.mp4 outro_generator.py OutroAnimation9x16")
