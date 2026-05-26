import json
import tornado.web
import tornado.gen
import asyncio
import re
from datetime import datetime
from urllib.parse import urlparse
import os
import requests

os.environ['CRAWL4AI_DB_PATH'] = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawl4ai')
os.environ['CRAWL4AI_CACHE_DIR'] = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawl4ai', 'cache')
try:
    os.makedirs(os.environ['CRAWL4AI_DB_PATH'], exist_ok=True)
    os.makedirs(os.environ['CRAWL4AI_CACHE_DIR'], exist_ok=True)
except:
    pass

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
except Exception as e:
    CRAWL4AI_AVAILABLE = False
    print(f"警告: crawl4ai 不可用，将使用requests作为备选方案。错误: {e}")

from app.controllers.base import BaseHandler
from app.models.warehouse import ScoutRecordRepository, ScoutDetailRepository
from app.models.scout_source import ScoutSourceRepository

class DeepCollectListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("deep_collect.html", current_user=self.current_user, xsrf_token=xsrf_token)

class DeepCollectApiHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")

        if action == "collect":
            self._deep_collect()
        elif action == "batch_collect":
            self._batch_deep_collect()
        elif action == "check_status":
            self._check_status()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _validate_url(self, url):
        """验证URL格式"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _deep_collect(self):
        """执行深度采集"""
        url = self.get_body_argument("url", "").strip()
        headless = self.get_body_argument("headless", "true").lower() == "true"
        js_enabled = self.get_body_argument("js_enabled", "true").lower() == "true"
        wait_for = self.get_body_argument("wait_for", "").strip()
        max_depth = int(self.get_body_argument("max_depth", "1"))
        source_name = self.get_body_argument("source_name", "").strip()

        if not url:
            self.write(json.dumps({"code": 1, "msg": "URL不能为空"}))
            return

        if not self._validate_url(url):
            self.write(json.dumps({"code": 1, "msg": "无效的URL格式"}))
            return

        try:
            result = None
            
            if CRAWL4AI_AVAILABLE:
                result = self._run_crawl_sync(url, headless, js_enabled, wait_for, max_depth)
            else:
                result = self._run_requests_crawl(url)

            if result["success"]:
                record_id = ScoutRecordRepository.create(
                    source_id=0,
                    source_name=source_name or url,
                    keyword="",
                    url=url,
                    title=result.get("title", ""),
                    summary=result.get("meta_description", ""),
                    raw_content=result.get("content", ""),
                    status="success"
                )

                self.write(json.dumps({
                    "code": 0,
                    "msg": "深度采集成功",
                    "data": {
                        "record_id": record_id,
                        "title": result.get("title", ""),
                        "url": url,
                        "content_length": len(result.get("content", "")),
                        "links_found": len(result.get("links", [])),
                        "images_found": len(result.get("images", [])),
                        "media_found": len(result.get("media", [])),
                        "crawl_time": result.get("crawl_time", 0)
                    }
                }))
            else:
                self.write(json.dumps({
                    "code": 1,
                    "msg": f"采集失败: {result.get('error', '未知错误')}"
                }))

        except Exception as e:
            self.write(json.dumps({
                "code": 1,
                "msg": f"采集异常: {str(e)}"
            }))
    
    def _run_requests_crawl(self, url):
        """使用requests进行简单采集（备选方案）"""
        start_time = datetime.now()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.encoding = response.apparent_encoding
            html = response.text
            
            title = self._extract_title(html)
            links = self._extract_links(html)
            images = self._extract_images(html)
            media = self._extract_media(html)
            
            meta_desc = ""
            meta_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', html, re.IGNORECASE)
            if meta_match:
                meta_desc = meta_match.group(1)
            else:
                meta_match = re.search(r'<meta[^>]+content="([^"]*)"[^>]+name="description"', html, re.IGNORECASE)
                if meta_match:
                    meta_desc = meta_match.group(1)
            
            html_content = html
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
            html_content = re.sub(r'<[^>]+>', '', html_content)
            html_content = ' '.join(html_content.split())
            content = html_content[:5000]
            
            crawl_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "html": html,
                "content": content,
                "title": title,
                "meta_description": meta_desc,
                "links": links[:50],
                "images": images[:20],
                "media": media,
                "crawl_time": round(crawl_time, 2)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _batch_deep_collect(self):
        """批量深度采集"""
        urls_str = self.get_body_argument("urls", "").strip()
        headless = self.get_body_argument("headless", "true").lower() == "true"
        js_enabled = self.get_body_argument("js_enabled", "true").lower() == "true"
        wait_for = self.get_body_argument("wait_for", "").strip()
        source_name = self.get_body_argument("source_name", "").strip()

        if not urls_str:
            self.write(json.dumps({"code": 1, "msg": "URL列表不能为空"}))
            return

        urls = [u.strip() for u in urls_str.split("\n") if u.strip()]

        valid_urls = []
        for u in urls:
            if self._validate_url(u):
                valid_urls.append(u)

        if not valid_urls:
            self.write(json.dumps({"code": 1, "msg": "没有有效的URL"}))
            return

        results = []
        success_count = 0
        fail_count = 0

        for url in valid_urls:
            try:
                result = None
                
                if CRAWL4AI_AVAILABLE:
                    result = self._run_crawl_sync(url, headless, js_enabled, wait_for, 1)
                else:
                    result = self._run_requests_crawl(url)

                if result["success"]:
                    record_id = ScoutRecordRepository.create(
                        source_id=0,
                        source_name=source_name or url,
                        keyword="",
                        url=url,
                        title=result.get("title", ""),
                        summary=result.get("meta_description", ""),
                        raw_content=result.get("content", ""),
                        status="success"
                    )

                    results.append({
                        "url": url,
                        "success": True,
                        "record_id": record_id,
                        "title": result.get("title", "")
                    })
                    success_count += 1
                else:
                    results.append({
                        "url": url,
                        "success": False,
                        "error": result.get("error", "未知错误")
                    })
                    fail_count += 1

            except Exception as e:
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
                fail_count += 1

        self.write(json.dumps({
            "code": 0,
            "msg": f"批量采集完成，成功 {success_count} 个，失败 {fail_count} 个",
            "data": {
                "success_count": success_count,
                "fail_count": fail_count,
                "results": results
            }
        }))

    def _run_crawl_sync(self, url, headless=True, js_enabled=True, wait_for="", max_depth=1):
        """同步执行深度采集"""
        start_time = datetime.now()

        try:
            browser_config = BrowserConfig(
                headless=headless,
                verbose=False
            )

            crawl_config = CrawlerRunConfig(
                delay_before_return_html=2.0 if wait_for else 0.5,
                page_timeout=30000,
                verbose=False
            )

            if wait_for:
                crawl_config.wait_for = wait_for

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self._crawl_url_async(url, browser_config, crawl_config))
            finally:
                loop.close()

            if result["success"]:
                crawl_time = (datetime.now() - start_time).total_seconds()
                result["crawl_time"] = round(crawl_time, 2)

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def _crawl_url_async(self, url, browser_config, crawl_config):
        """异步执行深度采集"""
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=crawl_config)

                if result.success:
                    links = self._extract_links(result.html)
                    images = self._extract_images(result.html)
                    media = self._extract_media(result.html)
                    title = self._extract_title(result.html)

                    meta_desc = ""
                    meta_match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', result.html, re.IGNORECASE)
                    if meta_match:
                        meta_desc = meta_match.group(1)
                    else:
                        meta_match = re.search(r'<meta[^>]+content="([^"]*)"[^>]+name="description"', result.html, re.IGNORECASE)
                        if meta_match:
                            meta_desc = meta_match.group(1)

                    # 获取采集内容，支持多个可能的属性名称
                    content = ""
                    if hasattr(result, 'extracted_content') and result.extracted_content:
                        content = result.extracted_content
                    elif hasattr(result, 'text') and result.text:
                        content = result.text
                    elif hasattr(result, 'markdown') and result.markdown:
                        content = result.markdown
                    elif hasattr(result, 'html') and result.html:
                        # 如果没有提取的内容，从HTML中提取纯文本
                        html_content = result.html
                        # 移除脚本和样式
                        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
                        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
                        # 移除HTML标签
                        html_content = re.sub(r'<[^>]+>', '', html_content)
                        # 清理空白字符
                        html_content = ' '.join(html_content.split())
                        content = html_content[:5000]  # 限制长度
                    
                    return {
                        "success": True,
                        "html": result.html,
                        "content": content,
                        "title": title,
                        "meta_description": meta_desc,
                        "links": links[:50],
                        "images": images[:20],
                        "media": media
                    }
                else:
                    return {
                        "success": False,
                        "error": result.error_message if hasattr(result, 'error_message') else "采集失败"
                    }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_title(self, html):
        """提取页面标题"""
        match = re.search(r'<title[^>]*>([^<]*)</title>', html, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_links(self, html):
        """提取页面链接"""
        links = []
        href_pattern = re.compile(r'href=["\']([^"\']+)["\']', re.IGNORECASE)
        for match in href_pattern.finditer(html):
            href = match.group(1)
            if href.startswith('http://') or href.startswith('https://'):
                links.append(href)
        return list(set(links))

    def _extract_images(self, html):
        """提取页面图片"""
        images = []
        src_pattern = re.compile(r'src=["\']([^"\']+\.(?:jpg|jpeg|png|gif|webp|svg)[^"\']*)["\']', re.IGNORECASE)
        for match in src_pattern.finditer(html):
            images.append(match.group(1))
        return list(set(images))

    def _extract_media(self, html):
        """提取页面媒体资源"""
        media = []
        patterns = [
            (r'<video[^>]+src=["\']([^"\']+)["\']', 'video'),
            (r'<audio[^>]+src=["\']([^"\']+)["\']', 'audio'),
            (r'<source[^>]+src=["\']([^"\']+)["\']', 'media'),
        ]
        for pattern, media_type in patterns:
            for match in re.finditer(pattern, html, re.IGNORECASE):
                media.append({"type": media_type, "url": match.group(1)})
        return media

    def _check_status(self):
        """检查crawl4ai状态"""
        if CRAWL4AI_AVAILABLE:
            try:
                # 创建新的事件循环
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    # 正确调用异步函数
                    result = new_loop.run_until_complete(self._test_crawl_async())
                    status = "ready" if result else "crawl_failed"
                except Exception as e:
                    status = f"error: {str(e)}"
                finally:
                    new_loop.close()

                self.write(json.dumps({
                    "code": 0,
                    "msg": status,
                    "data": {
                        "available": True,
                        "status": status
                    }
                }))
            except Exception as e:
                self.write(json.dumps({
                    "code": 0,
                    "msg": "异常",
                    "data": {
                        "available": False,
                        "status": "error",
                        "error": str(e)
                    }
                }))
        else:
            self.write(json.dumps({
                "code": 0,
                "msg": "crawl4ai未安装",
                "data": {
                    "available": False,
                    "status": "not_installed"
                }
            }))

    async def _test_crawl_async(self):
        """测试crawl4ai功能"""
        browser_config = BrowserConfig(headless=True, verbose=False)
        crawl_config = CrawlerRunConfig(js_enabled=False, verbose=False)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url="https://www.baidu.com", config=crawl_config)
            return result.success

class DeepCollectStatsApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        total_records = ScoutRecordRepository.get_total_count()
        analyzed_records = ScoutRecordRepository.get_total_count(ai_analyzed=1)
        unanalyzed_records = ScoutRecordRepository.get_total_count(ai_analyzed=0)

        total_details = ScoutDetailRepository.get_total_count()

        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "data": {
                "total_records": total_records,
                "analyzed_records": analyzed_records,
                "unanalyzed_records": unanalyzed_records,
                "total_details": total_details,
                "analyze_rate": f"{(analyzed_records/total_records*100) if total_records > 0 else 0:.1f}%"
            }
        }))