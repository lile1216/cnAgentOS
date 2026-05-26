import sqlite3
import random
import re

from app.models.db import get_connection


class DigitalEmployeeRepository:
    @staticmethod
    def get_all(page: int = 1, page_size: int = 20):
        offset = (page - 1) * page_size
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM digital_employee ORDER BY sort_order ASC LIMIT ? OFFSET ?",
                (page_size, offset)
            ).fetchall()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_all_employees():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM digital_employee ORDER BY sort_order ASC").fetchall()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_total_count():
        with get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM digital_employee").fetchone()
        return row["count"] if row else 0
    
    @staticmethod
    def get_enabled_employees():
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM digital_employee WHERE enabled = 1 ORDER BY sort_order ASC").fetchall()
        return [dict(row) for row in rows]
    
    @staticmethod
    def get_employee_by_id(employee_id):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM digital_employee WHERE id = ?", (employee_id,)).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def get_employee_by_name(name):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM digital_employee WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def create_employee(name, alias, category='AI', description='', prompt='', model_id=None, api_interface_id=None, avatar='🤖', welcome_msg='', enabled=1):
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO digital_employee(name, alias, category, description, prompt, model_id, api_interface_id, avatar, welcome_msg, enabled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, alias, category, description, prompt, model_id, api_interface_id, avatar, welcome_msg, enabled)
            )
            conn.commit()
        return cursor.lastrowid
    
    @staticmethod
    def update_employee(employee_id, name=None, alias=None, category=None, description=None, prompt=None, model_id=None, api_interface_id=None, avatar=None, welcome_msg=None, enabled=None):
        with get_connection() as conn:
            update_fields = []
            params = []
            
            if name:
                update_fields.append("name = ?")
                params.append(name)
            if alias:
                update_fields.append("alias = ?")
                params.append(alias)
            if category:
                update_fields.append("category = ?")
                params.append(category)
            if description:
                update_fields.append("description = ?")
                params.append(description)
            if prompt:
                update_fields.append("prompt = ?")
                params.append(prompt)
            if model_id is not None:
                update_fields.append("model_id = ?")
                params.append(model_id)
            if api_interface_id is not None:
                update_fields.append("api_interface_id = ?")
                params.append(api_interface_id)
            if avatar:
                update_fields.append("avatar = ?")
                params.append(avatar)
            if welcome_msg:
                update_fields.append("welcome_msg = ?")
                params.append(welcome_msg)
            if enabled is not None:
                update_fields.append("enabled = ?")
                params.append(enabled)
            
            if update_fields:
                params.append(employee_id)
                update_sql = f"UPDATE digital_employee SET {','.join(update_fields)} WHERE id = ?"
                conn.execute(update_sql, params)
                conn.commit()
    
    @staticmethod
    def delete_employee(employee_id):
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM digital_employee WHERE id = ?", (employee_id,))
            conn.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def get_by_alias(alias):
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM digital_employee WHERE alias = ?", (alias,)).fetchone()
        return dict(row) if row else None
    
    @staticmethod
    def create(name, alias, category='AI', description='', prompt='', model_id=None, api_interface_id=None, avatar='🤖', welcome_msg='', enabled=1):
        try:
            with get_connection() as conn:
                cursor = conn.execute(
                    "INSERT INTO digital_employee(name, alias, category, description, prompt, model_id, api_interface_id, avatar, welcome_msg, enabled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, alias, category, description, prompt, model_id, api_interface_id, avatar, welcome_msg, enabled)
                )
                conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None
    
    @staticmethod
    def update(employee_id, **kwargs):
        with get_connection() as conn:
            update_fields = []
            params = []
            
            if "name" in kwargs:
                update_fields.append("name = ?")
                params.append(kwargs["name"])
            if "alias" in kwargs:
                update_fields.append("alias = ?")
                params.append(kwargs["alias"])
            if "category" in kwargs:
                update_fields.append("category = ?")
                params.append(kwargs["category"])
            if "description" in kwargs:
                update_fields.append("description = ?")
                params.append(kwargs["description"])
            if "prompt" in kwargs:
                update_fields.append("prompt = ?")
                params.append(kwargs["prompt"])
            if "model_id" in kwargs:
                update_fields.append("model_id = ?")
                params.append(kwargs["model_id"])
            if "api_interface_id" in kwargs:
                update_fields.append("api_interface_id = ?")
                params.append(kwargs["api_interface_id"])
            if "avatar" in kwargs:
                update_fields.append("avatar = ?")
                params.append(kwargs["avatar"])
            if "welcome_msg" in kwargs:
                update_fields.append("welcome_msg = ?")
                params.append(kwargs["welcome_msg"])
            if "enabled" in kwargs:
                update_fields.append("enabled = ?")
                params.append(kwargs["enabled"])
            
            if update_fields:
                try:
                    params.append(employee_id)
                    update_sql = f"UPDATE digital_employee SET {','.join(update_fields)} WHERE id = ?"
                    conn.execute(update_sql, params)
                    conn.commit()
                    return True
                except sqlite3.IntegrityError:
                    return False
            return False
    
    @staticmethod
    def delete(employee_id):
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM digital_employee WHERE id = ?", (employee_id,))
            conn.commit()
        return cursor.rowcount > 0
    
    @staticmethod
    def batch_delete(ids):
        with get_connection() as conn:
            placeholders = ",".join("?" * len(ids))
            cursor = conn.execute(f"DELETE FROM digital_employee WHERE id IN ({placeholders})", ids)
            conn.commit()
        return cursor.rowcount
    
    @staticmethod
    def toggle_status(employee_id):
        with get_connection() as conn:
            row = conn.execute("SELECT enabled FROM digital_employee WHERE id = ?", (employee_id,)).fetchone()
            if row:
                new_status = 0 if row["enabled"] else 1
                conn.execute("UPDATE digital_employee SET enabled = ? WHERE id = ?", (new_status, employee_id))
                conn.commit()
                return True
        return False


