#!/usr/bin/env python
"""
舆情分析和数智大屏模拟数据初始化脚本
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from app.models.sentiment import SentimentAnalysisRepository
from app.models.datav import DataVScreenRepository, DataVLocationRepository, DataVStatsRepository
from app.models.warehouse import ScoutRecordRepository

def print_banner():
    print("=" * 60)
    print("     舆情分析与数智大屏数据初始化")
    print("=" * 60)

def create_sentiment_data():
    """创建模拟舆情分析数据"""
    print("\n[1/3] 创建舆情分析模拟数据...")
    
    # 检查是否已有数据
    existing_count = SentimentAnalysisRepository.get_total_count()
    if existing_count > 0:
        print(f"   已存在 {existing_count} 条数据，跳过创建")
        return

    news_data = [
        {
            "title": "国内AI大模型市场持续火热，多家企业发布新产品",
            "content": "近年来，国内AI大模型市场呈现爆发式增长。据不完全统计，已有超过50家企业发布了自研大模型产品。专家表示，AI技术正在深刻改变各行各业的发展模式，未来前景广阔。",
            "source_type": "news",
            "sentiment": "positive",
            "sentiment_score": 0.85,
            "confidence": 0.92,
            "keywords": "AI,大模型,人工智能,技术创新",
            "risk_level": "low",
            "risk_tags": "",
            "hot_score": 95.5,
            "location_name": "北京"
        },
        {
            "title": "新能源汽车销量突破千万，市场渗透率持续提升",
            "content": "最新数据显示，今年新能源汽车销量已突破千万辆大关，市场渗透率达到28%。政策支持、技术进步和消费者观念转变是推动新能源汽车发展的主要因素。",
            "source_type": "news",
            "sentiment": "positive",
            "sentiment_score": 0.78,
            "confidence": 0.88,
            "keywords": "新能源汽车,销量,渗透率,政策支持",
            "risk_level": "low",
            "risk_tags": "",
            "hot_score": 88.2,
            "location_name": "上海"
        },
        {
            "title": "全球芯片短缺问题持续，产业链面临重构",
            "content": "全球芯片短缺问题已持续两年多，对汽车、消费电子等多个行业造成严重影响。专家呼吁加快芯片产业链自主可控进程，降低对外依赖。",
            "source_type": "news",
            "sentiment": "negative",
            "sentiment_score": 0.22,
            "confidence": 0.90,
            "keywords": "芯片,短缺,产业链,自主可控",
            "risk_level": "high",
            "risk_tags": "供应链风险",
            "hot_score": 92.8,
            "location_name": "深圳"
        },
        {
            "title": "数字经济成为推动经济增长新引擎",
            "content": "数字经济在国民经济中的比重持续提升，已成为推动经济高质量发展的重要引擎。云计算、大数据、人工智能等数字技术正在加速与实体经济深度融合。",
            "source_type": "news",
            "sentiment": "positive",
            "sentiment_score": 0.82,
            "confidence": 0.85,
            "keywords": "数字经济,云计算,大数据,实体经济",
            "risk_level": "low",
            "risk_tags": "",
            "hot_score": 85.6,
            "location_name": "杭州"
        },
        {
            "title": "多地出台房地产新政，市场预期逐步企稳",
            "content": "近期，多地陆续出台房地产调控新政，包括降低首付比例、调整房贷利率等措施。市场人士认为，这些政策有助于稳定市场预期，促进房地产市场平稳健康发展。",
            "source_type": "news",
            "sentiment": "neutral",
            "sentiment_score": 0.52,
            "confidence": 0.78,
            "keywords": "房地产,政策,市场预期,调控",
            "risk_level": "medium",
            "risk_tags": "政策风险",
            "hot_score": 89.3,
            "location_name": "广州"
        },
        {
            "title": "5G商用三年：改变生活，赋能产业",
            "content": "5G商用三年来，已在多个领域得到广泛应用。从智能家居到工业互联网，从远程医疗到自动驾驶，5G技术正在深刻改变人们的生活和生产方式。",
            "source_type": "news",
            "sentiment": "positive",
            "sentiment_score": 0.88,
            "confidence": 0.91,
            "keywords": "5G,商用,工业互联网,数字化",
            "risk_level": "low",
            "risk_tags": "",
            "hot_score": 82.4,
            "location_name": "成都"
        },
        {
            "title": "跨境电商迎来新机遇，政策红利持续释放",
            "content": "随着RCEP生效实施，跨境电商迎来新的发展机遇。政策红利持续释放，为跨境电商企业提供了更加广阔的发展空间。",
            "source_type": "news",
            "sentiment": "positive",
            "sentiment_score": 0.76,
            "confidence": 0.86,
            "keywords": "跨境电商,RCEP,政策红利,出口",
            "risk_level": "low",
            "risk_tags": "",
            "hot_score": 78.9,
            "location_name": "义乌"
        },
        {
            "title": "原材料价格波动加大，企业成本压力上升",
            "content": "受国际形势影响，原材料价格波动明显加大，给企业带来较大成本压力。不少企业表示正在积极采取措施应对，包括优化供应链、加强成本控制等。",
            "source_type": "news",
            "sentiment": "negative",
            "sentiment_score": 0.35,
            "confidence": 0.87,
            "keywords": "原材料,价格波动,成本压力,供应链",
            "risk_level": "medium",
            "risk_tags": "成本风险",
            "hot_score": 84.1,
            "location_name": "苏州"
        },
        {
            "title": "人工智能伦理问题引发关注，行业呼吁加强规范",
            "content": "随着人工智能技术的快速发展，伦理问题日益受到关注。专家呼吁加强AI伦理规范，确保AI技术健康、安全、负责任地发展。",
            "source_type": "news",
            "sentiment": "neutral",
            "sentiment_score": 0.55,
            "confidence": 0.82,
            "keywords": "人工智能,伦理,规范,安全",
            "risk_level": "medium",
            "risk_tags": "合规风险",
            "hot_score": 76.7,
            "location_name": "南京"
        },
        {
            "title": "元宇宙概念降温，行业回归理性发展",
            "content": "经历了前期的火热炒作后，元宇宙概念逐渐降温，行业开始回归理性发展。业内人士认为，元宇宙技术仍处于早期阶段，需要更多的技术积累和应用探索。",
            "source_type": "news",
            "sentiment": "neutral",
            "sentiment_score": 0.48,
            "confidence": 0.80,
            "keywords": "元宇宙,虚拟现实,技术发展,理性",
            "risk_level": "medium",
            "risk_tags": "市场风险",
            "hot_score": 72.3,
            "location_name": "武汉"
        }
    ]

    count = 0
    for i, data in enumerate(news_data):
        # 创建不同时间的记录，模拟最近7天的数据
        publish_time = (datetime.now() - timedelta(days=i % 7)).strftime("%Y-%m-%d %H:%M:%S")
        
        record_id = SentimentAnalysisRepository.create(
            source_type=data["source_type"],
            title=data["title"],
            content=data["content"],
            sentiment=data["sentiment"],
            sentiment_score=data["sentiment_score"],
            confidence=data["confidence"],
            keywords=data["keywords"],
            risk_level=data["risk_level"],
            risk_tags=data["risk_tags"],
            hot_score=data["hot_score"],
            location_name=data["location_name"],
            publish_time=publish_time
        )
        
        if record_id:
            count += 1
            print(f"   ✓ 创建舆情记录 {i+1}: {data['title'][:30]}...")

    print(f"\n   成功创建 {count} 条舆情分析数据")

def create_datav_screens():
    """创建数智大屏配置"""
    print("\n[2/3] 创建数智大屏配置...")
    
    existing_count = DataVScreenRepository.get_total_count()
    if existing_count > 0:
        print(f"   已存在 {existing_count} 个大屏配置，跳过创建")
        return

    screens = [
        {
            "name": "数智舆情监测平台",
            "description": "实时舆情监控大屏，展示情感分布、风险趋势等数据",
            "config": json.dumps({
                "widgets": [
                    {"type": "sentiment_dist", "x": 0, "y": 0, "width": 2, "height": 2},
                    {"type": "risk_dist", "x": 2, "y": 0, "width": 2, "height": 2},
                    {"type": "source_dist", "x": 4, "y": 0, "width": 2, "height": 2},
                    {"type": "sentiment_trend", "x": 0, "y": 2, "width": 4, "height": 2},
                    {"type": "hotwords", "x": 4, "y": 2, "width": 2, "height": 2},
                    {"type": "geo_map", "x": 0, "y": 4, "width": 4, "height": 2},
                    {"type": "news_list", "x": 4, "y": 4, "width": 2, "height": 2}
                ]
            }),
            "refresh_interval": 30
        },
        {
            "name": "数据总览大屏",
            "description": "综合数据展示大屏，包含采集、分析、存储等核心指标",
            "config": json.dumps({
                "widgets": [
                    {"type": "overview_stats", "x": 0, "y": 0, "width": 4, "height": 2},
                    {"type": "timeline", "x": 0, "y": 2, "width": 6, "height": 2},
                    {"type": "top_sources", "x": 0, "y": 4, "width": 3, "height": 2},
                    {"type": "recent_records", "x": 3, "y": 4, "width": 3, "height": 2}
                ]
            }),
            "refresh_interval": 60
        }
    ]

    count = 0
    for screen in screens:
        screen_id = DataVScreenRepository.create(**screen)
        if screen_id:
            count += 1
            print(f"   ✓ 创建大屏: {screen['name']}")

    print(f"\n   成功创建 {count} 个大屏配置")

def create_location_data():
    """创建位置数据"""
    print("\n[3/3] 创建位置数据...")
    
    locations = [
        {"name": "北京", "lat": 39.9042, "lng": 116.4074},
        {"name": "上海", "lat": 31.2304, "lng": 121.4737},
        {"name": "广州", "lat": 23.1291, "lng": 113.2644},
        {"name": "深圳", "lat": 22.5431, "lng": 114.0579},
        {"name": "杭州", "lat": 30.2741, "lng": 120.1552},
        {"name": "成都", "lat": 30.5728, "lng": 104.0668},
        {"name": "武汉", "lat": 30.5928, "lng": 114.3055},
        {"name": "南京", "lat": 32.0603, "lng": 118.7969},
        {"name": "苏州", "lat": 31.3251, "lng": 120.6196},
        {"name": "义乌", "lat": 29.3013, "lng": 120.0659}
    ]

    count = 0
    for loc in locations:
        loc_id = DataVLocationRepository.create(
            latitude=loc["lat"],
            longitude=loc["lng"],
            location_name=loc["name"],
            location_type="city"
        )
        if loc_id:
            count += 1

    print(f"   成功创建 {count} 个位置数据")

def main():
    print_banner()
    create_sentiment_data()
    create_datav_screens()
    create_location_data()
    
    print("\n" + "=" * 60)
    print("数据初始化完成！")
    print("=" * 60)
    print("\n现在您可以：")
    print("1. 访问智能舆情分析页面查看数据")
    print("2. 访问数智大屏页面查看可视化效果")

if __name__ == "__main__":
    main()