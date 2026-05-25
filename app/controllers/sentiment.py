import json
import tornado.web
import tornado.gen
from datetime import datetime, timedelta
import time

from app.controllers.base import BaseHandler
from app.models.sentiment import (
    SentimentAnalysisRepository, SentimentAnalysisLogRepository,
    SentimentAnalyzer
)
from app.models.datav import DataVLocationRepository, DataVCacheRepository
from app.models.warehouse import ScoutRecordRepository, ScoutDetailRepository
from app.models.chat import ChatSessionRepository, ChatMessageRepository


class SentimentListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("sentiment_list.html", current_user=self.current_user, xsrf_token=xsrf_token)


class SentimentApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 20))
        except ValueError:
            page, page_size = 1, 20

        sentiment = self.get_argument("sentiment", "")
        source_type = self.get_argument("source_type", "")
        risk_level = self.get_argument("risk_level", "")
        keyword = self.get_argument("keyword", "")
        start_time = self.get_argument("start_time", "")
        end_time = self.get_argument("end_time", "")

        analyses = SentimentAnalysisRepository.get_all(
            page, page_size,
            sentiment=sentiment if sentiment else None,
            source_type=source_type if source_type else None,
            risk_level=risk_level if risk_level else None,
            keyword=keyword if keyword else None,
            start_time=start_time if start_time else None,
            end_time=end_time if end_time else None
        )

        total = SentimentAnalysisRepository.get_total_count(
            sentiment=sentiment if sentiment else None,
            source_type=source_type if source_type else None,
            risk_level=risk_level if risk_level else None,
            keyword=keyword if keyword else None,
            start_time=start_time if start_time else None,
            end_time=end_time if end_time else None
        )

        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "count": total,
            "data": analyses
        }))

    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")

        if action == "delete":
            self._delete_analysis()
        elif action == "batchDelete":
            self._batch_delete()
        elif action == "reanalyze":
            self._reanalyze()
        elif action == "batchAnalyze":
            self._batch_analyze()
        elif action == "export":
            self._export_data()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _delete_analysis(self):
        id = self.get_body_argument("id", "")
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return

        try:
            id = int(id)
            if SentimentAnalysisRepository.delete(id):
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
            deleted_count = SentimentAnalysisRepository.batch_delete(ids)
            self.write(json.dumps({"code": 0, "msg": f"成功删除 {deleted_count} 条记录"}))
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID列表"}))

    def _reanalyze(self):
        id = self.get_body_argument("id", "")
        if not id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return

        try:
            id = int(id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return

        analysis = SentimentAnalysisRepository.get_by_id(id)
        if not analysis:
            self.write(json.dumps({"code": 1, "msg": "分析记录不存在"}))
            return

        result = SentimentAnalyzer.analyze_text(analysis["content"])
        hot_score = SentimentAnalyzer.calculate_hot_score(
            analysis["content"],
            result["sentiment"],
            result["confidence"]
        )

        SentimentAnalysisRepository.update(
            id,
            sentiment=result["sentiment"],
            sentiment_score=result["sentiment_score"],
            confidence=result["confidence"],
            keywords=result["keywords"],
            risk_level=result["risk_level"],
            risk_tags=result["risk_tags"],
            summary=result["summary"],
            hot_score=hot_score
        )

        self.write(json.dumps({"code": 0, "msg": "重新分析成功", "data": result}))

    def _batch_analyze(self):
        source_type = self.get_body_argument("source_type", "")
        start_time = self.get_body_argument("start_time", "")
        end_time = self.get_body_argument("end_time", "")

        self.write(json.dumps({
            "code": 0,
            "msg": "批量分析任务已提交",
            "task_id": int(time.time())
        }))

    def _export_data(self):
        sentiment = self.get_body_argument("sentiment", "")
        source_type = self.get_body_argument("source_type", "")
        start_time = self.get_body_argument("start_time", "")
        end_time = self.get_body_argument("end_time", "")
        format_type = self.get_body_argument("format", "json")

        analyses = SentimentAnalysisRepository.get_all(
            1, 10000,
            sentiment=sentiment if sentiment else None,
            source_type=source_type if source_type else None,
            start_time=start_time if start_time else None,
            end_time=end_time if end_time else None
        )

        if format_type == "csv":
            csv_content = "ID,来源,标题,内容,情感,置信度,关键词,风险等级,热词得分,分析时间\n"
            for a in analyses:
                csv_content += f"{a['id']},{a['source_type']},{a.get('title','')},{a['content'][:50]},{a['sentiment']},{a['confidence']},{a.get('keywords','')},{a['risk_level']},{a['hot_score']},{a['analyze_time']}\n"
            self.set_header("Content-Type", "text/csv")
            self.set_header("Content-Disposition", "attachment; filename=sentiment_analysis.csv")
            self.write(csv_content)
        else:
            self.write(json.dumps({
                "code": 0,
                "data": analyses,
                "total": len(analyses)
            }))


class SentimentStatsApiHandler(BaseHandler):
    def initialize(self):
        self.redis_client = None
        try:
            import redis
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True, socket_timeout=1, socket_connect_timeout=1)
            self.redis_client.ping()
        except:
            self.redis_client = None

    def _get_cache(self, cache_key: str, expire_seconds: int = 60):
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    return json.loads(cached)
            except:
                pass
        else:
            cached = DataVCacheRepository.get(cache_key)
            if cached:
                return cached
        return None

    def _set_cache(self, cache_key: str, data, expire_seconds: int = 60):
        if self.redis_client:
            try:
                self.redis_client.setex(cache_key, expire_seconds, json.dumps(data, ensure_ascii=False))
                return
            except:
                pass
        else:
            DataVCacheRepository.set(cache_key, data, expire_seconds)

    def _parse_time_range(self):
        start_time = self.get_argument("start_time", "")
        end_time = self.get_argument("end_time", "")
        days = self.get_argument("days", "")

        if days:
            try:
                days = int(days)
                end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                start_time = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

        return start_time if start_time else None, end_time if end_time else None

    async def get(self):
        data_type = self.get_argument("type", "all")
        use_cache = self.get_argument("cache", "true").lower() == "true"
        cache_key_prefix = f"sentiment:stats:{data_type}"

        if data_type == "all":
            await self._get_all_stats(use_cache, cache_key_prefix)
        elif data_type == "sentiment":
            await self._get_sentiment_dist(use_cache, cache_key_prefix)
        elif data_type == "timeline":
            await self._get_timeline(use_cache, cache_key_prefix)
        elif data_type == "hotwords":
            await self._get_hotwords(use_cache, cache_key_prefix)
        elif data_type == "risk":
            await self._get_risk_dist(use_cache, cache_key_prefix)
        elif data_type == "geo":
            await self._get_geo_data(use_cache, cache_key_prefix)
        else:
            self.write(json.dumps({"code": 1, "msg": "未知的统计类型"}))

    async def _get_all_stats(self, use_cache: bool, cache_key_prefix: str):
        cache_key = f"{cache_key_prefix}:all"
        if use_cache:
            cached = self._get_cache(cache_key, 60)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        start_time, end_time = self._parse_time_range()

        stats = SentimentAnalysisRepository.get_sentiment_stats(
            start_time=start_time,
            end_time=end_time
        )

        timeline = SentimentAnalysisRepository.get_time_series(
            granularity="day",
            limit=30,
            start_time=start_time,
            end_time=end_time
        )

        hotwords = SentimentAnalysisRepository.get_hot_keywords(
            limit=20,
            start_time=start_time,
            end_time=end_time
        )

        result = {
            "stats": stats,
            "timeline": timeline,
            "hotwords": hotwords,
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, result, 60)

        self.write(json.dumps({"code": 0, "data": result, "cached": False}))

    async def _get_sentiment_dist(self, use_cache: bool, cache_key_prefix: str):
        start_time, end_time = self._parse_time_range()

        cache_key = f"{cache_key_prefix}:{start_time}:{end_time}"
        if use_cache:
            cached = self._get_cache(cache_key, 60)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        stats = SentimentAnalysisRepository.get_sentiment_stats(
            start_time=start_time,
            end_time=end_time
        )

        echarts_data = {
            "title": {"text": "情感分布", "left": "center"},
            "tooltip": {"trigger": "item"},
            "legend": {"bottom": 10, "left": "center"},
            "series": [{
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "itemStyle": {"borderRadius": 10, "borderColor": "#fff", "borderWidth": 2},
                "label": {"show": True, "formatter": "{b}: {c} ({d}%)"},
                "data": [
                    {"value": item["count"], "name": item["sentiment"], "itemStyle": {
                        "color": "#52c41a" if item["sentiment"] == "positive" else "#ff4d4f" if item["sentiment"] == "negative" else "#1890ff"
                    }}
                    for item in stats["by_sentiment"]
                ]
            }],
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, echarts_data, 60)

        self.write(json.dumps({"code": 0, "data": echarts_data, "cached": False}))

    async def _get_timeline(self, use_cache: bool, cache_key_prefix: str):
        granularity = self.get_argument("granularity", "day")
        limit = int(self.get_argument("limit", 30))
        start_time, end_time = self._parse_time_range()

        cache_key = f"{cache_key_prefix}:{granularity}:{limit}:{start_time}:{end_time}"
        if use_cache:
            cached = self._get_cache(cache_key, 60)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        timeline_data = SentimentAnalysisRepository.get_time_series(
            granularity=granularity,
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )

        echarts_data = {
            "title": {"text": f"舆情趋势 ({granularity})", "left": "center"},
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["总量", "正面", "负面", "中性"], "bottom": 10},
            "grid": {"left": "3%", "right": "4%", "bottom": "15%", "containLabel": True},
            "xAxis": {
                "type": "category",
                "boundaryGap": False,
                "data": [item["time_bucket"] for item in timeline_data]
            },
            "yAxis": {"type": "value"},
            "series": [
                {
                    "name": "总量",
                    "type": "bar",
                    "smooth": True,
                    "data": [item["total_count"] for item in timeline_data],
                    "itemStyle": {"color": "#1890ff"}
                },
                {
                    "name": "正面",
                    "type": "line",
                    "smooth": True,
                    "data": [item.get("positive_count", 0) for item in timeline_data],
                    "lineStyle": {"width": 2},
                    "itemStyle": {"color": "#52c41a"}
                },
                {
                    "name": "负面",
                    "type": "line",
                    "smooth": True,
                    "data": [item.get("negative_count", 0) for item in timeline_data],
                    "lineStyle": {"width": 2},
                    "itemStyle": {"color": "#ff4d4f"}
                },
                {
                    "name": "中性",
                    "type": "line",
                    "smooth": True,
                    "data": [item.get("neutral_count", 0) for item in timeline_data],
                    "lineStyle": {"width": 2},
                    "itemStyle": {"color": "#faad14"}
                }
            ],
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, echarts_data, 60)

        self.write(json.dumps({"code": 0, "data": echarts_data, "cached": False}))

    async def _get_hotwords(self, use_cache: bool, cache_key_prefix: str):
        limit = int(self.get_argument("limit", 20))
        start_time, end_time = self._parse_time_range()

        cache_key = f"{cache_key_prefix}:{limit}:{start_time}:{end_time}"
        if use_cache:
            cached = self._get_cache(cache_key, 120)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        hotwords = SentimentAnalysisRepository.get_hot_keywords(
            limit=limit,
            start_time=start_time,
            end_time=end_time
        )

        echarts_data = {
            "title": {"text": "热词TOP" + str(limit), "left": "center"},
            "tooltip": {"trigger": "item"},
            "series": [{
                "type": "wordCloud",
                "shape": "circle",
                "left": "center",
                "top": "center",
                "width": "90%",
                "height": "80%",
                "sizeRange": [14, 60],
                "rotationRange": [-45, 45],
                "rotationStep": 15,
                "gridSize": 8,
                "drawOutOfBound": False,
                "textStyle": {
                    "fontFamily": "sans-serif",
                    "fontWeight": "bold",
                    "color": {"type": "random"}
                },
                "data": [
                    {"name": item["keyword"], "value": item["count"]}
                    for item in hotwords
                ]
            }],
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, echarts_data, 120)

        self.write(json.dumps({"code": 0, "data": echarts_data, "cached": False}))

    async def _get_risk_dist(self, use_cache: bool, cache_key_prefix: str):
        start_time, end_time = self._parse_time_range()

        cache_key = f"{cache_key_prefix}:{start_time}:{end_time}"
        if use_cache:
            cached = self._get_cache(cache_key, 60)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        stats = SentimentAnalysisRepository.get_sentiment_stats(
            start_time=start_time,
            end_time=end_time
        )

        echarts_data = {
            "title": {"text": "风险分布", "left": "center"},
            "tooltip": {"trigger": "item"},
            "legend": {"bottom": 10, "left": "center"},
            "series": [{
                "type": "pie",
                "radius": "65%",
                "center": ["50%", "50%"],
                "label": {"show": True, "formatter": "{b}: {c}"},
                "data": [
                    {"value": item["count"], "name": item["risk_level"], "itemStyle": {
                        "color": "#52c41a" if item["risk_level"] == "low" else "#faad14" if item["risk_level"] == "medium" else "#ff4d4f"
                    }}
                    for item in stats["by_risk"]
                ]
            }],
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, echarts_data, 60)

        self.write(json.dumps({"code": 0, "data": echarts_data, "cached": False}))

    async def _get_geo_data(self, use_cache: bool, cache_key_prefix: str):
        limit = int(self.get_argument("limit", 1000))
        sentiment = self.get_argument("sentiment", "")
        start_time, end_time = self._parse_time_range()

        cache_key = f"{cache_key_prefix}:{sentiment}:{limit}"
        if use_cache:
            cached = self._get_cache(cache_key, 120)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        analyses = SentimentAnalysisRepository.get_all(
            1, limit,
            sentiment=sentiment if sentiment else None,
            start_time=start_time,
            end_time=end_time
        )

        geo_data = {
            "type": "scatterGL",
            "data": []
        }

        for item in analyses:
            lat = item.get("location_lat")
            lng = item.get("location_lng")
            
            if lat and lng:
                geo_data["data"].append({
                    "name": item.get("location_name", item.get("title", "")),
                    "value": [lng, lat],
                    "item": {
                        "title": item.get("title", ""),
                        "content": item["content"][:100],
                        "sentiment": item["sentiment"],
                        "sentiment_score": item["sentiment_score"],
                        "confidence": item["confidence"],
                        "keywords": item.get("keywords", ""),
                        "risk_level": item["risk_level"],
                        "hot_score": item["hot_score"],
                        "analyze_time": item["analyze_time"]
                    }
                })
        
        geo_data["timestamp"] = datetime.now().isoformat()

        if use_cache:
            self._set_cache(cache_key, geo_data, 120)

        self.write(json.dumps({"code": 0, "data": geo_data, "cached": False}))