class DigitalEmployeeManager:
    _employees = {}
    
    @staticmethod
    def register(name: str, employee):
        DigitalEmployeeManager._employees[name] = employee
    
    @staticmethod
    def get_employee(name: str):
        return DigitalEmployeeManager._employees.get(name)
    
    @staticmethod
    def list_employees():
        return list(DigitalEmployeeManager._employees.keys())


class SichuanAgriculturalAssistant:
    """川农小助手：负责关于川农的限定范围问题聊天"""
    
    def __init__(self):
        self.name = "川农小助手"
        self.avatar = "🌾"
        
        self.knowledge_base = {
            "学校名称": "四川农业大学（Sichuan Agricultural University）",
            "学校简称": "川农",
            "建校时间": "1906年",
            "办学性质": "国家双一流建设高校、国家211工程重点建设大学",
            "校训": "追求真理、造福社会、自强不息",
            "校区": "雅安校区、成都校区、都江堰校区",
            "知名校友": "周开达、荣廷昭、陈焕春、李宁等院士",
            "王牌专业": "作物学、畜牧学、兽医学、农林经济管理",
            "占地面积": "约4500亩",
            "在校学生": "约4.4万人",
            "教师队伍": "约3000人，其中院士6人",
            "科研平台": "国家级科研平台8个，省部级科研平台40余个",
            "校歌": "《川农之歌》",
            "吉祥物": "麦麦",
        }
        
        self.greetings = [
            "您好！我是川农小助手，很高兴为您服务！",
            "你好呀！有什么关于川农的问题想问我吗？",
            "嗨！欢迎咨询四川农业大学相关问题~",
        ]
        
        self.farewells = [
            "感谢您的咨询，祝您生活愉快！",
            "再见！欢迎下次再来咨询~",
            "拜拜~ 有问题随时找我！",
        ]
    
    def respond(self, message: str, context: dict = None) -> str:
        message = message.strip()
        
        if re.search(r'你好|您好|Hi|hello|嗨', message, re.IGNORECASE):
            return random.choice(self.greetings)
        
        if re.search(r'再见|拜拜|再见了|结束', message, re.IGNORECASE):
            return random.choice(self.farewells)
        
        for keyword, answer in self.knowledge_base.items():
            if keyword in message or keyword[:2] in message:
                return f"{keyword}：{answer}"
        
        keywords = ["历史", "多少年", "多久", "成立"]
        if any(k in message for k in keywords):
            return f"四川农业大学始建于1906年，至今已有百年历史。{self.knowledge_base['办学性质']}。"
        
        keywords = ["专业", "学科", "王牌", "优势"]
        if any(k in message for k in keywords):
            return f"川农的王牌专业包括：{self.knowledge_base['王牌专业']}。这些专业在国内都处于领先水平。"
        
        keywords = ["校区", "在哪里", "位置", "地址"]
        if any(k in message for k in keywords):
            return f"四川农业大学有三个校区：{self.knowledge_base['校区']}。校本部位于雅安市。"
        
        keywords = ["学生", "人数", "规模", "多少人"]
        if any(k in message for k in keywords):
            return f"学校现有{self.knowledge_base['在校学生']}，{self.knowledge_base['教师队伍']}。"
        
        keywords = ["科研", "研究", "平台", "实验室"]
        if any(k in message for k in keywords):
            return f"学校拥有{self.knowledge_base['科研平台']}，科研实力雄厚。"
        
        keywords = ["校训", "校歌", "精神", "文化"]
        if any(k in message for k in keywords):
            return f"川农的校训是：{self.knowledge_base['校训']}。校歌为《川农之歌》。"
        
        return "抱歉，我只了解四川农业大学相关的信息。请问您有什么关于川农的问题吗？"


