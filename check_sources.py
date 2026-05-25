#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, 'd:/aiAgentOS-main')
from app.models.scout_source import ScoutSourceRepository

sources = ScoutSourceRepository.get_all()
print('数据源列表:')
for s in sources:
    enabled = '启用' if s['enabled'] == 1 else '禁用'
    print(f"ID: {s['id']}, 名称: {s['name']}, 启用状态: {enabled}")

# 如果数据源太少，添加一些
if len(sources) < 3:
    print('\n添加更多数据源...')
    
    ScoutSourceRepository.create(
        name='百度新闻搜索',
        url_pattern='https://news.baidu.com/search?word={关键字}',
        request_method='GET',
        headers='User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        enabled=True
    )
    
    ScoutSourceRepository.create(
        name='新浪新闻搜索', 
        url_pattern='https://search.sina.com.cn/?q={关键字}&c=news',
        request_method='GET',
        headers='User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        enabled=True
    )
    
    ScoutSourceRepository.create(
        name='网易新闻搜索',
        url_pattern='https://news.163.com/search?keyword={关键字}',
        request_method='GET',
        headers='User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        enabled=True
    )
    
    ScoutSourceRepository.create(
        name='搜狐新闻搜索',
        url_pattern='https://sohu.com/a/search?q={关键字}',
        request_method='GET',
        headers='User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        enabled=True
    )
    
    print('数据源添加完成!')
