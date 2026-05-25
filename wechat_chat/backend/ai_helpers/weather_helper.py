class WeatherHelper:
    """天气小助手：根据城市返回天气和特效指令"""
    
    @staticmethod
    def get_response(city_name):
        # 这里模拟一个天气接口返回，实际可对接高德/心知天气等 API
        # 为了演示动态效果，我们根据城市名包含的字来模拟不同天气
        weather_type = "sunny"
        temp = "25℃"
        desc = "晴空万里"
        
        if "雨" in city_name or "上海" in city_name:
            weather_type = "rainy"
            temp = "18℃"
            desc = "中雨，记得带伞"
        elif "雪" in city_name or "哈尔滨" in city_name:
            weather_type = "snowy"
            temp = "-5℃"
            desc = "大雪纷飞"
            
        return {
            "text": f"【{city_name}】当前天气：{desc}，温度：{temp}。",
            "weather_type": weather_type,
            "city": city_name
        }
