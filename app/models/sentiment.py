import sqlite3
import json
import re
from datetime import datetime
from app.models.db import get_connection

class SentimentAnalysisRepository:
    @staticmethod
    def create(source_type: str, content: str, source_id: int = None,
               source_record_id: int = None, title: str = None,
               summary: str = None, sentiment: str = "neutral",
               sentiment_score: float = 0.5, confidence: float = 0.0,
               keywords: str = None, topics: str = None,
               hot_score: float = 0.0, risk_level: str = "low",
               risk_tags: str = None, location_lat: float = None,
               location_lng: float = None, location_name: str = None,
               publish_time: str = None, analyze_time: str = None) -> int:
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    """INSERT INTO sentiment_analysis(source_type, source_id, source_record_id,
                       title, content, summary, sentiment, sentiment_score, confidence,
                       keywords, topics, hot_score, risk_level, risk_tags,
                       location_lat, location_lng, location_name, publish_time, analyze_time)
                       VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (source_type, source_id, source_record_id, title, content,
                     summary, sentiment, sentiment_score, confidence, keywords,
                     topics, hot_score, risk_level, risk_tags, location_lat,
                     location_lng, location_name, publish_time, analyze_time)
                )
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return 0

    @staticmethod
    def get_all(page: int = 1, page_size: int = 20,
                sentiment: str = None, source_type: str = None,
                risk_level: str = None, keyword: str = None,
                start_time: str = None, end_time: str = None):
        offset = (page - 1) * page_size
        where_clauses = []
        params = []

        if sentiment:
            where_clauses.append("sentiment = ?")
            params.append(sentiment)
        if source_type:
            where_clauses.append("source_type = ?")
            params.append(source_type)
        if risk_level:
            where_clauses.append("risk_level = ?")
            params.append(risk_level)
        if keyword:
            where_clauses.append("(title LIKE ? OR content LIKE ? OR keywords LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        if start_time:
            where_clauses.append("analyze_time >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("analyze_time <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM sentiment_analysis WHERE {where_sql} ORDER BY analyze_time DESC LIMIT ? OFFSET ?",
                (*params, page_size, offset)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_total_count(sentiment: str = None, source_type: str = None,
                        risk_level: str = None, keyword: str = None,
                        start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if sentiment:
            where_clauses.append("sentiment = ?")
            params.append(sentiment)
        if source_type:
            where_clauses.append("source_type = ?")
            params.append(source_type)
        if risk_level:
            where_clauses.append("risk_level = ?")
            params.append(risk_level)
        if keyword:
            where_clauses.append("(title LIKE ? OR content LIKE ? OR keywords LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])
        if start_time:
            where_clauses.append("analyze_time >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("analyze_time <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            row = conn.execute(
                f"SELECT COUNT(*) as total FROM sentiment_analysis WHERE {where_sql}",
                tuple(params)
            ).fetchone()
            return row["total"] if row else 0

    @staticmethod
    def get_by_id(id: int):
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM sentiment_analysis WHERE id = ?",
                (id,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def update(id: int, **kwargs):
        update_fields = []
        params = []

        allowed_fields = ['title', 'content', 'summary', 'sentiment', 'sentiment_score',
                         'confidence', 'keywords', 'topics', 'hot_score', 'risk_level',
                         'risk_tags', 'location_lat', 'location_lng', 'location_name',
                         'publish_time']

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                update_fields.append(f"{key} = ?")
                params.append(value)

        if not update_fields:
            return False

        update_fields.append("update_at = datetime('now')")
        params.append(id)

        with get_connection() as conn:
            conn.execute(
                f"UPDATE sentiment_analysis SET {','.join(update_fields)} WHERE id = ?",
                params
            )
            conn.commit()
        return True

    @staticmethod
    def delete(id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM sentiment_analysis WHERE id = ?",
                (id,)
            )
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def batch_delete(ids: list) -> int:
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        with get_connection() as conn:
            cursor = conn.execute(
                f"DELETE FROM sentiment_analysis WHERE id IN ({placeholders})",
                tuple(ids)
            )
            conn.commit()
        return cursor.rowcount

    @staticmethod
    def get_by_source(source_type: str, source_id: int = None, limit: int = 100):
        where_clauses = ["source_type = ?"]
        params = [source_type]

        if source_id:
            where_clauses.append("source_id = ?")
            params.append(source_id)

        where_sql = " AND ".join(where_clauses)

        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM sentiment_analysis WHERE {where_sql} ORDER BY analyze_time DESC LIMIT ?",
                (*params, limit)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_sentiment_stats(start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if start_time:
            where_clauses.append("analyze_time >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("analyze_time <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            total = conn.execute(
                f"SELECT COUNT(*) as total FROM sentiment_analysis WHERE {where_sql}",
                tuple(params)
            ).fetchone()["total"]

            by_sentiment = conn.execute(
                f"""SELECT sentiment, COUNT(*) as count, AVG(confidence) as avg_confidence
                    FROM sentiment_analysis WHERE {where_sql}
                    GROUP BY sentiment""",
                tuple(params)
            ).fetchall()

            by_risk = conn.execute(
                f"""SELECT risk_level, COUNT(*) as count
                    FROM sentiment_analysis WHERE {where_sql}
                    GROUP BY risk_level""",
                tuple(params)
            ).fetchall()

            by_source = conn.execute(
                f"""SELECT source_type, COUNT(*) as count
                    FROM sentiment_analysis WHERE {where_sql}
                    GROUP BY source_type""",
                tuple(params)
            ).fetchall()

            return {
                "total": total,
                "by_sentiment": [dict(row) for row in by_sentiment],
                "by_risk": [dict(row) for row in by_risk],
                "by_source": [dict(row) for row in by_source]
            }

    @staticmethod
    def get_hot_keywords(limit: int = 20, start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if start_time:
            where_clauses.append("analyze_time >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("analyze_time <= ?")
            params.append(end_time)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        with get_connection() as conn:
            rows = conn.execute(
                f"""SELECT keywords, hot_score FROM sentiment_analysis
                    WHERE {where_sql} AND keywords IS NOT NULL AND keywords != ''
                    ORDER BY hot_score DESC LIMIT ?""",
                (*params, limit)
            ).fetchall()

        keyword_freq = {}
        for row in rows:
            if row["keywords"]:
                for kw in row["keywords"].split(","):
                    kw = kw.strip()
                    if kw:
                        keyword_freq[kw] = keyword_freq.get(kw, 0) + row["hot_score"]

        sorted_kw = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"keyword": k, "count": int(v)} for k, v in sorted_kw]

    @staticmethod
    def get_time_series(granularity: str = "day", limit: int = 30,
                        start_time: str = None, end_time: str = None):
        where_clauses = []
        params = []

        if start_time:
            where_clauses.append("analyze_time >= ?")
            params.append(start_time)
        if end_time:
            where_clauses.append("analyze_time <= ?")
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
                f"""SELECT strftime('{date_format}', analyze_time) as time_bucket,
                           COUNT(*) as total_count,
                           SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) as positive_count,
                           SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) as negative_count,
                           SUM(CASE WHEN sentiment = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                           SUM(hot_score) as total_hot_score
                    FROM sentiment_analysis WHERE {where_sql}
                    GROUP BY time_bucket
                    ORDER BY time_bucket DESC LIMIT ?""",
                (*params, limit)
            ).fetchall()
            return [dict(row) for row in rows]


class SentimentAnalysisLogRepository:
    @staticmethod
    def create(analysis_id: int = None, action: str = "analyze",
               status: str = "running", total_count: int = 0) -> int:
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO sentiment_analysis_log(analysis_id, action, status, total_count)
                   VALUES(?, ?, ?, ?)""",
                (analysis_id, action, status, total_count)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def update(id: int, status: str = None, total_count: int = None,
               success_count: int = None, fail_count: int = None,
               error_msg: str = None, duration_ms: int = None):
        update_fields = []
        params = []

        if status:
            update_fields.append("status = ?")
            params.append(status)
        if total_count is not None:
            update_fields.append("total_count = ?")
            params.append(total_count)
        if success_count is not None:
            update_fields.append("success_count = ?")
            params.append(success_count)
        if fail_count is not None:
            update_fields.append("fail_count = ?")
            params.append(fail_count)
        if error_msg:
            update_fields.append("error_msg = ?")
            params.append(error_msg)
        if duration_ms is not None:
            update_fields.append("duration_ms = ?")
            params.append(duration_ms)

        if not update_fields:
            return False

        params.append(id)
        with get_connection() as conn:
            conn.execute(
                f"UPDATE sentiment_analysis_log SET {','.join(update_fields)} WHERE id = ?",
                params
            )
            conn.commit()
        return True

    @staticmethod
    def get_all(page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM sentiment_analysis_log
                   ORDER BY create_at DESC LIMIT ? OFFSET ?""",
                (page_size, offset)
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def get_total_count():
        with get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as total FROM sentiment_analysis_log"
            ).fetchone()
            return row["total"] if row else 0


class SentimentAnalyzer:
    @staticmethod
    def analyze_text(text: str, use_ai: bool = True) -> dict:
        if use_ai:
            return SentimentAnalyzer._analyze_with_ai(text)
        else:
            return SentimentAnalyzer._analyze_with_rules(text)

    @staticmethod
    def _analyze_with_rules(text: str) -> dict:
        positive_words = ["好", "棒", "优秀", "满意", "喜欢", "赞", "支持", "积极", "正面", "good", "great", "excellent"]
        negative_words = ["差", "烂", "糟糕", "不满", "讨厌", "垃圾", "负面", "消极", "bad", "terrible", "awful"]

        pos_count = sum(1 for w in positive_words if w in text.lower())
        neg_count = sum(1 for w in negative_words if w in text.lower())

        total = pos_count + neg_count
        if total == 0:
            sentiment = "neutral"
            score = 0.5
            confidence = 0.3
        elif pos_count > neg_count:
            sentiment = "positive"
            score = 0.5 + (pos_count - neg_count) / (total * 2)
            confidence = min(0.9, 0.5 + total * 0.1)
        else:
            sentiment = "negative"
            score = 0.5 - (neg_count - pos_count) / (total * 2)
            confidence = min(0.9, 0.5 + total * 0.1)

        keywords = SentimentAnalyzer._extract_keywords(text)
        risk_level, risk_tags = SentimentAnalyzer._detect_risk(text)

        return {
            "sentiment": sentiment,
            "sentiment_score": max(0, min(1, score)),
            "confidence": confidence,
            "keywords": ",".join(keywords[:10]),
            "risk_level": risk_level,
            "risk_tags": ",".join(risk_tags),
            "summary": text[:200] if len(text) > 200 else text
        }

    @staticmethod
    def _analyze_with_ai(text: str) -> dict:
        from app.models.model_service import ModelServiceRepository

        default_model = ModelServiceRepository.get_default()
        if not default_model:
            return SentimentAnalyzer._analyze_with_rules(text)

        try:
            prompt = f"""请分析以下文本的情感倾向，并提取关键信息。

文本内容：
{text[:1000]}

请以JSON格式返回分析结果，包含以下字段：
- sentiment: 情感倾向 (positive/negative/neutral)
- sentiment_score: 情感得分 (0-1之间的浮点数，0表示极度负面，1表示极度正面)
- confidence: 置信度 (0-1之间的浮点数)
- keywords: 关键词列表，用逗号分隔，最多10个
- summary: 内容摘要（不超过100字）
- risk_level: 风险等级 (low/medium/high)
- risk_tags: 风险标签列表，用逗号分隔

请直接返回JSON，不要有其他内容："""

            from openai import OpenAI
            client = OpenAI(
                api_key=default_model["api_key"],
                base_url=default_model["base_url"] if default_model["base_url"] else None
            )

            response = client.chat.completions.create(
                model=default_model["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result = json.loads(result_text.strip())

            return {
                "sentiment": result.get("sentiment", "neutral"),
                "sentiment_score": float(result.get("sentiment_score", 0.5)),
                "confidence": float(result.get("confidence", 0.5)),
                "keywords": ",".join(result.get("keywords", [])[:10]),
                "risk_level": result.get("risk_level", "low"),
                "risk_tags": ",".join(result.get("risk_tags", [])),
                "summary": result.get("summary", text[:200])
            }
        except Exception as e:
            print(f"AI分析失败，回退到规则分析: {e}")
            return SentimentAnalyzer._analyze_with_rules(text)

    @staticmethod
    def _extract_keywords(text: str) -> list:
        stopwords = {"的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}

        words = re.findall(r'[\w]+', text.lower())
        word_freq = {}
        for word in words:
            if len(word) >= 2 and word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:10]]

    @staticmethod
    def _detect_risk(text: str) -> tuple:
        risk_keywords = {
            "high": ["暴动", "恐怖", "袭击", "战争", "死亡", "自杀", "杀人"],
            "medium": ["诈骗", "欺诈", "虚假", "谣言", "色情", "暴力"],
            "low": ["投诉", "纠纷", "争议", "负面"]
        }

        risk_tags = []
        risk_level = "low"

        for level, keywords in risk_keywords.items():
            for kw in keywords:
                if kw in text:
                    risk_tags.append(kw)
                    if level == "high":
                        risk_level = "high"
                    elif level == "medium" and risk_level != "high":
                        risk_level = "medium"

        return risk_level, list(set(risk_tags))

    @staticmethod
    def calculate_hot_score(text: str, sentiment: str, confidence: float,
                           time_factor: float = 1.0) -> float:
        base_score = 0.0

        text_length = len(text)
        if text_length > 100:
            base_score += 10
        elif text_length > 500:
            base_score += 20

        word_count = len(re.findall(r'[\w]+', text))
        base_score += word_count * 0.1

        if sentiment == "negative":
            base_score *= 1.5
        elif sentiment == "positive":
            base_score *= 1.2

        base_score *= confidence

        base_score *= time_factor

        return min(100, base_score)
