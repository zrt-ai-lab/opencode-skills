#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音 Cookie 有效性检查脚本
"""

import asyncio
import os
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("错误：未安装 playwright")
    print("请运行：pip install playwright && playwright install chromium")
    exit(1)


# Cookie 存储路径
COOKIE_DIR = Path(__file__).parent.parent / "cookies"
COOKIE_FILE = COOKIE_DIR / "douyin.json"


async def check_cookie():
    """检查抖音 Cookie 是否有效"""
    
    print("=" * 50)
    print("抖音 Cookie 有效性检查")
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
            
            # 访问抖音创作者中心上传页面
            await page.goto("https://creator.douyin.com/creator-micro/content/upload")
            
            # 等待页面加载
            try:
                await page.wait_for_url(
                    "https://creator.douyin.com/creator-micro/content/upload",
                    timeout=10000
                )
            except:
                pass
            
            # 检查是否需要登录
            login_required = False
            
            # 检查是否出现登录提示
            if await page.get_by_text('手机号登录').count() > 0:
                login_required = True
            elif await page.get_by_text('扫码登录').count() > 0:
                login_required = True
            elif 'login' in page.url.lower():
                login_required = True
            
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
