#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import sys

async def test_crawl(url):
    """测试采集功能"""
    try:
        # 动态导入crawl4ai
        from crawl4ai import AsyncWebCrawler
        
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            
            if result.success:
                # 先打印属性信息
                print("采集成功!")
                print("\n=== CrawlResult 属性 ===")
                print("可用属性:", dir(result))
                
                # 安全获取属性
                title = result.metadata.get('title', '未获取到标题') if hasattr(result, 'metadata') else '未获取到标题'
                status = result.http_status if hasattr(result, 'http_status') else '未知'
                url = result.url if hasattr(result, 'url') else '未知'
                
                print(f"\n标题: {title}")
                print(f"状态码: {status}")
                print(f"URL: {url}")
                
                # 查找内容属性
                content = ''
                content_attrs = ['extracted_content', 'markdown_content', 'html_content', 'raw_content', 'text']
                for attr in content_attrs:
                    if hasattr(result, attr):
                        content = getattr(result, attr)
                        print(f"找到内容属性: {attr}")
                        break
                
                if content:
                    print(f"文本长度: {len(content)} 字符")
                    print("\n内容预览:")
                    preview = content[:500] if len(content) > 500 else content
                    print(preview)
                else:
                    print("未找到内容属性")
                
                return True
            else:
                print(f"采集失败: {result.error_message}")
                return False
                
    except ImportError as e:
        print(f"导入crawl4ai失败: {e}")
        return False
    except Exception as e:
        print(f"采集异常: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_crawl.py <URL>")
        print("示例: python test_crawl.py https://news.baidu.com")
        sys.exit(1)
    
    url = sys.argv[1]
    print(f"正在测试采集: {url}")
    print("=" * 50)
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        success = loop.run_until_complete(test_crawl(url))
        sys.exit(0 if success else 1)
    finally:
        loop.close()
