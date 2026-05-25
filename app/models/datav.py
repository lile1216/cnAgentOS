import sqlite3
import json
from datetime import datetime
from app.models.db import get_connection

class DataVScreenRepository:
    @staticmethod
    def create(name: str, description: str = "", config: str = None,
               refresh_interval: int = 60, enabled: bool = True) -> int:
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO datav_screen(name, description, config, refresh_interval, enabled)
                       VALUES(?, ?, ?, ?, ?)""",
                    (name, description, config or "{}", refresh_interval, 1 if enabled else 0)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return 0

    @staticmethod
    def get_all(page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM datav_screen ORDER BY create_at DESC LIMIT ? OFFSET ?",
                (page_size, offset)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_total_count():
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as total FROM datav_screen").fetchone()
            return row["total"] if row else 0

    @staticmethod
    def get_by_id(id: int):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM datav_screen WHERE id = ?", (id,)).fetchone()
            return dict(row) if row else None

    @staticmethod
    def get_enabled():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM datav_screen WHERE enabled = 1 ORDER BY create_at DESC").fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def update(id: int, name: str = None, description: str = None,
               config: str = None, refresh_interval: int = None, enabled: bool = None) -> bool:
        update_fields = []
        params = []

        if name is not None:
            update_fields.append("name = ?")
            params.append(name)
        if description is not None:
            update_fields.append("description = ?")
            params.append(description)
        if config is not None:
            update_fields.append("config = ?")
            params.append(config)
        if refresh_interval is not None:
            update_fields.append("refresh_interval = ?")
            params.append(refresh_interval)
        if enabled is not None:
            update_fields.append("enabled = ?")
            params.append(1 if enabled else 0)

        update_fields.append("update_at = datetime('now')")

        if len(update_fields) == 1:
            return False

        params.append(id)
        update_sql = f"UPDATE datav_screen SET {','.join(update_fields)} WHERE id = ?"

        try:
            with get_connection() as conn:
                conn.execute(update_sql, params)
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM datav_screen WHERE id = ?", (id,))
            conn.commit()
        return cursor.rowcount > 0


class DataVLocationRepository:
    @staticmethod
    def create(latitude: float, longitude: float, location_name: str = "",
               location_type: str = "default", source_id: int = None,
               source_type: str = "scout", title: str = "",
               summary: str = "", sentiment: str = "neutral",
               tags: str = "", event_time: str = None) -> int:
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO datav_location(latitude, longitude, location_name, location_type,
                       source_id, source_type, title, summary, sentiment, tags, event_time)
                       VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (latitude, longitude, location_name, location_type,
                     source_id, source_type, title, summary, sentiment, tags, event_time)
                )
                conn.commit()
                return cursor.lastrowid
        except (sqlite3.IntegrityError, ValueError):
            return 0

    @staticmethod
    def get_all(page: int = 1, page_size: int = 100,
                source_type: str = None, sentiment: str = None,
                start_time: str = None, end_time: str = None):
        offset = (page - 1) * page_size
        where_clauses = []
        params = []

        if source_type:
            where_clauses.append("source_type = ?")
            params.append(source_type)
        if sentiment:
            where_clauses.append("sentiment = ?")
            params.append(sentiment)
        if start_time:
            where_clauses.append("event_time >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("event_time <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM datav_location WHERE {where_sql} ORDER BY event_time DESC LIMIT ? OFFSET ?",
                (*params, page_size, offset)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_total_count(source_type: str = None, sentiment: str = None,
                        start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if source_type:
            where_clauses.append("source_type = ?")
            params.append(source_type)
        if sentiment:
            where_clauses.append("sentiment = ?")
            params.append(sentiment)
        if start_time:
            where_clauses.append("event_time >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("event_time <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            row = conn.execute(f"SELECT COUNT(*) as total FROM datav_location WHERE {where_sql}", tuple(params)).fetchone()
            return row["total"] if row else 0

    @staticmethod
    def get_geo_data(source_type: str = None, sentiment: str = None,
                     start_time: str = None, end_time: str = None, limit: int = 1000):
        where_clauses = []
        params = []

        if source_type:
            where_clauses.append("source_type = ?")
            params.append(source_type)
        if sentiment:
            where_clauses.append("sentiment = ?")
            params.append(sentiment)
        if start_time:
            where_clauses.append("create_at >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("create_at <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            rows = conn.execute(
                f"""SELECT location_lat as latitude, location_lng as longitude, location_name,
                    source_type as location_type, title, summary, sentiment, keywords as tags, create_at as event_time
                    FROM sentiment_analysis WHERE {where_sql} AND location_lat IS NOT NULL AND location_lng IS NOT NULL
                    ORDER BY create_at DESC LIMIT ?""",
                (*params, limit)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def delete(id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM datav_location WHERE id = ?", (id,))
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def batch_delete(ids: list) -> int:
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        with get_connection() as conn:
            cursor = conn.execute(f"DELETE FROM datav_location WHERE id IN ({placeholders})", tuple(ids))
            conn.commit()
        return cursor.rowcount

    @staticmethod
    def delete_old(days: int = 30) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """DELETE FROM datav_location
                   WHERE event_time < datetime('now', ?)""",
                (f"-{days} days",)
            )
            conn.commit()
        return cursor.rowcount


class DataVStatsRepository:
    @staticmethod
    def get_total_count(source_type: str = None, start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if source_type:
            where_clauses.append("source_type = ?")
            params.append(source_type)
        if start_time:
            where_clauses.append("create_at >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("create_at <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            row = conn.execute(f"SELECT COUNT(*) as total FROM sentiment_analysis WHERE {where_sql}", tuple(params)).fetchone()
            return row["total"] if row else 0

    @staticmethod
    def get_sentiment_distribution(source_type: str = None, start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if source_type:
            where_clauses.append("source_type = ?")
            params.append(source_type)
        if start_time:
            where_clauses.append("create_at >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("create_at <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            rows = conn.execute(
                f"""SELECT sentiment, COUNT(*) as count
                    FROM sentiment_analysis WHERE {where_sql}
                    GROUP BY sentiment""",
                tuple(params)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_source_distribution(start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if start_time:
            where_clauses.append("create_at >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("create_at <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            rows = conn.execute(
                f"""SELECT source_type, COUNT(*) as count
                    FROM sentiment_analysis WHERE {where_sql}
                    GROUP BY source_type""",
                tuple(params)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_time_series_stats(granularity: str = "day",
                              source_type: str = None, start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if source_type:
            where_clauses.append("source_type = ?")
            params.append(source_type)
        if start_time:
            where_clauses.append("create_at >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("create_at <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        if granularity == "hour":
            date_format = "%Y-%m-%d %H:00"
        elif granularity == "minute":
            date_format = "%Y-%m-%d %H:%i"
        else:
            date_format = "%Y-%m-%d"

        with get_connection() as conn:
            rows = conn.execute(
                f"""SELECT strftime('{date_format}', create_at) as time_bucket,
                           COUNT(*) as count,
                           SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                           SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                           SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count
                    FROM sentiment_analysis WHERE {where_sql}
                    GROUP BY time_bucket
                    ORDER BY time_bucket DESC""",
                tuple(params)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_hot_tags(limit: int = 20, start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if start_time:
            where_clauses.append("create_at >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("create_at <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            rows = conn.execute(
                f"""SELECT keywords, COUNT(*) as count
                    FROM sentiment_analysis WHERE {where_sql} AND keywords IS NOT NULL AND keywords != ''
                    GROUP BY keywords
                    ORDER BY count DESC LIMIT ?""",
                (*params, limit)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_scout_stats(start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if start_time:
            where_clauses.append("collect_time >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("collect_time <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) as total FROM scout_record WHERE {where_sql}",
                tuple(params)
            ).fetchone()["total"]

            analyzed = conn.execute(
                f"SELECT COUNT(*) as analyzed FROM scout_record WHERE {where_sql} AND ai_analyzed = 1",
                tuple(params)
            ).fetchone()["analyzed"]

            by_source = conn.execute(
                f"""SELECT source_name, COUNT(*) as count
                    FROM scout_record WHERE {where_sql}
                    GROUP BY source_name""",
                tuple(params)
            ).fetchall()

            return {
                "total": total,
                "analyzed": analyzed,
                "unanalyzed": total - analyzed,
                "by_source": [dict(row) for row in by_source]
            }

    @staticmethod
    def get_chat_stats(start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if start_time:
            where_clauses.append("cs.create_at >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("cs.create_at <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            total_sessions = conn.execute(
                f"SELECT COUNT(*) as total FROM chat_session cs WHERE {where_sql}",
                tuple(params)
            ).fetchone()["total"]

            total_messages = conn.execute(
                f"""SELECT COUNT(*) as total FROM chat_message cm
                    JOIN chat_session cs ON cm.session_id = cs.id
                    WHERE {where_sql}""",
                tuple(params)
            ).fetchone()["total"]

            by_role = conn.execute(
                f"""SELECT cm.role, COUNT(*) as count
                    FROM chat_message cm
                    JOIN chat_session cs ON cm.session_id = cs.id
                    WHERE {where_sql}
                    GROUP BY cm.role""",
                tuple(params)
            ).fetchall()

            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "by_role": [dict(row) for row in by_role]
            }


class DataVCacheRepository:
    @staticmethod
    def get(cache_key: str):
        with get_connection() as conn:
            row = conn.execute(
                """SELECT cache_value, expire_at FROM datav_cache
                   WHERE cache_key = ? AND (expire_at IS NULL OR expire_at > datetime('now'))""",
                (cache_key,)
            ).fetchone()
            if row:
                try:
                    return json.loads(row["cache_value"])
                except json.JSONDecodeError:
                    return row["cache_value"]
            return None

    @staticmethod
    def set(cache_key: str, cache_value, expire_seconds: int = 300):
        cache_value_str = json.dumps(cache_value) if not isinstance(cache_value, str) else cache_value

        with get_connection() as conn:
            if expire_seconds > 0:
                conn.execute(
                    """INSERT OR REPLACE INTO datav_cache(cache_key, cache_value, expire_at, update_at)
                       VALUES(?, ?, datetime('now', ?), datetime('now'))""",
                    (cache_key, cache_value_str, f"+{expire_seconds} seconds")
                )
            else:
                conn.execute(
                    """INSERT OR REPLACE INTO datav_cache(cache_key, cache_value, expire_at, update_at)
                       VALUES(?, ?, NULL, datetime('now'))""",
                    (cache_key, cache_value_str)
                )
            conn.commit()

    @staticmethod
    def delete(cache_key: str) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM datav_cache WHERE cache_key = ?", (cache_key,))
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def clear_expired():
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM datav_cache WHERE expire_at IS NOT NULL AND expire_at <= datetime('now')")
            conn.commit()
        return cursor.rowcount

    @staticmethod
    def clear_all():
        with get_connection() as conn:
            conn.execute("DELETE FROM datav_cache")
            conn.commit()