class WeatherAssistant:
    """天气小助手：输入城市名，返回指定城市天气卡片"""
    
    def __init__(self):
        self.name = "天气小助手"
        self.avatar = "☀️"
        
        self.weather_data = {
            "北京": {"temperature": "26°C", "condition": "晴", "wind": "东北风3级", "humidity": "45%", "icon": "☀️"},
            "上海": {"temperature": "28°C", "condition": "多云", "wind": "东南风2级", "humidity": "65%", "icon": "⛅"},
            "广州": {"temperature": "32°C", "condition": "雷阵雨", "wind": "南风4级", "humidity": "85%", "icon": "⛈️"},
            "深圳": {"temperature": "30°C", "condition": "多云转晴", "wind": "东风2级", "humidity": "70%", "icon": "🌤️"},
            "成都": {"temperature": "24°C", "condition": "阴", "wind": "北风1级", "humidity": "80%", "icon": "☁️"},
            "杭州": {"temperature": "27°C", "condition": "小雨", "wind": "西北风3级", "humidity": "90%", "icon": "🌧️"},
            "武汉": {"temperature": "25°C", "condition": "晴转多云", "wind": "西南风2级", "humidity": "55%", "icon": "🌥️"},
            "南京": {"temperature": "26°C", "condition": "多云", "wind": "东北风3级", "humidity": "60%", "icon": "⛅"},
            "西安": {"temperature": "22°C", "condition": "晴", "wind": "东风2级", "humidity": "40%", "icon": "☀️"},
            "重庆": {"temperature": "29°C", "condition": "小雨", "wind": "南风2级", "humidity": "85%", "icon": "🌧️"},
            "天津": {"temperature": "25°C", "condition": "晴", "wind": "西北风4级", "humidity": "50%", "icon": "☀️"},
            "苏州": {"temperature": "27°C", "condition": "多云", "wind": "东南风2级", "humidity": "75%", "icon": "⛅"},
            "郑州": {"temperature": "28°C", "condition": "晴", "wind": "东北风3级", "humidity": "45%", "icon": "☀️"},
            "长沙": {"temperature": "28°C", "condition": "阵雨", "wind": "南风3级", "humidity": "80%", "icon": "🌦️"},
            "青岛": {"temperature": "22°C", "condition": "晴", "wind": "海风4级", "humidity": "60%", "icon": "☀️"},
        }
        
        self.default_weather = {"temperature": "25°C", "condition": "晴", "wind": "微风", "humidity": "50%", "icon": "☀️"}
    
    def respond(self, message: str, context: dict = None) -> str:
        message = message.strip()
        
        city = self._extract_city(message)
        
        if not city:
            return "请告诉我您想查询哪个城市的天气？例如：北京天气怎么样？"
        
        weather = self.weather_data.get(city, self.default_weather)
        
        return f"""
{weather['icon']} **{city}天气**
🌡️ 温度：{weather['temperature']}
☁️ 天气：{weather['condition']}
💨 风向：{weather['wind']}
💧 湿度：{weather['humidity']}
        """.strip()
    
    def _extract_city(self, message: str) -> str:
        cities = list(self.weather_data.keys())
        for city in cities:
            if city in message:
                return city
        return ""
    
    def get_weather_style(self, city: str) -> dict:
        weather = self.weather_data.get(city, self.default_weather)
        condition = weather["condition"]
        
        styles = {
            "晴": {"bg_gradient": "linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%)", "animation": "sunny"},
            "多云": {"bg_gradient": "linear-gradient(135deg, #e0e5ec 0%, #a8c0d7 100%)", "animation": "cloudy"},
            "阴": {"bg_gradient": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "animation": "cloudy"},
            "小雨": {"bg_gradient": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)", "animation": "rainy"},
            "雷阵雨": {"bg_gradient": "linear-gradient(135deg, #434343 0%, #000000 100%)", "animation": "thunder"},
            "阵雨": {"bg_gradient": "linear-gradient(135deg, #74b9ff 0%, #0984e3 100%)", "animation": "rainy"},
            "晴转多云": {"bg_gradient": "linear-gradient(135deg, #ffecd2 0%, #a8c0d7 100%)", "animation": "sunny-cloudy"},
            "多云转晴": {"bg_gradient": "linear-gradient(135deg, #a8c0d7 0%, #ffecd2 100%)", "animation": "cloudy-sunny"},
        }
        
        return styles.get(condition, styles["晴"])


