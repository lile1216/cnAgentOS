#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
sys.path.insert(0, 'd:/aiAgentOS-main')
from app.models.db import get_connection

print('=== 检查缓存表 ===')

with get_connection() as conn:
    cursor = conn.execute("SELECT COUNT(*) as cnt FROM datav_cache")
    row = cursor.fetchone()
    print(f"缓存表记录数: {row['cnt']}")
    
    if row['cnt'] > 0:
        cursor = conn.execute("SELECT * FROM datav_cache LIMIT 5")
        rows = cursor.fetchall()
        print("\n缓存记录示例:")
        for row in rows:
            print(f"  Key: {row['cache_key'][:50]}..., Expire: {row['expire_at']}")
    
    # 测试缓存查询性能
    start = time.time()
    cursor = conn.execute("SELECT * FROM datav_cache WHERE cache_key = 'test_key'")
    cursor.fetchone()
    elapsed = time.time() - start
    print(f"\n缓存查询时间: {elapsed*1000:.2f}ms")

print('\n=== 检查完成 ===')