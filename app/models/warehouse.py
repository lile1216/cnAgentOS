import sqlite3
import json
from app.models.db import get_connection

class ScoutRecordRepository:
    """采集记录仓库"""
    
    @staticmethod
    def create(source_id: int, source_name: str, url: str, keyword: str = None,
               title: str = None, summary: str = None, raw_content: str = None,
               status: str = "pending") -> int:
        """创建采集记录"""
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO scout_record(source_id, source_name, keyword, url, title, summary, raw_content, status) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (source_id, source_name, keyword, url, title, summary, raw_content, status)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_all(page: int = 1, page_size: int = 20, source_id: int = None, keyword: str = None, ai_analyzed: int = None):
        """获取所有采集记录"""
        offset = (page - 1) * page_size
        where_clauses = []
        params = []
        
        if source_id:
            where_clauses.append("source_id = ?")
            params.append(source_id)
        if keyword:
            where_clauses.append("(title LIKE ? OR summary LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if ai_analyzed is not None:
            where_clauses.append("ai_analyzed = ?")
            params.append(ai_analyzed)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM scout_record WHERE {where_sql} ORDER BY create_at DESC LIMIT ? OFFSET ?",
                (*params, page_size, offset)
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_total_count(source_id: int = None, keyword: str = None, ai_analyzed: int = None):
        """获取总记录数"""
        where_clauses = []
        params = []
        
        if source_id:
            where_clauses.append("source_id = ?")
            params.append(source_id)
        if keyword:
            where_clauses.append("(title LIKE ? OR summary LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        if ai_analyzed is not None:
            where_clauses.append("ai_analyzed = ?")
            params.append(ai_analyzed)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        with get_connection() as conn:
            row = conn.execute(f"SELECT COUNT(*) as total FROM scout_record WHERE {where_sql}", tuple(params)).fetchone()
        return row["total"] if row else 0

    @staticmethod
    def get_by_id(id: int):
        """根据ID获取记录"""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM scout_record WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def update(id: int, **kwargs):
        """更新记录"""
        update_fields = []
        params = []
        
        allowed_fields = ['title', 'summary', 'raw_content', 'status', 'ai_analyzed', 'ai_analyze_status', 'ai_analyze_msg', 'ai_analyze_time']
        
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                update_fields.append(f"{key} = ?")
                params.append(value)
        
        if not update_fields:
            return False
        
        update_fields.append("update_at = datetime('now')")
        params.append(id)
        
        with get_connection() as conn:
            conn.execute(f"UPDATE scout_record SET {','.join(update_fields)} WHERE id = ?", params)
            conn.commit()
        return True

    @staticmethod
    def delete(id: int) -> bool:
        """删除记录"""
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM scout_record WHERE id = ?", (id,))
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def batch_delete(ids: list) -> int:
        """批量删除记录"""
        if not ids:
            return 0
        
        placeholders = ",".join("?" * len(ids))
        with get_connection() as conn:
            cursor = conn.execute(f"DELETE FROM scout_record WHERE id IN ({placeholders})", tuple(ids))
            conn.commit()
        return cursor.rowcount

    @staticmethod
    def get_by_source(source_id: int, page: int = 1, page_size: int = 20):
        """根据数据源获取记录"""
        return ScoutRecordRepository.get_all(page, page_size, source_id=source_id)

    @staticmethod
    def get_unanalyzed(page: int = 1, page_size: int = 20):
        """获取未分析的记录"""
        return ScoutRecordRepository.get_all(page, page_size, ai_analyzed=0)

    @staticmethod
    def get_unanalyzed_count():
        """获取未分析记录数"""
        return ScoutRecordRepository.get_total_count(ai_analyzed=0)


class ScoutDetailRepository:
    """采集明细仓库"""
    
    @staticmethod
    def create(record_id: int, source_id: int, title: str = None, content: str = None,
               author: str = None, publish_time: str = None, source_url: str = None,
               tags: str = None, categories: str = None, images: str = None,
               ai_summary: str = None, ai_keywords: str = None,
               ai_sentiment: str = None, ai_entities: str = None) -> int:
        """创建采集明细"""
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO scout_detail(record_id, source_id, title, content, author, publish_time, 
                   source_url, tags, categories, images, ai_summary, ai_keywords, ai_sentiment, ai_entities) 
                   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (record_id, source_id, title, content, author, publish_time, source_url,
                 tags, categories, images, ai_summary, ai_keywords, ai_sentiment, ai_entities)
            )
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_all(page: int = 1, page_size: int = 20, record_id: int = None, source_id: int = None):
        """获取所有采集明细"""
        offset = (page - 1) * page_size
        where_clauses = []
        params = []
        
        if record_id:
            where_clauses.append("record_id = ?")
            params.append(record_id)
        if source_id:
            where_clauses.append("source_id = ?")
            params.append(source_id)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        with get_connection() as conn:
            rows = conn.execute(
                f"SELECT * FROM scout_detail WHERE {where_sql} ORDER BY create_at DESC LIMIT ? OFFSET ?",
                (*params, page_size, offset)
            ).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def get_total_count(record_id: int = None, source_id: int = None):
        """获取总记录数"""
        where_clauses = []
        params = []
        
        if record_id:
            where_clauses.append("record_id = ?")
            params.append(record_id)
        if source_id:
            where_clauses.append("source_id = ?")
            params.append(source_id)
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        with get_connection() as conn:
            row = conn.execute(f"SELECT COUNT(*) as total FROM scout_detail WHERE {where_sql}", tuple(params)).fetchone()
        return row["total"] if row else 0

    @staticmethod
    def get_by_id(id: int):
        """根据ID获取明细"""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM scout_detail WHERE id = ?", (id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def get_by_record_id(record_id: int):
        """根据记录ID获取明细"""
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM scout_detail WHERE record_id = ?", (record_id,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def update(id: int, **kwargs):
        """更新明细"""
        update_fields = []
        params = []
        
        allowed_fields = ['title', 'content', 'author', 'publish_time', 'source_url',
                         'tags', 'categories', 'images', 'ai_summary', 'ai_keywords',
                         'ai_sentiment', 'ai_entities']
        
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                update_fields.append(f"{key} = ?")
                params.append(value)
        
        if not update_fields:
            return False
        
        update_fields.append("update_at = datetime('now')")
        params.append(id)
        
        with get_connection() as conn:
            conn.execute(f"UPDATE scout_detail SET {','.join(update_fields)} WHERE id = ?", params)
            conn.commit()
        return True

    @staticmethod
    def delete(id: int) -> bool:
        """删除明细"""
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM scout_detail WHERE id = ?", (id,))
            conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def delete_by_record_id(record_id: int) -> int:
        """根据记录ID删除明细"""
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM scout_detail WHERE record_id = ?", (record_id,))
            conn.commit()
        return cursor.rowcount
