import json
import tornado.web
import tornado.gen
import tornado.escape
import asyncio
import re
import os
from datetime import datetime

os.environ['CRAWL4AI_DB_PATH'] = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawl4ai')
os.environ['CRAWL4AI_CACHE_DIR'] = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'crawl4ai', 'cache')
try:
    os.makedirs(os.environ['CRAWL4AI_DB_PATH'], exist_ok=True)
    os.makedirs(os.environ['CRAWL4AI_CACHE_DIR'], exist_ok=True)
except:
    pass

try:
    from crawl4ai import AsyncWebCrawler
    CRAWL4AI_AVAILABLE = True
except Exception as e:
    CRAWL4AI_AVAILABLE = False
    print(f"警告: crawl4ai 不可用，AI深度采集功能将不可用。错误: {e}")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

from app.controllers.base import BaseHandler
from app.models.warehouse import ScoutRecordRepository, ScoutDetailRepository
from app.models.scout_source import ScoutSourceRepository
from app.models.model_service import ModelServiceRepository

class WarehouseListHandler(BaseHandler):
    """数据仓库列表"""
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        sources = ScoutSourceRepository.get_all(1, 100)
        self.render("warehouse_list.html", current_user=self.current_user, xsrf_token=xsrf_token, sources=sources)

class WarehouseApiHandler(BaseHandler):
    """数据仓库API"""
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 20))
            source_id = self.get_argument("source_id", "")
            keyword = self.get_argument("keyword", "")
            ai_analyzed = self.get_argument("ai_analyzed", "")
        except ValueError:
            page, page_size = 1, 20
            source_id, keyword, ai_analyzed = "", "", ""
        
        records = ScoutRecordRepository.get_all(page, page_size, 
                                               source_id=int(source_id) if source_id else None,
                                               keyword=keyword if keyword else None,
                                               ai_analyzed=int(ai_analyzed) if ai_analyzed else None)
        total = ScoutRecordRepository.get_total_count(
            source_id=int(source_id) if source_id else None,
            keyword=keyword if keyword else None,
            ai_analyzed=int(ai_analyzed) if ai_analyzed else None
        )
        
        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "count": total,
            "data": records
        }))

    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")
        
        if action == "delete":
            self._delete_record()
        elif action == "batchDelete":
            self._batch_delete()
        elif action == "collect":
            self._collect_data()
        elif action == "batchCollect":
            self._batch_collect()
        elif action == "aiAnalyze":
            self._ai_analyze()
        elif action == "batchAiAnalyze":
            self._batch_ai_analyze()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _delete_record(self):
        id = self.get_body_argument("id", "")
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return
        
        try:
            id = int(id)
            ScoutDetailRepository.delete_by_record_id(id)
            if ScoutRecordRepository.delete(id):
                self.write(json.dumps({"code": 0, "msg": "删除成功"}))
            else:
                self.write(json.dumps({"code": 1, "msg": "删除失败"}))
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))

    def _batch_delete(self):
        ids_str = self.get_body_argument("ids", "")
        if not ids_str:
            self.write(json.dumps({"code": 1, "msg": "请选择要删除的记录"}))
            return
        
        try:
            ids = [int(id.strip()) for id in ids_str.split(",") if id.strip()]
            for id in ids:
                ScoutDetailRepository.delete_by_record_id(id)
            deleted_count = ScoutRecordRepository.batch_delete(ids)
            self.write(json.dumps({"code": 0, "msg": f"成功删除 {deleted_count} 条记录"}))
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID列表"}))

    def _collect_data(self):
        """采集数据"""
        source_id = self.get_body_argument("source_id", "")
        keywords = self.get_body_argument("keywords", "").strip()
        
        if not source_id:
            self.write(json.dumps({"code": 1, "msg": "请选择数据源"}))
            return
        
        if not keywords:
            self.write(json.dumps({"code": 1, "msg": "请输入关键字"}))
            return
        
        try:
            source_id = int(source_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的数据源ID"}))
            return
        
        source = ScoutSourceRepository.get_by_id(source_id)
        if not source:
            self.write(json.dumps({"code": 1, "msg": "数据源不存在"}))
            return
        
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        results = []
        
        for keyword in keyword_list:
            try:
                url = source["url_pattern"].replace("{关键字}", keyword)
                headers = ScoutSourceRepository.parse_headers(source["headers"])
                
                import requests
                response = requests.request(
                    method=source["request_method"],
                    url=url,
                    headers=headers,
                    timeout=30
                )
                
                titles = self._extract_titles(response.text)
                
                for title in titles[:10]:
                    record_id = ScoutRecordRepository.create(
                        source_id=source_id,
                        source_name=source["name"],
                        keyword=keyword,
                        url=url,
                        title=title,
                        summary="",
                        raw_content=response.text[:5000],
                        status="success"
                    )
                    results.append({"title": title, "record_id": record_id})
                
            except Exception as e:
                results.append({"error": str(e), "keyword": keyword})
        
        self.write(json.dumps({
            "code": 0,
            "msg": f"采集完成，共采集 {len([r for r in results if 'record_id' in r])} 条记录",
            "data": results
        }))

    def _batch_collect(self):
        """批量采集"""
        source_ids_str = self.get_body_argument("source_ids", "")
        keywords = self.get_body_argument("keywords", "").strip()
        
        if not source_ids_str:
            self.write(json.dumps({"code": 1, "msg": "请选择数据源"}))
            return
        
        if not keywords:
            self.write(json.dumps({"code": 1, "msg": "请输入关键字"}))
            return
        
        try:
            source_ids = [int(id.strip()) for id in source_ids_str.split(",") if id.strip()]
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的数据源ID"}))
            return
        
        keyword_list = [k.strip() for k in keywords.split(",") if k.strip()]
        total_collected = 0
        results = []
        
        for source_id in source_ids:
            source = ScoutSourceRepository.get_by_id(source_id)
            if not source:
                continue
            
            for keyword in keyword_list:
                try:
                    url = source["url_pattern"].replace("{关键字}", keyword)
                    headers = ScoutSourceRepository.parse_headers(source["headers"])
                    
                    import requests
                    response = requests.request(
                        method=source["request_method"],
                        url=url,
                        headers=headers,
                        timeout=30
                    )
                    
                    titles = self._extract_titles(response.text)
                    count = 0
                    
                    for title in titles[:10]:
                        record_id = ScoutRecordRepository.create(
                            source_id=source_id,
                            source_name=source["name"],
                            keyword=keyword,
                            url=url,
                            title=title,
                            summary="",
                            raw_content=response.text[:5000],
                            status="success"
                        )
                        count += 1
                    
                    total_collected += count
                    results.append({
                        "source": source["name"],
                        "keyword": keyword,
                        "count": count
                    })
                    
                except Exception as e:
                    results.append({
                        "source": source["name"],
                        "keyword": keyword,
                        "error": str(e)
                    })
        
        self.write(json.dumps({
            "code": 0,
            "msg": f"批量采集完成，共采集 {total_collected} 条记录",
            "data": results
        }))

    def _extract_titles(self, html_content):
        """从HTML内容中提取标题"""
        titles = []
        patterns = [
            r'<h3[^>]*class="[^"]*news-title[^"]*"[^>]*>(.*?)</h3>',
            r'<h3[^>]*>(.*?)</h3>',
            r'title="([^"]*)"',
            r'<a[^>]*>([^<]*[^标题新闻文章][^<]*)</a>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                title = re.sub(r'<[^>]+>', '', match).strip()
                if title and len(title) > 5 and len(title) < 200:
                    titles.append(title)
        
        return list(set(titles))[:20]

    @tornado.gen.coroutine
    def _ai_analyze(self):
        """AI深度分析单条记录"""
        record_id = self.get_body_argument("record_id", "")
        
        if not record_id:
            self.write(json.dumps({"code": 1, "msg": "记录ID不能为空"}))
            return
        
        try:
            record_id = int(record_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的记录ID"}))
            return
        
        record = ScoutRecordRepository.get_by_id(record_id)
        if not record:
            self.write(json.dumps({"code": 1, "msg": "记录不存在"}))
            return
        
        if record["ai_analyzed"]:
            self.write(json.dumps({"code": 0, "msg": "该记录已分析", "data": {"status": "already_analyzed"}}))
            return
        
        ScoutRecordRepository.update(record_id, ai_analyze_status="analyzing", ai_analyze_msg="正在分析...")
        
        try:
            result = yield self._do_ai_analyze(record)
            
            if result["success"]:
                detail_id = ScoutDetailRepository.create(
                    record_id=record_id,
                    source_id=record["source_id"],
                    title=record.get("title"),
                    content=result.get("content", ""),
                    source_url=record.get("url"),
                    ai_summary=result.get("summary", ""),
                    ai_keywords=result.get("keywords", ""),
                    ai_sentiment=result.get("sentiment", ""),
                    ai_entities=result.get("entities", "")
                )
                
                ScoutRecordRepository.update(record_id,
                    ai_analyzed=1,
                    ai_analyze_status="completed",
                    ai_analyze_msg="分析完成",
                    ai_analyze_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
                
                self.write(json.dumps({
                    "code": 0,
                    "msg": "AI分析完成",
                    "data": {"detail_id": detail_id}
                }))
            else:
                ScoutRecordRepository.update(record_id,
                    ai_analyze_status="failed",
                    ai_analyze_msg=result.get("error", "分析失败")
                )
                self.write(json.dumps({"code": 1, "msg": result.get("error", "分析失败")}))
                
        except Exception as e:
            ScoutRecordRepository.update(record_id,
                ai_analyze_status="failed",
                ai_analyze_msg=str(e)
            )
            self.write(json.dumps({"code": 1, "msg": str(e)}))

    @tornado.gen.coroutine
    def _batch_ai_analyze(self):
        """批量AI分析"""
        ids_str = self.get_body_argument("ids", "")
        
        if not ids_str:
            self.write(json.dumps({"code": 1, "msg": "请选择要分析的记录"}))
            return
        
        try:
            ids = [int(id.strip()) for id in ids_str.split(",") if id.strip()]
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID列表"}))
            return
        
        success_count = 0
        fail_count = 0
        results = []
        
        for record_id in ids:
            record = ScoutRecordRepository.get_by_id(record_id)
            if not record or record["ai_analyzed"]:
                continue
            
            ScoutRecordRepository.update(record_id, ai_analyze_status="analyzing", ai_analyze_msg="正在分析...")
            
            try:
                result = yield self._do_ai_analyze(record)
                
                if result["success"]:
                    detail_id = ScoutDetailRepository.create(
                        record_id=record_id,
                        source_id=record["source_id"],
                        title=record.get("title"),
                        content=result.get("content", ""),
                        source_url=record.get("url"),
                        ai_summary=result.get("summary", ""),
                        ai_keywords=result.get("keywords", ""),
                        ai_sentiment=result.get("sentiment", ""),
                        ai_entities=result.get("entities", "")
                    )
                    
                    ScoutRecordRepository.update(record_id,
                        ai_analyzed=1,
                        ai_analyze_status="completed",
                        ai_analyze_msg="分析完成",
                        ai_analyze_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                    
                    success_count += 1
                    results.append({"id": record_id, "success": True})
                else:
                    fail_count += 1
                    results.append({"id": record_id, "success": False, "error": result.get("error")})
                    
            except Exception as e:
                fail_count += 1
                ScoutRecordRepository.update(record_id,
                    ai_analyze_status="failed",
                    ai_analyze_msg=str(e)
                )
                results.append({"id": record_id, "success": False, "error": str(e)})
        
        self.write(json.dumps({
            "code": 0,
            "msg": f"批量分析完成，成功 {success_count} 条，失败 {fail_count} 条",
            "data": {
                "success_count": success_count,
                "fail_count": fail_count,
                "results": results
            }
        }))

    @tornado.gen.coroutine
    def _do_ai_analyze(self, record):
        """执行AI分析"""
        if not OPENAI_AVAILABLE:
            return {"success": False, "error": "OpenAI模块未安装"}
        
        default_model = ModelServiceRepository.get_default()
        if not default_model:
            return {"success": False, "error": "未配置默认模型"}
        
        try:
            client = OpenAI(
                api_key=default_model["api_key"],
                base_url=default_model["base_url"]
            )
            
            content = record.get("raw_content", "") or record.get("summary", "")
            if not content:
                content = record.get("title", "")
            
            prompt = f"""请分析以下内容，提取关键信息：

内容标题：{record.get('title', '无标题')}
内容摘要：{content[:2000]}

请以JSON格式返回以下信息：
{{
    "summary": "内容摘要（100字以内）",
    "keywords": "关键词（用逗号分隔，最多5个）",
    "sentiment": "情感倾向（正面/负面/中性）",
    "entities": "实体识别（提取人名、地名、机构名等，用逗号分隔）",
    "content": "主要内容（200字以内）"
}}

只返回JSON，不要有其他内容。"""

            response = client.chat.completions.create(
                model=default_model["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=default_model["max_tokens"],
                temperature=default_model["temperature"]
            )
            
            result_text = response.choices[0].message.content
            
            try:
                result_json = json.loads(result_text)
                return {
                    "success": True,
                    "summary": result_json.get("summary", ""),
                    "keywords": result_json.get("keywords", ""),
                    "sentiment": result_json.get("sentiment", ""),
                    "entities": result_json.get("entities", ""),
                    "content": result_json.get("content", "")
                }
            except json.JSONDecodeError:
                return {
                    "success": True,
                    "summary": result_text[:200],
                    "keywords": "",
                    "sentiment": "未知",
                    "entities": "",
                    "content": result_text[:500]
                }
                
        except Exception as e:
            return {"success": False, "error": str(e)}


class WarehouseDetailHandler(BaseHandler):
    """数据明细详情"""
    @tornado.web.authenticated
    def get(self):
        id = self.get_argument("id", "")
        record = None
        detail = None
        
        if id:
            try:
                record = ScoutRecordRepository.get_by_id(int(id))
                if record:
                    detail = ScoutDetailRepository.get_by_record_id(record["id"])
            except ValueError:
                pass
        
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("warehouse_detail.html", current_user=self.current_user, xsrf_token=xsrf_token, record=record, detail=detail)

class WarehouseStatsApiHandler(BaseHandler):
    """数据统计API"""
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
