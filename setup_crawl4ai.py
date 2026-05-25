#!/usr/bin/env python
"""
AI深度采集功能初始化脚本
用于配置crawl4ai环境并安装Playwright浏览器
"""
import os
import sys
import subprocess

def print_banner():
    print("=" * 60)
    print("     AI深度采集功能初始化 - cnAgentOS")
    print("=" * 60)

def check_network():
    print("\n[1/5] 检测网络状态...")
    try:
        import socket
        socket.create_connection(("www.baidu.com", 80), timeout=3)
        print("   ✓ 网络连接正常")
        return True
    except OSError:
        print("   ✗ 网络连接失败，可能无法下载浏览器")
        return False

def check_proxy():
    print("\n[2/5] 检测代理设置...")

    proxies = {
        'http': os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy'),
        'https': os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy'),
        'all': os.environ.get('ALL_PROXY') or os.environ.get('all_proxy')
    }

    has_proxy = any(proxies.values())

    if has_proxy:
        print("   ✓ 检测到代理设置:")
        for k, v in proxies.items():
            if v:
                print(f"     - {k.upper()}_PROXY: {v}")
    else:
        print("   ○ 未检测到代理设置")

    return proxies

def setup_proxy_env(proxies):
    print("\n[3/5] 配置下载环境...")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data', 'crawl4ai')
    cache_dir = os.path.join(data_dir, 'cache')

    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)

    os.environ['CRAWL4AI_DB_PATH'] = data_dir
    os.environ['CRAWL4AI_CACHE_DIR'] = cache_dir

    if proxies.get('https'):
        os.environ['HTTPS_PROXY'] = proxies['https']
        os.environ['https_proxy'] = proxies['https']
    if proxies.get('http'):
        os.environ['HTTP_PROXY'] = proxies['http']
        os.environ['http_proxy'] = proxies['http']

    print(f"   数据目录: {data_dir}")
    print(f"   缓存目录: {cache_dir}")

    if proxies.get('https'):
        print(f"   下载代理: {proxies['https']}")

    return data_dir, cache_dir

def install_playwright():
    print("\n[4/5] 安装Playwright浏览器...")

    playwright_options = [
        'chromium',
        '--with-deps'
    ]

    cmd = [sys.executable, '-m', 'playwright', 'install'] + playwright_options

    print(f"   执行命令: {' '.join(cmd)}")
    print("   提示: 首次安装需要下载约180MB的Chrome浏览器")
    print("   如果下载太慢，可以尝试:")
    print("   1. 设置代理环境变量后重新运行")
    print("   2. 使用VPN")
    print("   3. 手动运行: playwright install chromium")
    print("")

    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=False
        )

        if result.returncode == 0:
            print("   ✓ Playwright浏览器安装成功!")
            return True
        else:
            print("   ✗ Playwright浏览器安装失败")
            print("   请检查网络连接或手动运行安装命令")
            return False

    except Exception as e:
        print(f"   ✗ 安装出错: {e}")
        return False

def verify_crawl4ai(data_dir, cache_dir):
    print("\n[5/5] 验证crawl4ai...")

    try:
        os.environ['CRAWL4AI_DB_PATH'] = data_dir
        os.environ['CRAWL4AI_CACHE_DIR'] = cache_dir

        from crawl4ai import AsyncWebCrawler
        print("   ✓ crawl4ai导入成功!")

        try:
            from crawl4ai import BrowserConfig, CrawlerRunConfig
            print("   ✓ 浏览器配置模块正常")
        except ImportError:
            print("   ⚠ 部分模块导入失败")

        return True

    except ImportError as e:
        print(f"   ✗ crawl4ai导入失败: {e}")
        print("\n   请先安装crawl4ai:")
        print("   pip install crawl4ai")
        return False
    except Exception as e:
        print(f"   ⚠ 验证过程出现问题: {e}")
        return False

def print_summary(success):
    print("\n" + "=" * 60)
    if success:
        print("初始化完成!")
        print("=" * 60)
        print("\n现在可以启动服务器了:")
        print("  python app.py")
        print("\n然后访问: http://localhost:10086/admin/deep-collect")
    else:
        print("初始化未完成，请解决上述问题后重试")
        print("=" * 60)
        print("\n常见问题解决方案:")
        print("1. 下载慢: 设置代理环境变量后重试")
        print("   set HTTPS_PROXY=http://127.0.0.1:7890")
        print("   python setup_crawl4ai.py")
        print("\n2. 手动安装浏览器:")
        print("   playwright install chromium")
        print("\n3. 安装crawl4ai:")
        print("   pip install crawl4ai")

def main():
    print_banner()

    network_ok = check_network()

    if not network_ok:
        print("\n警告: 网络连接有问题，建议先解决网络问题再继续")

    proxies = check_proxy()

    data_dir, cache_dir = setup_proxy_env(proxies)

    playwright_ok = install_playwright()

    crawl4ai_ok = verify_crawl4ai(data_dir, cache_dir)

    success = playwright_ok and crawl4ai_ok

    print_summary(success)

    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())