#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信视频号 Cookie 有效性检查脚本
"""

import asyncio
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("错误：未安装 playwright")
    print("请运行：pip install playwright && playwright install chromium")
    exit(1)


# Cookie 存储路径
COOKIE_DIR = Path(__file__).parent.parent / "cookies"
COOKIE_FILE = COOKIE_DIR / "weixin_video.json"


async def check_cookie():
    """检查微信视频号 Cookie 是否有效"""
    
    print("=" * 50)
    print("微信视频号 Cookie 有效性检查")
    print("=" * 50)
    print()
    
    # 检查 Cookie 文件是否存在
    if not COOKIE_FILE.exists():
        print(f"❌ Cookie 文件不存在: {COOKIE_FILE}")
        print()
        print("请先运行 get_cookie.py 获取 Cookie")
        return False
    
    print(f"Cookie 文件: {COOKIE_FILE}")
    print("正在验证 Cookie 有效性...")
    print()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        try:
            # 使用保存的 Cookie 创建上下文
            context = await browser.new_context(storage_state=str(COOKIE_FILE))
            page = await context.new_page()
            
            # 访问视频号创作者中心发布页面
            await page.goto("https://channels.weixin.qq.com/platform/post/create", timeout=30000)
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 检查是否需要登录（出现微信小店提示表示未登录）
            login_required = False
            
            try:
                # 如果出现登录相关元素，说明 Cookie 失效
                if await page.locator('div.title-name:has-text("微信小店")').count() > 0:
                    login_required = True
                elif await page.get_by_text('扫码登录').count() > 0:
                    login_required = True
            except:
                pass
            
            await context.close()
            await browser.close()
            
            if login_required:
                print("❌ Cookie 已失效，需要重新登录")
                print()
                print("请运行 get_cookie.py 重新获取 Cookie")
                return False
            else:
                print("✅ Cookie 有效！可以正常使用")
                return True
                
        except Exception as e:
            print(f"❌ 检查过程出错: {e}")
            await browser.close()
            return False


def main():
    result = asyncio.run(check_cookie())
    exit(0 if result else 1)


if __name__ == "__main__":
    main()