class SentimentAnalyzeHandler(BaseHandler):
    @tornado.web.authenticated
    async def post(self):
        action = self.get_body_argument("action", "analyze_all")

        start_time = time.time()
        log_id = SentimentAnalysisLogRepository.create(
            action=action,
            status="running",
            total_count=0
        )

        try:
            if action == "analyze_all":
                result = await self._analyze_all_data()
            elif action == "analyze_scout":
                result = await self._analyze_scout_data()
            elif action == "analyze_chat":
                result = await self._analyze_chat_data()
            else:
                self.write(json.dumps({"code": 1, "msg": "无效的操作"}))
                return

            duration_ms = int((time.time() - start_time) * 1000)
            SentimentAnalysisLogRepository.update(
                log_id,
                status="completed",
                total_count=result["total"],
                success_count=result["success"],
                fail_count=result["fail"],
                duration_ms=duration_ms
            )

            DataVCacheRepository.clear_all()

            self.write(json.dumps({
                "code": 0,
                "msg": f"分析完成，成功 {result['success']} 条，失败 {result['fail']} 条",
                "data": result,
                "duration_ms": duration_ms
            }))

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            SentimentAnalysisLogRepository.update(
                log_id,
                status="failed",
                error_msg=str(e),
                duration_ms=duration_ms
            )
            self.write(json.dumps({"code": 1, "msg": f"分析失败: {str(e)}"}))

    async def _analyze_all_data(self) -> dict:
        scout_result = await self._analyze_scout_data()
        chat_result = await self._analyze_chat_data()

        return {
            "total": scout_result["total"] + chat_result["total"],
            "success": scout_result["success"] + chat_result["success"],
            "fail": scout_result["fail"] + chat_result["fail"]
        }

    async def _analyze_scout_data(self) -> dict:
        records = ScoutRecordRepository.get_all(1, 1000)
        success_count = 0
        fail_count = 0

        for record in records:
            try:
                existing = SentimentAnalysisRepository.get_all(
                    1, 1,
                    source_type="scout",
                    start_time=record.get("collect_time"),
                    end_time=record.get("collect_time")
                )
                if existing and existing[0].get("source_record_id") == record["id"]:
                    continue

                result = SentimentAnalyzer.analyze_text(record.get("title", "") + " " + record.get("summary", ""))

                detail = ScoutDetailRepository.get_by_record_id(record["id"])
                content = record.get("title", "") + " " + record.get("summary", "")
                if detail:
                    content = detail.get("content", content)

                hot_score = SentimentAnalyzer.calculate_hot_score(
                    content,
                    result["sentiment"],
                    result["confidence"]
                )

                SentimentAnalysisRepository.create(
                    source_type="scout",
                    source_id=record.get("source_id"),
                    source_record_id=record["id"],
                    title=record.get("title"),
                    content=content[:5000],
                    summary=result["summary"],
                    sentiment=result["sentiment"],
                    sentiment_score=result["sentiment_score"],
                    confidence=result["confidence"],
                    keywords=result["keywords"],
                    risk_level=result["risk_level"],
                    risk_tags=result["risk_tags"],
                    hot_score=hot_score,
                    publish_time=record.get("collect_time")
                )

                ScoutRecordRepository.update(record["id"], ai_analyzed=1)

                if detail:
                    SentimentAnalysisRepository.update(
                        record["id"],
                        sentiment=result["sentiment"],
                        sentiment_score=result["sentiment_score"],
                        confidence=result["confidence"],
                        keywords=result["keywords"],
                        risk_level=result["risk_level"],
                        risk_tags=result["risk_tags"],
                        summary=result["summary"]
                    )

                success_count += 1

            except Exception as e:
                print(f"分析采集记录 {record['id']} 失败: {e}")
                fail_count += 1

        return {
            "total": len(records),
            "success": success_count,
            "fail": fail_count
        }

    async def _analyze_chat_data(self) -> dict:
        sessions = ChatSessionRepository.get_all(1, 500)
        success_count = 0
        fail_count = 0

        for session in sessions:
            try:
                messages = ChatMessageRepository.get_by_session_id(session["id"])
                if not messages:
                    continue

                chat_content = " ".join([f"{m['role']}: {m['content']}" for m in messages[:10]])

                result = SentimentAnalyzer.analyze_text(chat_content)

                hot_score = SentimentAnalyzer.calculate_hot_score(
                    chat_content,
                    result["sentiment"],
                    result["confidence"]
                )

                SentimentAnalysisRepository.create(
                    source_type="chat",
                    source_id=session["user_id"],
                    source_record_id=session["id"],
                    title=f"聊天会话 {session['id']}",
                    content=chat_content[:5000],
                    summary=result["summary"],
                    sentiment=result["sentiment"],
                    sentiment_score=result["sentiment_score"],
                    confidence=result["confidence"],
                    keywords=result["keywords"],
                    risk_level=result["risk_level"],
                    risk_tags=result["risk_tags"],
                    hot_score=hot_score,
                    publish_time=session.get("create_at")
                )

                success_count += 1

            except Exception as e:
                print(f"分析聊天会话 {session['id']} 失败: {e}")
                fail_count += 1

        return {
            "total": len(sessions),
            "success": success_count,
            "fail": fail_count
        }


class SentimentDetailHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self, analysis_id):
        try:
            analysis_id = int(analysis_id)
        except ValueError:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return

        analysis = SentimentAnalysisRepository.get_by_id(analysis_id)
        if not analysis:
            self.set_status(404)
            self.write(json.dumps({"code": 1, "msg": "分析记录不存在"}))
            return

        self.write(json.dumps({
            "code": 0,
            "data": analysis
        }))
