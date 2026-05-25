import json
import tornado.web
import tornado.gen
from datetime import datetime, timedelta

from app.controllers.base import BaseHandler
from app.models.datav import (
    DataVScreenRepository, DataVLocationRepository,
    DataVStatsRepository, DataVCacheRepository
)
from app.models.warehouse import ScoutRecordRepository
from app.models.chat import ChatSessionRepository, ChatMessageRepository

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("警告: redis 未安装，将使用本地缓存。请运行: pip install redis")


class DataVListHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        xsrf_token = self.xsrf_token.decode('utf-8')
        self.render("datav_list.html", current_user=self.current_user, xsrf_token=xsrf_token)


class DataVScreenHandler(BaseHandler):
    def get(self):
        mode = self.get_argument("mode", "view")
        self.render("datav_screen.html", fullscreen=mode == "fullscreen")


class DataVApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 20))
        except ValueError:
            page, page_size = 1, 20

        screens = DataVScreenRepository.get_all(page, page_size)
        total = DataVScreenRepository.get_total_count()

        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "count": total,
            "data": screens
        }))

    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")

        if action == "add":
            self._add_screen()
        elif action == "edit":
            self._edit_screen()
        elif action == "delete":
            self._delete_screen()
        elif action == "toggle":
            self._toggle_screen()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _add_screen(self):
        name = self.get_body_argument("name", "").strip()
        description = self.get_body_argument("description", "").strip()
        config = self.get_body_argument("config", "{}")
        refresh_interval = int(self.get_body_argument("refresh_interval", 60))

        if not name:
            self.write(json.dumps({"code": 1, "msg": "大屏名称不能为空"}))
            return

        screen_id = DataVScreenRepository.create(
            name=name,
            description=description,
            config=config,
            refresh_interval=refresh_interval
        )

        if screen_id:
            self.write(json.dumps({"code": 0, "msg": "创建成功", "data": {"id": screen_id}}))
        else:
            self.write(json.dumps({"code": 1, "msg": "创建失败"}))

    def _edit_screen(self):
        screen_id = self.get_body_argument("id", "")
        name = self.get_body_argument("name", "").strip()
        description = self.get_body_argument("description", "").strip()
        config = self.get_body_argument("config", None)
        refresh_interval = self.get_body_argument("refresh_interval", None)

        if not screen_id:
            self.write(json.dumps({"code": 1, "msg": "大屏ID不能为空"}))
            return

        try:
            screen_id = int(screen_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的大屏ID"}))
            return

        if not name:
            self.write(json.dumps({"code": 1, "msg": "大屏名称不能为空"}))
            return

        if DataVScreenRepository.update(screen_id, name=name, description=description,
                                         config=config,
                                         refresh_interval=int(refresh_interval) if refresh_interval else None):
            self.write(json.dumps({"code": 0, "msg": "更新成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "更新失败"}))

    def _delete_screen(self):
        screen_id = self.get_body_argument("id", "")
        if not screen_id:
            self.write(json.dumps({"code": 1, "msg": "大屏ID不能为空"}))
            return

        try:
            screen_id = int(screen_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的大屏ID"}))
            return

        if DataVScreenRepository.delete(screen_id):
            self.write(json.dumps({"code": 0, "msg": "删除成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "删除失败"}))

    def _toggle_screen(self):
        screen_id = self.get_body_argument("id", "")
        if not screen_id:
            self.write(json.dumps({"code": 1, "msg": "大屏ID不能为空"}))
            return

        try:
            screen_id = int(screen_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的大屏ID"}))
            return

        screen = DataVScreenRepository.get_by_id(screen_id)
        if not screen:
            self.write(json.dumps({"code": 1, "msg": "大屏不存在"}))
            return

        enabled = 0 if screen["enabled"] else 1
        if DataVScreenRepository.update(screen_id, enabled=enabled):
            self.write(json.dumps({"code": 0, "msg": "操作成功", "data": {"enabled": enabled}}))
        else:
            self.write(json.dumps({"code": 1, "msg": "操作失败"}))


class DataVStatsApiHandler(BaseHandler):
    def initialize(self):
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
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
        cache_key_prefix = f"datav:stats:{data_type}"

        if data_type == "all":
            await self._get_all_stats(use_cache, cache_key_prefix)
        elif data_type == "geo":
            await self._get_geo_data(use_cache, cache_key_prefix)
        elif data_type == "sentiment":
            await self._get_sentiment(use_cache, cache_key_prefix)
        elif data_type == "source":
            await self._get_source_distribution(use_cache, cache_key_prefix)
        elif data_type == "timeline":
            await self._get_timeline(use_cache, cache_key_prefix)
        elif data_type == "hotwords":
            await self._get_hotwords(use_cache, cache_key_prefix)
        elif data_type == "scout":
            await self._get_scout_stats(use_cache, cache_key_prefix)
        elif data_type == "chat":
            await self._get_chat_stats(use_cache, cache_key_prefix)
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

        stats = {
            "total_count": DataVStatsRepository.get_total_count(start_time=start_time, end_time=end_time),
            "sentiment_distribution": DataVStatsRepository.get_sentiment_distribution(start_time=start_time, end_time=end_time),
            "source_distribution": DataVStatsRepository.get_source_distribution(start_time=start_time, end_time=end_time),
            "timeline": DataVStatsRepository.get_time_series_stats(granularity="day", start_time=start_time, end_time=end_time),
            "hot_tags": DataVStatsRepository.get_hot_tags(limit=20, start_time=start_time, end_time=end_time),
            "scout_stats": DataVStatsRepository.get_scout_stats(start_time=start_time, end_time=end_time),
            "chat_stats": DataVStatsRepository.get_chat_stats(start_time=start_time, end_time=end_time),
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, stats, 60)

        self.write(json.dumps({"code": 0, "data": stats, "cached": False}))

    async def _get_geo_data(self, use_cache: bool, cache_key_prefix: str):
        source_type = self.get_argument("source_type", "")
        sentiment = self.get_argument("sentiment", "")
        limit = int(self.get_argument("limit", 1000))
        start_time, end_time = self._parse_time_range()

        cache_key = f"{cache_key_prefix}:{source_type}:{sentiment}:{limit}"
        if use_cache:
            cached = self._get_cache(cache_key, 120)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        geo_data = DataVLocationRepository.get_geo_data(
            source_type=source_type if source_type else None,
            sentiment=sentiment if sentiment else None,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

        echarts_data = {
            "type": "scatterGL",
            "data": [
                {
                    "name": item.get("location_name", item.get("title", "")),
                    "value": [item["longitude"], item["latitude"]],
                    "item": {
                        "title": item.get("title", ""),
                        "summary": item.get("summary", ""),
                        "sentiment": item.get("sentiment", "neutral"),
                        "tags": item.get("tags", ""),
                        "event_time": item.get("event_time", "")
                    }
                }
                for item in geo_data
                if item.get("latitude") and item.get("longitude")
            ],
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, echarts_data, 120)

        self.write(json.dumps({"code": 0, "data": echarts_data, "cached": False}))

    async def _get_sentiment(self, use_cache: bool, cache_key_prefix: str):
        start_time, end_time = self._parse_time_range()

        cache_key = f"{cache_key_prefix}:{start_time}:{end_time}"
        if use_cache:
            cached = self._get_cache(cache_key, 60)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        sentiment_data = DataVStatsRepository.get_sentiment_distribution(start_time=start_time, end_time=end_time)

        echarts_data = {
            "title": {"text": "情感分布", "left": "center"},
            "tooltip": {"trigger": "item"},
            "legend": {"bottom": 10, "left": "center"},
            "series": [{
                "type": "pie",
                "radius": ["40%", "70%"],
                "avoidLabelOverlap": False,
                "itemStyle": {
                    "borderRadius": 10,
                    "borderColor": "#fff",
                    "borderWidth": 2
                },
                "label": {"show": True, "formatter": "{b}: {c} ({d}%)"},
                "data": [
                    {"value": item["count"], "name": item["sentiment"], "itemStyle": {
                        "color": "#52c41a" if item["sentiment"] == "positive" else "#ff4d4f" if item["sentiment"] == "negative" else "#1890ff"
                    }}
                    for item in sentiment_data
                ]
            }],
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, echarts_data, 60)

        self.write(json.dumps({"code": 0, "data": echarts_data, "cached": False}))

    async def _get_source_distribution(self, use_cache: bool, cache_key_prefix: str):
        start_time, end_time = self._parse_time_range()

        cache_key = f"{cache_key_prefix}:{start_time}:{end_time}"
        if use_cache:
            cached = self._get_cache(cache_key, 60)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        source_data = DataVStatsRepository.get_source_distribution(start_time=start_time, end_time=end_time)

        echarts_data = {
            "title": {"text": "来源分布", "left": "center"},
            "tooltip": {"trigger": "item"},
            "legend": {"bottom": 10, "left": "center"},
            "series": [{
                "type": "pie",
                "radius": "65%",
                "center": ["50%", "50%"],
                "label": {"show": True, "formatter": "{b}: {c}"},
                "data": [
                    {"value": item["count"], "name": item["source_type"]}
                    for item in source_data
                ]
            }],
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, echarts_data, 60)

        self.write(json.dumps({"code": 0, "data": echarts_data, "cached": False}))

    async def _get_timeline(self, use_cache: bool, cache_key_prefix: str):
        granularity = self.get_argument("granularity", "day")
        start_time, end_time = self._parse_time_range()

        cache_key = f"{cache_key_prefix}:{granularity}:{start_time}:{end_time}"
        if use_cache:
            cached = self._get_cache(cache_key, 60)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        timeline_data = DataVStatsRepository.get_time_series_stats(
            granularity=granularity,
            start_time=start_time,
            end_time=end_time
        )

        echarts_data = {
            "title": {"text": f"时序趋势 ({granularity})", "left": "center"},
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
                    "type": "line",
                    "smooth": True,
                    "data": [item["count"] for item in timeline_data],
                    "areaStyle": {"opacity": 0.3},
                    "lineStyle": {"width": 2},
                    "itemStyle": {"color": "#1890ff"}
                },
                {
                    "name": "正面",
                    "type": "line",
                    "smooth": True,
                    "data": [item.get("positive_count", 0) for item in timeline_data],
                    "lineStyle": {"width": 1},
                    "itemStyle": {"color": "#52c41a"}
                },
                {
                    "name": "负面",
                    "type": "line",
                    "smooth": True,
                    "data": [item.get("negative_count", 0) for item in timeline_data],
                    "lineStyle": {"width": 1},
                    "itemStyle": {"color": "#ff4d4f"}
                },
                {
                    "name": "中性",
                    "type": "line",
                    "smooth": True,
                    "data": [item.get("neutral_count", 0) for item in timeline_data],
                    "lineStyle": {"width": 1},
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

        hotwords_data = DataVStatsRepository.get_hot_tags(limit=limit, start_time=start_time, end_time=end_time)

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
                    "color": {
                        "type": "random"
                    }
                },
                "data": [
                    {"name": item["tags"], "value": item["count"]}
                    for item in hotwords_data
                ]
            }],
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, echarts_data, 120)

        self.write(json.dumps({"code": 0, "data": echarts_data, "cached": False}))

    async def _get_scout_stats(self, use_cache: bool, cache_key_prefix: str):
        start_time, end_time = self._parse_time_range()

        cache_key = f"{cache_key_prefix}:{start_time}:{end_time}"
        if use_cache:
            cached = self._get_cache(cache_key, 60)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        scout_stats = DataVStatsRepository.get_scout_stats(start_time=start_time, end_time=end_time)

        echarts_data = {
            "title": {"text": "瞭望采集统计", "left": "center"},
            "tooltip": {"trigger": "item"},
            "series": [
                {
                    "type": "gauge",
                    "center": ["50%", "60%"],
                    "radius": "80%",
                    "startAngle": 200,
                    "endAngle": -20,
                    "min": 0,
                    "max": scout_stats["total"] or 1,
                    "splitNumber": 8,
                    "axisLine": {"lineStyle": {"width": 6}},
                    "pointer": {"width": 5},
                    "axisTick": {"distance": -10, "length": 5},
                    "splitLine": {"distance": -10, "length": 10},
                    "axisLabel": {"distance": 15},
                    "detail": {"valueAnimation": True, "formatter": "{value}", "fontSize": 20, "offsetCenter": [0, "70%"]},
                    "data": [{"value": scout_stats["analyzed"], "name": "已分析"}]
                }
            ],
            "stat_data": scout_stats,
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, echarts_data, 60)

        self.write(json.dumps({"code": 0, "data": echarts_data, "cached": False}))

    async def _get_chat_stats(self, use_cache: bool, cache_key_prefix: str):
        start_time, end_time = self._parse_time_range()

        cache_key = f"{cache_key_prefix}:{start_time}:{end_time}"
        if use_cache:
            cached = self._get_cache(cache_key, 60)
            if cached:
                self.write(json.dumps({"code": 0, "data": cached, "cached": True}))
                return

        chat_stats = DataVStatsRepository.get_chat_stats(start_time=start_time, end_time=end_time)

        echarts_data = {
            "title": {"text": "智能问答统计", "left": "center"},
            "tooltip": {"trigger": "axis"},
            "grid": {"left": "3%", "right": "4%", "bottom": "10%", "containLabel": True},
            "xAxis": {"type": "category", "data": ["会话数", "消息数"]},
            "yAxis": {"type": "value"},
            "series": [{
                "type": "bar",
                "data": [chat_stats["total_sessions"], chat_stats["total_messages"]],
                "itemStyle": {"color": "#1890ff"}
            }],
            "stat_data": chat_stats,
            "timestamp": datetime.now().isoformat()
        }

        if use_cache:
            self._set_cache(cache_key, echarts_data, 60)

        self.write(json.dumps({"code": 0, "data": echarts_data, "cached": False}))


class DataVLocationApiHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        try:
            page = int(self.get_argument("page", 1))
            page_size = int(self.get_argument("limit", 20))
        except ValueError:
            page, page_size = 1, 20

        source_type = self.get_argument("source_type", "")
        sentiment = self.get_argument("sentiment", "")
        start_time = self.get_argument("start_time", "")
        end_time = self.get_argument("end_time", "")

        locations = DataVLocationRepository.get_all(
            page, page_size,
            source_type=source_type if source_type else None,
            sentiment=sentiment if sentiment else None,
            start_time=start_time if start_time else None,
            end_time=end_time if end_time else None
        )
        total = DataVLocationRepository.get_total_count(
            source_type=source_type if source_type else None,
            sentiment=sentiment if sentiment else None,
            start_time=start_time if start_time else None,
            end_time=end_time if end_time else None
        )

        self.write(json.dumps({
            "code": 0,
            "msg": "success",
            "count": total,
            "data": locations
        }))

    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")

        if action == "add":
            self._add_location()
        elif action == "batchAdd":
            self._batch_add_locations()
        elif action == "delete":
            self._delete_location()
        elif action == "batchDelete":
            self._batch_delete_locations()
        elif action == "clearOld":
            self._clear_old_locations()
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))

    def _add_location(self):
        latitude = self.get_body_argument("latitude", "")
        longitude = self.get_body_argument("longitude", "")
        location_name = self.get_body_argument("location_name", "")
        location_type = self.get_body_argument("location_type", "default")
        source_id = self.get_body_argument("source_id", "")
        source_type = self.get_body_argument("source_type", "scout")
        title = self.get_body_argument("title", "")
        summary = self.get_body_argument("summary", "")
        sentiment = self.get_body_argument("sentiment", "neutral")
        tags = self.get_body_argument("tags", "")
        event_time = self.get_body_argument("event_time", "")

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "经纬度格式无效"}))
            return

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            self.write(json.dumps({"code": 1, "msg": "经纬度超出有效范围"}))
            return

        location_id = DataVLocationRepository.create(
            latitude=latitude,
            longitude=longitude,
            location_name=location_name,
            location_type=location_type,
            source_id=int(source_id) if source_id else None,
            source_type=source_type,
            title=title,
            summary=summary,
            sentiment=sentiment,
            tags=tags,
            event_time=event_time if event_time else None
        )

        if location_id:
            self.write(json.dumps({"code": 0, "msg": "添加成功", "data": {"id": location_id}}))
        else:
            self.write(json.dumps({"code": 1, "msg": "添加失败"}))

    def _batch_add_locations(self):
        locations_json = self.get_body_argument("locations", "[]")
        try:
            locations = json.loads(locations_json)
        except json.JSONDecodeError:
            self.write(json.dumps({"code": 1, "msg": "数据格式无效"}))
            return

        if not locations:
            self.write(json.dumps({"code": 1, "msg": "没有要添加的数据"}))
            return

        added_count = 0
        for loc in locations:
            try:
                if loc.get("latitude") and loc.get("longitude"):
                    DataVLocationRepository.create(
                        latitude=float(loc["latitude"]),
                        longitude=float(loc["longitude"]),
                        location_name=loc.get("location_name", ""),
                        location_type=loc.get("location_type", "default"),
                        source_id=loc.get("source_id"),
                        source_type=loc.get("source_type", "scout"),
                        title=loc.get("title", ""),
                        summary=loc.get("summary", ""),
                        sentiment=loc.get("sentiment", "neutral"),
                        tags=loc.get("tags", ""),
                        event_time=loc.get("event_time")
                    )
                    added_count += 1
            except (ValueError, KeyError):
                continue

        self.write(json.dumps({"code": 0, "msg": f"成功添加 {added_count} 条记录"}))

    def _delete_location(self):
        location_id = self.get_body_argument("id", "")
        if not location_id:
            self.write(json.dumps({"code": 1, "msg": "ID不能为空"}))
            return

        try:
            location_id = int(location_id)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID"}))
            return

        if DataVLocationRepository.delete(location_id):
            self.write(json.dumps({"code": 0, "msg": "删除成功"}))
        else:
            self.write(json.dumps({"code": 1, "msg": "删除失败"}))

    def _batch_delete_locations(self):
        ids_str = self.get_body_argument("ids", "")
        if not ids_str:
            self.write(json.dumps({"code": 1, "msg": "请选择要删除的记录"}))
            return

        try:
            ids = [int(id.strip()) for id in ids_str.split(",") if id.strip()]
            deleted_count = DataVLocationRepository.batch_delete(ids)
            self.write(json.dumps({"code": 0, "msg": f"成功删除 {deleted_count} 条记录"}))
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的ID列表"}))

    def _clear_old_locations(self):
        days = self.get_body_argument("days", "30")
        try:
            days = int(days)
        except ValueError:
            self.write(json.dumps({"code": 1, "msg": "无效的天数"}))
            return

        deleted_count = DataVLocationRepository.delete_old(days)
        self.write(json.dumps({"code": 0, "msg": f"成功删除 {deleted_count} 条过期记录"}))


class DataVCacheClearHandler(BaseHandler):
    @tornado.web.authenticated
    def post(self):
        action = self.get_body_argument("action", "")

        if action == "clearExpired":
            count = DataVCacheRepository.clear_expired()
            self.write(json.dumps({"code": 0, "msg": f"已清理 {count} 条过期缓存"}))
        elif action == "clearAll":
            DataVCacheRepository.clear_all()
            self.write(json.dumps({"code": 0, "msg": "已清理所有缓存"}))
        else:
            self.set_status(400)
            self.write(json.dumps({"code": 1, "msg": "无效的操作"}))
