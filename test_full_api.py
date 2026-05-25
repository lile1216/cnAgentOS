#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
sys.path.insert(0, 'd:/aiAgentOS-main')

from app.models.sentiment import SentimentAnalysisRepository
from app.models.datav import DataVCacheRepository
from datetime import datetime, timedelta

print('=== 完整API流程测试 ===')

start_time = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
cache_key = "sentiment:stats:all:all"

# 步骤1: 检查缓存
print("\n1. 检查缓存:")
start = time.time()
cached = DataVCacheRepository.get(cache_key)
elapsed = time.time() - start
print(f"   耗时: {elapsed*1000:.2f}ms, 结果: {cached is not None}")

# 步骤2: 获取统计数据
print("\n2. 获取统计数据:")
start = time.time()
stats = SentimentAnalysisRepository.get_sentiment_stats(start_time, end_time)
elapsed = time.time() - start
print(f"   耗时: {elapsed*1000:.2f}ms")

# 步骤3: 获取时间线
print("\n3. 获取时间线:")
start = time.time()
timeline = SentimentAnalysisRepository.get_time_series("day", 30, start_time, end_time)
elapsed = time.time() - start
print(f"   耗时: {elapsed*1000:.2f}ms")

# 步骤4: 获取热词
print("\n4. 获取热词:")
start = time.time()
hotwords = SentimentAnalysisRepository.get_hot_keywords(20, start_time, end_time)
elapsed = time.time() - start
print(f"   耗时: {elapsed*1000:.2f}ms")

# 步骤5: 设置缓存
print("\n5. 设置缓存:")
result = {"stats": stats, "timeline": timeline, "hotwords": hotwords}
start = time.time()
DataVCacheRepository.set(cache_key, result, 60)
elapsed = time.time() - start
print(f"   耗时: {elapsed*1000:.2f}ms")

print('\n=== 测试完成 ===')