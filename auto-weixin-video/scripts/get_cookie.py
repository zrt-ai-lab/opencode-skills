#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信视频号登录 Cookie 获取脚本
使用微信扫码登录，保存 Cookie 供后续自动化使用
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


async def get_weixin_cookie():
    """获取微信视频号登录 Cookie"""
    
    # 确保 cookies 目录存在
    COOKIE_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 50)
    print("微信视频号登录 Cookie 获取")
    print("=" * 50)
    print()
    print("即将打开浏览器，请使用微信扫码登录")
    print("登录成功后，请点击浏览器调试窗口中的「继续」按钮")
    print()
    
    async with async_playwright() as p:
        # 启动浏览器（非无头模式，方便扫码）
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # 打开视频号创作者中心
        print("正在打开微信视频号创作者中心，请稍候...")
        try:
            await page.goto("https://channels.weixin.qq.com", timeout=120000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"页面加载较慢，但已打开，继续操作: {e}")
        
        print("请在浏览器中使用微信扫码登录...")
        print("登录成功后，点击调试窗口的「继续」按钮保存 Cookie")
        print()
        
        # 暂停，等待用户手动操作（扫码登录）
        await page.pause()
        
        # 保存 Cookie
        await context.storage_state(path=str(COOKIE_FILE))
        
        print()
        print("=" * 50)
        print(f"✅ Cookie 已保存到: {COOKIE_FILE}")
        print("=" * 50)
        
        await browser.close()


def main():
    asyncio.run(get_weixin_cookie())


if __name__ == "__main__":
    main()
