#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信视频号视频发布脚本
支持上传视频、设置标题话题、定时发布、原创声明等功能
"""

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    from playwright.async_api import async_playwright, Page
except ImportError:
    print("错误：未安装 playwright")
    print("请运行：pip install playwright && playwright install chromium")
    sys.exit(1)


# Cookie 存储路径
COOKIE_DIR = Path(__file__).parent.parent / "cookies"
COOKIE_FILE = COOKIE_DIR / "weixin_video.json"


def format_short_title(title: str) -> str:
    """生成短标题（6-16字）"""
    # 定义允许的特殊字符
    allowed_special_chars = "《》"":+?%°"
    
    # 移除不允许的特殊字符
    filtered_chars = [
        char if char.isalnum() or char in allowed_special_chars 
        else ' ' if char == ',' 
        else '' 
        for char in title
    ]
    formatted_string = ''.join(filtered_chars)
    
    # 调整字符串长度
    if len(formatted_string) > 16:
        formatted_string = formatted_string[:16]
    elif len(formatted_string) < 6:
        formatted_string += ' ' * (6 - len(formatted_string))
    
    return formatted_string


class WeixinVideoUploader:
    """微信视频号上传器"""
    
    def __init__(
        self,
        video_path: str,
        title: str,
        tags: List[str] = None,
        original: bool = False,
        category: str = None,
        schedule_time: datetime = None,
        is_draft: bool = False,
        headless: bool = False
    ):
        self.video_path = Path(video_path)
        self.title = title
        self.tags = tags or []
        self.original = original
        self.category = category
        self.schedule_time = schedule_time
        self.is_draft = is_draft
        self.headless = headless
        
        # 验证文件
        if not self.video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {self.video_path}")
    
    async def upload(self) -> bool:
        """执行上传"""
        
        print("=" * 60)
        print("微信视频号发布")
        print("=" * 60)
        print()
        print(f"视频文件: {self.video_path}")
        print(f"标题: {self.title}")
        print(f"话题: {', '.join(self.tags) if self.tags else '无'}")
        print(f"声明原创: {'是' if self.original else '否'}")
        print(f"发布时间: {self.schedule_time.strftime('%Y-%m-%d %H:%M') if self.schedule_time else '立即发布'}")
        print(f"模式: {'保存草稿' if self.is_draft else '发布'}")
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
                
                # 进入发布页面
                print("[1/7] 打开视频号创作者中心...")
                await page.goto("https://channels.weixin.qq.com/platform/post/create", timeout=60000)
                await page.wait_for_url("https://channels.weixin.qq.com/platform/post/create")
                
                # 上传视频
                print("[2/7] 上传视频文件...")
                file_input = page.locator('input[type="file"]')
                await file_input.set_input_files(str(self.video_path))
                
                # 填写标题和话题
                print("[3/7] 填写标题和话题...")
                await self._fill_title_and_tags(page)
                
                # 添加到合集（如果有）
                print("[4/7] 检查合集...")
                await self._add_to_collection(page)
                
                # 原创声明（默认执行）
                print("[5/7] 声明原创...")
                await self._declare_original(page)
                
                # 等待上传完成
                print("[6/7] 等待视频上传完成...")
                await self._wait_for_upload_complete(page)
                
                # 设置定时发布
                if self.schedule_time:
                    print(f"[7/7] 设置定时发布: {self.schedule_time.strftime('%Y-%m-%d %H:%M')}...")
                    await self._set_schedule_time(page)
                else:
                    print("[7/7] 准备发布...")
                
                # 添加短标题
                await self._add_short_title(page)
                
                # 点击发布/保存草稿
                await self._publish(page)
                
                # 保存更新的 Cookie
                await context.storage_state(path=str(COOKIE_FILE))
                
                print()
                print("=" * 60)
                if self.is_draft:
                    print("✅ 视频已保存为草稿！")
                else:
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
    
    async def _fill_title_and_tags(self, page: Page):
        """填写标题和话题"""
        await page.locator("div.input-editor").click()
        await page.keyboard.type(self.title)
        await page.keyboard.press("Enter")
        
        for tag in self.tags:
            await page.keyboard.type("#" + tag)
            await page.keyboard.press("Space")
            await asyncio.sleep(0.3)
        
        if self.tags:
            print(f"   已添加 {len(self.tags)} 个话题")
    
    async def _add_to_collection(self, page: Page):
        """添加到合集"""
        try:
            collection_elements = page.get_by_text("添加到合集").locator("xpath=following-sibling::div").locator(
                '.option-list-wrap > div')
            if await collection_elements.count() > 1:
                await page.get_by_text("添加到合集").locator("xpath=following-sibling::div").click()
                await collection_elements.first.click()
                print("   已添加到合集")
        except:
            print("   无可用合集")
    
    async def _declare_original(self, page: Page):
        """声明原创 - 完整流程：勾选 -> 弹窗选择类型 -> 勾选协议 -> 点击声明原创"""
        try:
            await asyncio.sleep(1)
            
            # 第一步：找到并勾选"声明原创"复选框
            # 尝试多种定位方式
            original_checkbox = None
            
            # 方式1: 通过 label 文字
            if await page.get_by_label("视频为原创").count():
                original_checkbox = page.get_by_label("视频为原创")
            # 方式2: 通过文字定位附近的 checkbox
            elif await page.locator('text="声明原创"').count():
                parent = page.locator('text="声明原创"').locator('..')
                original_checkbox = parent.locator('input[type="checkbox"]')
            # 方式3: ant-checkbox 样式
            elif await page.locator('.declare-original-checkbox').count():
                original_checkbox = page.locator('.declare-original-checkbox input')
            
            if original_checkbox and await original_checkbox.count():
                if not await original_checkbox.is_checked():
                    await original_checkbox.click()
                    print("   已勾选声明原创")
                    await asyncio.sleep(1)
            
            # 第二步：处理弹窗 - 选择原创类型
            # 等待弹窗出现
            await asyncio.sleep(1)
            
            # 检查是否有弹窗
            modal_visible = False
            modal_selectors = [
                'div.declare-original-dialog',
                'div.weui-desktop-dialog',
                'div.ant-modal-content',
                'div[class*="modal"]'
            ]
            
            for selector in modal_selectors:
                if await page.locator(selector).count() > 0:
                    modal_visible = True
                    break
            
            if modal_visible:
                print("   检测到弹窗，处理中...")
                
                # 选择原创类型（如果有下拉框）
                type_dropdown = page.locator('div.original-type-form .form-content, div[class*="select"], .weui-desktop-dropdown')
                if await type_dropdown.count():
                    await type_dropdown.first.click()
                    await asyncio.sleep(0.5)
                    # 选择第一个选项
                    options = page.locator('[role="option"], .weui-desktop-dropdown__list-ele, li[class*="option"]')
                    if await options.count():
                        await options.first.click()
                        print("   已选择原创类型")
                        await asyncio.sleep(0.5)
                
                # 勾选弹窗里的协议复选框
                dialog_checkboxes = page.locator('div[class*="modal"] input[type="checkbox"]:not(:checked), div[class*="dialog"] input[type="checkbox"]:not(:checked)')
                count = await dialog_checkboxes.count()
                for i in range(count):
                    try:
                        cb = dialog_checkboxes.nth(i)
                        if await cb.is_visible():
                            await cb.click()
                            await asyncio.sleep(0.3)
                    except:
                        pass
                
                # 也尝试点击 label 来勾选
                agreement_labels = page.locator('label:has-text("我已阅读"), label:has-text("同意")')
                if await agreement_labels.count():
                    for i in range(await agreement_labels.count()):
                        try:
                            label = agreement_labels.nth(i)
                            if await label.is_visible():
                                await label.click()
                                await asyncio.sleep(0.3)
                        except:
                            pass
                
                # 第三步：点击"声明原创"确认按钮
                await asyncio.sleep(0.5)
                confirm_buttons = [
                    'button:has-text("声明原创")',
                    'button:has-text("确认")',
                    'button:has-text("确定")',
                    'button.confirm',
                    'button.ant-btn-primary'
                ]
                
                for btn_selector in confirm_buttons:
                    btn = page.locator(btn_selector)
                    if await btn.count():
                        visible_btn = btn.first
                        if await visible_btn.is_visible() and await visible_btn.is_enabled():
                            await visible_btn.click()
                            print("   已点击声明原创确认")
                            break
                
                await asyncio.sleep(1)
            
            print("   原创声明完成")
            
        except Exception as e:
            print(f"   原创声明失败: {e}")
    
    async def _wait_for_upload_complete(self, page: Page):
        """等待视频上传完成"""
        max_attempts = 120
        for i in range(max_attempts):
            try:
                # 检查发布按钮是否可用
                publish_btn = page.get_by_role("button", name="发表")
                if "weui-desktop-btn_disabled" not in await publish_btn.get_attribute('class'):
                    print("   视频上传完成")
                    return
                
                # 检查上传错误
                if await page.locator('div.status-msg.error').count():
                    raise Exception("视频上传出错")
                
                if i % 10 == 0:
                    print(f"   正在上传... ({i}s)")
                await asyncio.sleep(1)
            except:
                await asyncio.sleep(1)
        
        raise TimeoutError("视频上传超时")
    
    async def _set_schedule_time(self, page: Page):
        """设置定时发布"""
        # 点击定时发布
        label_element = page.locator("label").filter(has_text="定时").nth(1)
        await label_element.click()
        
        await page.click('input[placeholder="请选择发表时间"]')
        
        # 处理月份
        str_month = str(self.schedule_time.month).zfill(2)
        current_month = f"{str_month}月"
        page_month = await page.inner_text('span.weui-desktop-picker__panel__label:has-text("月")')
        
        if page_month != current_month:
            await page.click('button.weui-desktop-btn__icon__right')
        
        # 选择日期
        elements = await page.query_selector_all('table.weui-desktop-picker__table a')
        for element in elements:
            if 'weui-desktop-picker__disabled' in await element.evaluate('el => el.className'):
                continue
            text = await element.inner_text()
            if text.strip() == str(self.schedule_time.day):
                await element.click()
                break
        
        # 输入小时
        await page.click('input[placeholder="请选择时间"]')
        await page.keyboard.press("Control+KeyA")
        await page.keyboard.type(str(self.schedule_time.hour))
        
        # 点击其他区域使设置生效
        await page.locator("div.input-editor").click()
    
    async def _add_short_title(self, page: Page):
        """添加短标题"""
        try:
            short_title_element = page.get_by_text("短标题", exact=True).locator("..").locator(
                "xpath=following-sibling::div").locator('span input[type="text"]')
            if await short_title_element.count():
                short_title = format_short_title(self.title)
                await short_title_element.fill(short_title)
        except:
            pass
    
    async def _check_declarations(self, page: Page):
        """勾选页面上的声明/协议复选框"""
        try:
            # 查找所有未勾选的 checkbox 并勾选
            checkboxes = page.locator('input[type="checkbox"]:not(:checked)')
            count = await checkboxes.count()
            for i in range(count):
                try:
                    checkbox = checkboxes.nth(i)
                    if await checkbox.is_visible():
                        await checkbox.click()
                        await asyncio.sleep(0.3)
                except:
                    pass
            
            # 常见的声明文字，尝试点击其 label
            declarations = [
                "我已阅读并同意",
                "我确认",
                "我声明",
                "本人承诺"
            ]
            for text in declarations:
                try:
                    label = page.locator(f'label:has-text("{text}")')
                    if await label.count() > 0 and await label.first.is_visible():
                        checkbox = label.first.locator('input[type="checkbox"]')
                        if await checkbox.count() > 0 and not await checkbox.is_checked():
                            await checkbox.click()
                            print(f"   已勾选: {text}...")
                except:
                    pass
            
            # 尝试点击 ant-checkbox 类型的复选框
            ant_checkboxes = page.locator('.ant-checkbox:not(.ant-checkbox-checked)')
            count = await ant_checkboxes.count()
            for i in range(count):
                try:
                    cb = ant_checkboxes.nth(i)
                    if await cb.is_visible():
                        await cb.click()
                        await asyncio.sleep(0.3)
                except:
                    pass
                    
        except Exception as e:
            print(f"   勾选声明时出错: {e}")
    
    async def _publish(self, page: Page):
        """点击发布/保存草稿"""
        # 先勾选所有声明
        print("   勾选声明...")
        await self._check_declarations(page)
        await asyncio.sleep(1)
        
        max_attempts = 30
        for _ in range(max_attempts):
            try:
                if self.is_draft:
                    draft_button = page.locator('div.form-btns button:has-text("保存草稿")')
                    if await draft_button.count():
                        await draft_button.click()
                    await page.wait_for_url("**/post/list**", timeout=5000)
                    return
                else:
                    publish_button = page.locator('div.form-btns button:has-text("发表")')
                    if await publish_button.count():
                        await publish_button.click()
                    await page.wait_for_url("https://channels.weixin.qq.com/platform/post/list", timeout=5000)
                    return
            except:
                # 可能还有未勾选的声明，再试一次
                await self._check_declarations(page)
                await asyncio.sleep(1)
        
        raise TimeoutError("发布超时")


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="微信视频号自动发布")
    
    parser.add_argument("-v", "--video", required=True, help="视频文件路径")
    parser.add_argument("-t", "--title", required=True, help="视频标题")
    parser.add_argument("-g", "--tags", default="", help="话题标签，逗号分隔")
    parser.add_argument("-o", "--original", action="store_true", help="声明原创")
    parser.add_argument("-c", "--category", default=None, help="原创类型")
    parser.add_argument("-s", "--schedule", default=None, help="定时发布时间 YYYY-MM-DD HH:MM")
    parser.add_argument("--draft", action="store_true", help="保存为草稿")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
    
    schedule_time = None
    if args.schedule:
        try:
            schedule_time = datetime.strptime(args.schedule, "%Y-%m-%d %H:%M")
        except ValueError:
            print("❌ 时间格式错误，应为 YYYY-MM-DD HH:MM")
            sys.exit(1)
    
    try:
        uploader = WeixinVideoUploader(
            video_path=args.video,
            title=args.title,
            tags=tags,
            original=args.original,
            category=args.category,
            schedule_time=schedule_time,
            is_draft=args.draft,
            headless=args.headless
        )
        
        success = asyncio.run(uploader.upload())
        sys.exit(0 if success else 1)
        
    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