class PoisonChickenSoupAssistant:
    """毒鸡汤助手：随机回复毒鸡汤语句"""
    
    def __init__(self):
        self.name = "毒鸡汤助手"
        self.avatar = "💀"
        
        self.soups = [
            "你努力不一定会成功，但不努力会很舒服。",
            "生活不止眼前的苟且，还有长远的凑合。",
            "比你优秀的人还在努力，那你努力还有什么用？",
            "条条大路通罗马，可有的人就生在罗马。",
            "失败是成功之母，但成功之父是谁呢？谁都不知道。",
            "你以为的极限，可能只是别人的起点。",
            "世界上最遥远的距离不是生与死，而是我在努力，你却在睡觉，结果还比我成功。",
            "不要抱怨生活，因为生活根本不知道你是谁。",
            "你全力做到的最好，可能还不如别人随便搞搞。",
            "努力了这么久，但凡有点天赋也该有点成功迹象了。",
            "如果你觉得自己整天累得像狗一样，那你真是误会大了，狗都没你这么累。",
            "有些人出现在你的生命里，就是为了告诉你：你真好骗。",
            "生活嘛，就是生下来，活下去，其他的都是浮云。",
            "你连几点睡都控制不了，还想控制人生？",
            "当你觉得自己又丑又穷，一无是处时，别绝望，因为至少你的判断是对的。",
            "梦想还是要有的，万一实现了呢？不过实现的概率和中彩票差不多。",
            "别人都在假装正经，我只好假装不正经。",
            "人生没有彩排，每天都是现场直播，而且收视率极低。",
            "长得好看的才能叫吃货，长得丑的只能叫饭桶。",
            "所谓的一见钟情，不过是见色起意；所谓的日久生情，不过是权衡利弊。",
            "钱不是万能的，但没钱是万万不能的，这就是现实。",
            "你可以像猪一样懒，但无法像猪一样懒得心安理得。",
            "有时候你不努力一下，都不知道什么叫绝望。",
            "成功的路上并不拥挤，因为坚持的人太少了，而你就是那个放弃的人。",
            "别担心，你永远都有比你更惨的人。",
        ]
    
    def respond(self, message: str, context: dict = None) -> str:
        return random.choice(self.soups)


DigitalEmployeeManager.register("川农小助手", SichuanAgriculturalAssistant())
DigitalEmployeeManager.register("天气小助手", WeatherAssistant())
DigitalEmployeeManager.register("毒鸡汤助手", PoisonChickenSoupAssistant())
