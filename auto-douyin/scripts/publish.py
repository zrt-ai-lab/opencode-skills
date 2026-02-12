#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音视频发布脚本
支持上传视频、设置标题话题、定时发布等功能
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from playwright.async_api import async_playwright, Page, BrowserContext
except ImportError:
    print("错误：未安装 playwright")
    print("请运行：pip install playwright && playwright install chromium")
    sys.exit(1)


# Cookie 存储路径
COOKIE_DIR = Path(__file__).parent.parent / "cookies"
COOKIE_FILE = COOKIE_DIR / "douyin.json"


class DouyinUploader:
    """抖音视频上传器"""
    
    def __init__(
        self,
        video_path: str,
        title: str,
        tags: List[str] = None,
        cover_path: str = None,
        schedule_time: datetime = None,
        headless: bool = False
    ):
        self.video_path = Path(video_path)
        self.title = title[:30]  # 抖音标题最多30字
        self.tags = tags or []
        self.cover_path = Path(cover_path) if cover_path else None
        self.schedule_time = schedule_time
        self.headless = headless
        
        # 验证文件
        if not self.video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {self.video_path}")
        if self.cover_path and not self.cover_path.exists():
            raise FileNotFoundError(f"封面文件不存在: {self.cover_path}")
    
    async def upload(self) -> bool:
        """执行上传"""
        
        print("=" * 60)
        print("抖音视频发布")
        print("=" * 60)
        print()
        print(f"视频文件: {self.video_path}")
        print(f"标题: {self.title}")
        print(f"话题: {', '.join(self.tags) if self.tags else '无'}")
        print(f"封面: {self.cover_path if self.cover_path else '自动选择'}")
        print(f"发布时间: {self.schedule_time.strftime('%Y-%m-%d %H:%M') if self.schedule_time else '立即发布'}")
        print()
        
        # 检查 Cookie
        if not COOKIE_FILE.exists():
            print("❌ Cookie 文件不存在，请先运行 get_cookie.py 获取登录凭证")
            return False
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            
            try:
                # 加载 Cookie
                context = await browser.new_context(storage_state=str(COOKIE_FILE))
                page = await context.new_page()
                
                # 进入上传页面
                print("[1/6] 打开抖音创作者中心...")
                await page.goto("https://creator.douyin.com/creator-micro/content/upload", timeout=120000)
                
                # 等待页面加载
                try:
                    await page.wait_for_url(
                        "https://creator.douyin.com/creator-micro/content/upload",
                        timeout=10000
                    )
                except:
                    pass
                
                # 检查登录状态
                if await page.get_by_text('手机号登录').count() > 0 or await page.get_by_text('扫码登录').count() > 0:
                    print("❌ Cookie 已失效，请重新运行 get_cookie.py 获取登录凭证")
                    await browser.close()
                    return False
                
                # 上传视频
                print("[2/6] 上传视频文件...")
                await page.locator("div[class^='container'] input").set_input_files(str(self.video_path))
                
                # 等待跳转到发布页面
                print("[3/6] 等待视频处理...")
                await self._wait_for_publish_page(page)
                
                # 等待视频上传完成
                await self._wait_for_upload_complete(page)
                
                # 填写标题和话题
                print("[4/6] 填写标题和话题...")
                await self._fill_title_and_tags(page)
                
                # 设置封面（如果指定）
                if self.cover_path:
                    print("[5/6] 设置视频封面...")
                    await self._set_cover(page)
                else:
                    print("[5/6] 使用自动推荐封面...")
                
                # 设置定时发布（如果指定）
                if self.schedule_time:
                    print(f"[6/6] 设置定时发布: {self.schedule_time.strftime('%Y-%m-%d %H:%M')}...")
                    await self._set_schedule_time(page)
                else:
                    print("[6/6] 准备立即发布...")
                
                # 点击发布
                await self._publish(page)
                
                # 保存更新的 Cookie
                await context.storage_state(path=str(COOKIE_FILE))
                
                print()
                print("=" * 60)
                print("✅ 视频发布成功！")
                print("=" * 60)
                
                await asyncio.sleep(2)
                await browser.close()
                return True
                
            except Exception as e:
                print(f"❌ 发布失败: {e}")
                import traceback
                traceback.print_exc()
                await browser.close()
                return False
    
    async def _wait_for_publish_page(self, page: Page):
        """等待进入发布页面"""
        max_attempts = 60
        for _ in range(max_attempts):
            try:
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/publish?enter_from=publish_page",
                    timeout=2000
                )
                return
            except:
                pass
            
            try:
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/post/video?enter_from=publish_page",
                    timeout=2000
                )
                return
            except:
                pass
            
            await asyncio.sleep(0.5)
        
        raise TimeoutError("等待发布页面超时")
    
    async def _wait_for_upload_complete(self, page: Page):
        """等待视频上传完成"""
        max_attempts = 120  # 最多等待2分钟
        for i in range(max_attempts):
            # 检查是否出现"重新上传"按钮（表示上传完成）
            if await page.locator('[class^="long-card"] div:has-text("重新上传")').count() > 0:
                print("   视频上传完成")
                return
            
            # 检查上传失败
            if await page.locator('div.progress-div > div:has-text("上传失败")').count() > 0:
                raise Exception("视频上传失败，请检查文件格式")
            
            if i % 10 == 0:
                print(f"   正在上传... ({i}s)")
            await asyncio.sleep(1)
        
        raise TimeoutError("视频上传超时")
    
    async def _fill_title_and_tags(self, page: Page):
        """填写标题和话题"""
        await asyncio.sleep(1)
        
        # 尝试填写标题
        title_input = page.get_by_text('作品标题').locator("..").locator("xpath=following-sibling::div[1]").locator("input")
        if await title_input.count() > 0:
            await title_input.fill(self.title)
        else:
            # 备用方案：直接在编辑区域输入
            title_area = page.locator(".notranslate")
            await title_area.click()
            await page.keyboard.press("Control+KeyA")
            await page.keyboard.press("Delete")
            await page.keyboard.type(self.title)
            await page.keyboard.press("Enter")
        
        # 填写话题标签
        if self.tags:
            css_selector = ".zone-container"
            for tag in self.tags:
                await page.type(css_selector, "#" + tag)
                await page.press(css_selector, "Space")
                await asyncio.sleep(0.3)
            print(f"   已添加 {len(self.tags)} 个话题")
    
    async def _set_cover(self, page: Page):
        """设置视频封面"""
        try:
            await page.click('text="选择封面"')
            await page.wait_for_selector("div.dy-creator-content-modal", timeout=5000)
            await page.click('text="设置竖封面"')
            await asyncio.sleep(2)
            
            # 上传封面图片
            await page.locator("div[class^='semi-upload upload'] >> input.semi-upload-hidden-input").set_input_files(str(self.cover_path))
            await asyncio.sleep(2)
            
            # 点击完成
            await page.locator("div#tooltip-container button:visible:has-text('完成')").click()
            print("   封面设置完成")
            
            # 等待对话框关闭
            await page.wait_for_selector("div.extractFooter", state='detached', timeout=5000)
        except Exception as e:
            print(f"   封面设置失败: {e}，将使用自动推荐封面")
    
    async def _set_schedule_time(self, page: Page):
        """设置定时发布"""
        # 点击定时发布
        label_element = page.locator("[class^='radio']:has-text('定时发布')")
        await label_element.click()
        await asyncio.sleep(1)
        
        # 格式化时间
        time_str = self.schedule_time.strftime("%Y-%m-%d %H:%M")
        
        # 输入时间
        await page.locator('.semi-input[placeholder="日期和时间"]').click()
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.type(time_str)
        await page.keyboard.press("Enter")
        await asyncio.sleep(1)
    
    async def _publish(self, page: Page):
        """点击发布按钮"""
        max_attempts = 30
        for _ in range(max_attempts):
            try:
                publish_button = page.get_by_role('button', name="发布", exact=True)
                if await publish_button.count() > 0:
                    await publish_button.click()
                
                # 等待跳转到管理页面（表示发布成功）
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/manage**",
                    timeout=5000
                )
                return
            except:
                # 处理封面提示
                await self._handle_cover_prompt(page)
                await asyncio.sleep(1)
        
        raise TimeoutError("发布超时")
    
    async def _handle_cover_prompt(self, page: Page):
        """处理封面设置提示"""
        if await page.get_by_text("请设置封面后再发布").first.is_visible():
            print("   检测到需要设置封面，正在选择推荐封面...")
            recommend_cover = page.locator('[class^="recommendCover-"]').first
            if await recommend_cover.count() > 0:
                await recommend_cover.click()
                await asyncio.sleep(1)
                
                # 处理确认弹窗
                if await page.get_by_text("是否确认应用此封面？").first.is_visible():
                    await page.get_by_role("button", name="确定").click()
                    await asyncio.sleep(1)


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="抖音视频自动发布")
    
    parser.add_argument(
        "-v", "--video",
        required=True,
        help="视频文件路径"
    )
    parser.add_argument(
        "-t", "--title",
        required=True,
        help="视频标题（最多30字）"
    )
    parser.add_argument(
        "-g", "--tags",
        default="",
        help="话题标签，逗号分隔（如：干货分享,效率提升）"
    )
    parser.add_argument(
        "-c", "--cover",
        default=None,
        help="封面图片路径（可选，不指定则自动选择）"
    )
    parser.add_argument(
        "-s", "--schedule",
        default=None,
        help="定时发布时间，格式：YYYY-MM-DD HH:MM（可选，不指定则立即发布）"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式运行（不显示浏览器窗口）"
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # 解析话题
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    
    # 解析定时发布时间
    schedule_time = None
    if args.schedule:
        try:
            schedule_time = datetime.strptime(args.schedule, "%Y-%m-%d %H:%M")
        except ValueError:
            print(f"❌ 时间格式错误，应为 YYYY-MM-DD HH:MM，例如：2025-02-01 18:00")
            sys.exit(1)
    
    try:
        uploader = DouyinUploader(
            video_path=args.video,
            title=args.title,
            tags=tags,
            cover_path=args.cover,
            schedule_time=schedule_time,
            headless=args.headless
        )
        
        success = asyncio.run(uploader.upload())
        sys.exit(0 if success else 1)
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
