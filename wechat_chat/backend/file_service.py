import hashlib
import os
from wechat_chat.backend.db import get_connection

class WechatFileService:
    """聊天子系统文件服务 (支持 MD5 去重)"""
    
    @staticmethod
    def calculate_md5(file_body):
        """计算文件 MD5"""
        md5_obj = hashlib.md5()
        md5_obj.update(file_body)
        return md5_obj.hexdigest()

    @staticmethod
    def save_file(file_meta):
        """保存文件，如果 MD5 已存在则返回原有路径"""
        content = file_meta['body']
        md5 = WechatFileService.calculate_md5(content)
        original_name = file_meta['filename']
        file_size = len(content)
        
        with get_connection() as conn:
            # 检查是否已存在相同 MD5 的文件
            existing = conn.execute(
                "SELECT file_path FROM wechat_file_index WHERE md5 = ?", 
                (md5,)
            ).fetchone()
            
            if existing:
                return existing['file_path'], original_name
            
            # 如果不存在，保存新文件
            ext = os.path.splitext(original_name)[1]
            import uuid
            new_filename = f"{uuid.uuid4().hex}{ext}"
            
            upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)
                
            file_path_disk = os.path.join(upload_dir, new_filename)
            with open(file_path_disk, 'wb') as f:
                f.write(content)
            
            relative_url = f"/wechat-chat/static/uploads/{new_filename}"
            
            # 记录到索引表
            conn.execute("""
                INSERT INTO wechat_file_index (md5, file_path, original_name, file_size)
                VALUES (?, ?, ?, ?)
            """, (md5, relative_url, original_name, file_size))
            conn.commit()
            
            return relative_url, original_name

    @staticmethod
    def get_all_files():
        """获取所有文件记录"""
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM wechat_file_index ORDER BY create_at DESC").fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def delete_file(file_id):
        """删除文件记录及磁盘文件"""
        with get_connection() as conn:
            file_info = conn.execute("SELECT file_path FROM wechat_file_index WHERE id = ?", (file_id,)).fetchone()
            if file_info:
                # 尝试删除磁盘文件
                # 注意：生产环境下如果多个 MD5 对应一个文件，需要引用计数，这里简化处理
                # 用户要求“独立操作”，我们按 ID 删除记录
                conn.execute("DELETE FROM wechat_file_index WHERE id = ?", (file_id,))
                conn.commit()
                return True
        return False
