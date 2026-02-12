#!/usr/bin/env python3
"""
小红书笔记发布脚本 - 浏览器自动化版本
使用 Playwright 模拟人工操作，支持真正可点击的话题标签

使用方法:
    python publish_xhs_browser.py --title "标题" --desc "描述" --images cover.png card_1.png --topics AI工具 程序员

环境变量:
    XHS_COOKIE: 小红书 Cookie 字符串

依赖安装:
    pip install playwright python-dotenv
    playwright install chromium
"""

import argparse
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

try:
    from playwright.async_api import async_playwright, Page, Browser
    from dotenv import load_dotenv
except ImportError as e:
    print(f"缺少依赖: {e}")
    print("请运行: pip install playwright python-dotenv")
    print("然后运行: playwright install chromium")
    sys.exit(1)


def load_cookie() -> str:
    """从 .env 文件加载 Cookie"""
    env_paths = [
        Path.cwd() / '.env',
        Path(__file__).parent.parent / '.env',
        Path(__file__).parent.parent.parent / '.env',
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
    
    cookie = os.getenv('XHS_COOKIE')
    if not cookie:
        print("❌ 错误: 未找到 XHS_COOKIE 环境变量")
        print("请创建 .env 文件，添加: XHS_COOKIE=your_cookie_string_here")
        sys.exit(1)
    
    return cookie


def parse_cookie_to_list(cookie_string: str) -> List[dict]:
    """将 Cookie 字符串解析为 Playwright 格式"""
    cookies = []
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies.append({
                "name": key.strip(),
                "value": value.strip(),
                "domain": ".xiaohongshu.com",
                "path": "/"
            })
    return cookies


def validate_images(image_paths: List[str]) -> List[str]:
    """验证图片文件是否存在"""
    valid_images = []
    for path in image_paths:
        if os.path.exists(path):
            valid_images.append(os.path.abspath(path))
        else:
            print(f"⚠️ 警告: 图片不存在 - {path}")
    
    if not valid_images:
        print("❌ 错误: 没有有效的图片文件")
        sys.exit(1)
    
    return valid_images


class XHSBrowserPublisher:
    """小红书浏览器自动化发布器"""
    
    def __init__(self, cookie: str, headless: bool = False):
        self.cookie = cookie
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def init(self):
        """初始化浏览器"""
        print("🌐 启动浏览器...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # 创建上下文并注入 Cookie
        context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 注入 Cookie
        cookies = parse_cookie_to_list(self.cookie)
        await context.add_cookies(cookies)
        
        self.page = await context.new_page()
        print("✅ 浏览器已启动")
        
    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            print("🔒 浏览器已关闭")
    
    async def goto_creator(self):
        """进入创作者后台"""
        print("📍 进入创作者后台...")
        await self.page.goto('https://creator.xiaohongshu.com/publish/publish', wait_until='networkidle')
        await asyncio.sleep(2)
        
        # 检查是否需要登录
        if 'login' in self.page.url.lower():
            print("❌ 错误: Cookie 已过期，请重新获取")
            await self.close()
            sys.exit(1)
        
        print("✅ 已进入创作者后台")
    
    async def upload_images(self, image_paths: List[str]):
        """上传图片"""
        print(f"📷 上传 {len(image_paths)} 张图片...")
        
        # 等待上传区域出现
        try:
            # 查找文件上传 input
            upload_input = await self.page.wait_for_selector('input[type="file"]', timeout=10000)
            
            # 上传所有图片
            await upload_input.set_input_files(image_paths)
            
            # 等待上传完成
            print("⏳ 等待图片上传...")
            await asyncio.sleep(3)
            
            # 等待所有图片显示
            for i in range(len(image_paths)):
                await asyncio.sleep(1)
            
            print(f"✅ 已上传 {len(image_paths)} 张图片")
            
        except Exception as e:
            print(f"❌ 图片上传失败: {e}")
            raise
    
    async def fill_title(self, title: str):
        """填写标题"""
        print(f"📝 填写标题: {title[:20]}...")
        
        try:
            # 查找标题输入框
            title_input = await self.page.wait_for_selector('input[placeholder*="标题"]', timeout=5000)
            if not title_input:
                title_input = await self.page.wait_for_selector('.title-input input', timeout=5000)
            
            await title_input.fill(title[:20])  # 标题最多20字
            print("✅ 标题已填写")
            
        except Exception as e:
            print(f"⚠️ 标题填写失败，尝试其他方式: {e}")
            # 尝试其他选择器
            try:
                await self.page.fill('[class*="title"] input', title[:20])
                print("✅ 标题已填写（备用方式）")
            except:
                print("❌ 无法找到标题输入框")
    
    async def fill_desc(self, desc: str):
        """填写正文描述"""
        print(f"📝 填写正文...")
        
        try:
            # 查找正文编辑区域
            desc_editor = await self.page.wait_for_selector('[contenteditable="true"]', timeout=5000)
            if not desc_editor:
                desc_editor = await self.page.wait_for_selector('.ql-editor', timeout=5000)
            
            await desc_editor.click()
            await self.page.keyboard.type(desc, delay=10)
            print("✅ 正文已填写")
            
        except Exception as e:
            print(f"⚠️ 正文填写失败: {e}")
    
    async def add_topics(self, topics: List[str]):
        """添加话题标签（可点击版本）"""
        if not topics:
            return
            
        print(f"🏷️ 添加话题标签: {', '.join(topics)}")
        
        for topic in topics:
            try:
                # 方法1: 在正文中输入 # 触发话题选择
                desc_editor = await self.page.query_selector('[contenteditable="true"]')
                if desc_editor:
                    await desc_editor.click()
                    # 移动到末尾
                    await self.page.keyboard.press('End')
                    await self.page.keyboard.type(' ')
                    await self.page.keyboard.type(f'#{topic}')
                    await asyncio.sleep(1)
                    
                    # 等待话题下拉列表出现
                    try:
                        topic_item = await self.page.wait_for_selector(
                            f'[class*="topic"] >> text="{topic}"', 
                            timeout=3000
                        )
                        if topic_item:
                            await topic_item.click()
                            print(f"  ✅ 已添加话题: #{topic}")
                            await asyncio.sleep(0.5)
                            continue
                    except:
                        pass
                    
                    # 方法2: 尝试点击第一个话题建议
                    try:
                        first_topic = await self.page.wait_for_selector(
                            '[class*="topic-item"], [class*="suggest-item"]',
                            timeout=2000
                        )
                        if first_topic:
                            await first_topic.click()
                            print(f"  ✅ 已添加话题: #{topic}（自动匹配）")
                            await asyncio.sleep(0.5)
                            continue
                    except:
                        pass
                    
                    # 如果都失败，按回车确认
                    await self.page.keyboard.press('Escape')
                    print(f"  ⚠️ 话题 #{topic} 可能未关联（将作为纯文本）")
                    
            except Exception as e:
                print(f"  ❌ 添加话题 #{topic} 失败: {e}")
        
        print("✅ 话题标签处理完成")
    
    async def publish(self):
        """点击发布按钮"""
        print("🚀 准备发布...")
        
        try:
            # 查找发布按钮
            publish_btn = await self.page.wait_for_selector(
                'button:has-text("发布"), [class*="publish-btn"], button:has-text("发布笔记")',
                timeout=5000
            )
            
            if publish_btn:
                await asyncio.sleep(1)
                await publish_btn.click()
                print("⏳ 正在发布...")
                
                # 等待发布完成
                await asyncio.sleep(5)
                
                # 检查是否发布成功
                current_url = self.page.url
                if 'success' in current_url or 'publish' not in current_url:
                    print("✅ 发布成功！")
                    return True
                else:
                    print("⚠️ 发布状态未知，请手动检查")
                    return True
            else:
                print("❌ 未找到发布按钮")
                return False
                
        except Exception as e:
            print(f"❌ 发布失败: {e}")
            return False


async def main_async(args):
    """异步主函数"""
    # 加载 Cookie
    cookie = load_cookie()
    
    # 验证图片
    valid_images = validate_images(args.images)
    
    print("\n" + "="*50)
    print("🍰 小红书浏览器自动化发布")
    print("="*50)
    print(f"  📌 标题: {args.title}")
    print(f"  📝 描述: {args.desc[:50]}..." if len(args.desc) > 50 else f"  📝 描述: {args.desc}")
    print(f"  🖼️ 图片: {len(valid_images)} 张")
    if args.topics:
        print(f"  🏷️ 话题: {', '.join(args.topics)}")
    print("="*50 + "\n")
    
    # 创建发布器
    publisher = XHSBrowserPublisher(cookie, headless=args.headless)
    
    try:
        # 初始化
        await publisher.init()
        
        # 进入创作者后台
        await publisher.goto_creator()
        
        # 上传图片
        await publisher.upload_images(valid_images)
        
        # 填写标题
        await publisher.fill_title(args.title)
        
        # 填写正文
        await publisher.fill_desc(args.desc)
        
        # 添加话题标签
        if args.topics:
            await publisher.add_topics(args.topics)
        
        # 如果不是 dry-run，则发布
        if not args.dry_run:
            success = await publisher.publish()
            if success:
                print("\n✨ 笔记发布完成！")
        else:
            print("\n🔍 Dry-run 模式，不会实际发布")
            print("按 Enter 键关闭浏览器...")
            input()
            
    except Exception as e:
        print(f"\n❌ 发布过程出错: {e}")
        raise
    finally:
        await publisher.close()


def main():
    parser = argparse.ArgumentParser(
        description='小红书笔记发布（浏览器自动化版本，支持可点击话题标签）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 基本用法
  python publish_xhs_browser.py -t "我的标题" -d "正文内容" -i cover.png card_1.png
  
  # 带话题标签
  python publish_xhs_browser.py -t "我的标题" -d "正文内容" -i cover.png --topics AI工具 程序员
  
  # 显示浏览器窗口（调试用）
  python publish_xhs_browser.py -t "我的标题" -d "正文内容" -i cover.png --no-headless
  
  # 仅测试，不实际发布
  python publish_xhs_browser.py -t "我的标题" -d "正文内容" -i cover.png --dry-run
'''
    )
    parser.add_argument('--title', '-t', required=True, help='笔记标题（不超过20字）')
    parser.add_argument('--desc', '-d', default='', help='笔记描述/正文内容')
    parser.add_argument('--images', '-i', nargs='+', required=True, help='图片文件路径')
    parser.add_argument('--topics', nargs='+', default=None, help='话题标签（可点击版本）')
    parser.add_argument('--headless', action='store_true', default=True, help='无头模式运行（默认）')
    parser.add_argument('--no-headless', dest='headless', action='store_false', help='显示浏览器窗口')
    parser.add_argument('--dry-run', action='store_true', help='仅测试，不实际发布')
    
    args = parser.parse_args()
    
    # 运行异步主函数
    asyncio.run(main_async(args))


if __name__ == '__main__':
    main()
