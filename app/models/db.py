import os
import sqlite3

def _project_root():
	return os.path.abspath(os.path.join(os.path.dirname(__file__),os.pardir,os.pardir))

DB_PATH = os.path.join(_project_root(),"database","app.db")

def get_connection():
	os.makedirs(os.path.dirname(DB_PATH),exist_ok=True)
	conn = sqlite3.connect(DB_PATH)
	conn.row_factory = sqlite3.Row
	return conn


def init_db():
	with get_connection() as conn:
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS user(
				id integer PRIMARY KEY AUTOINCREMENT,
				username TEXT NOT NULL UNIQUE,
				password_hash TEXT NOT NULL,
				salt TEXT NOT NULL,
				role TEXT NOT NULL DEFAULT('user'),
				create_at TEXT NOT NULL DEFAULT(datetime('now'))
				
			)
			"""
		)
		# 如果表已存在，添加role字段（如果不存在）
		try:
			conn.execute("ALTER TABLE user ADD COLUMN role TEXT NOT NULL DEFAULT('user')")
			conn.commit()
		except sqlite3.OperationalError:
			pass  # 字段已存在
		
		# 创建模型服务表
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS model_service(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL UNIQUE,
				model TEXT NOT NULL,
				api_key TEXT NOT NULL,
				base_url TEXT NOT NULL,
				max_tokens INTEGER DEFAULT 4096,
				temperature REAL DEFAULT 0.7,
				is_default INTEGER DEFAULT 0,
				token_usage INTEGER DEFAULT 0,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS scout_source(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL UNIQUE,
				url_pattern TEXT NOT NULL,
				request_method TEXT DEFAULT 'GET',
				headers TEXT,
				enabled INTEGER DEFAULT 1,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS api_interface(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				url TEXT NOT NULL,
				method TEXT DEFAULT 'GET',
				response_format TEXT DEFAULT 'JSON',
				example TEXT,
				qps_limit TEXT,
				token_required INTEGER DEFAULT 0,
				remark TEXT,
				enabled INTEGER DEFAULT 1,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS digital_employee(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				alias TEXT NOT NULL UNIQUE,
				category TEXT NOT NULL DEFAULT 'AI',
				description TEXT,
				prompt TEXT,
				model_id INTEGER,
				api_interface_id INTEGER,
				avatar TEXT,
				welcome_msg TEXT,
				enabled INTEGER DEFAULT 1,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS scout_record(
				id integer PRIMARY KEY AUTOINCREMENT,
				source_id INTEGER NOT NULL,
				source_name TEXT NOT NULL,
				keyword TEXT,
				url TEXT NOT NULL,
				title TEXT,
				summary TEXT,
				raw_content TEXT,
				status TEXT DEFAULT 'pending',
				ai_analyzed INTEGER DEFAULT 0,
				ai_analyze_status TEXT DEFAULT 'pending',
				ai_analyze_msg TEXT,
				ai_analyze_time TEXT,
				collect_time TEXT NOT NULL DEFAULT(datetime('now')),
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS scout_detail(
				id integer PRIMARY KEY AUTOINCREMENT,
				record_id INTEGER NOT NULL,
				source_id INTEGER NOT NULL,
				title TEXT,
				content TEXT,
				author TEXT,
				publish_time TEXT,
				source_url TEXT,
				tags TEXT,
				categories TEXT,
				images TEXT,
				ai_summary TEXT,
				ai_keywords TEXT,
				ai_sentiment TEXT,
				ai_entities TEXT,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (record_id) REFERENCES scout_record(id) ON DELETE CASCADE
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS chat_session(
				id integer PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER NOT NULL,
				title TEXT,
				model_id INTEGER,
				employee_id INTEGER,
				session_type TEXT DEFAULT 'chat',
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
			)
			"""
		)
		
		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS chat_message(
				id integer PRIMARY KEY AUTOINCREMENT,
				session_id INTEGER NOT NULL,
				role TEXT NOT NULL,
				content TEXT NOT NULL,
				tokens INTEGER DEFAULT 0,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (session_id) REFERENCES chat_session(id) ON DELETE CASCADE
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS datav_screen(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				description TEXT,
				config TEXT DEFAULT '{}',
				refresh_interval INTEGER DEFAULT 60,
				enabled INTEGER DEFAULT 1,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS datav_location(
				id integer PRIMARY KEY AUTOINCREMENT,
				latitude REAL NOT NULL,
				longitude REAL NOT NULL,
				location_name TEXT,
				location_type TEXT DEFAULT 'default',
				source_id INTEGER,
				source_type TEXT DEFAULT 'scout',
				title TEXT,
				summary TEXT,
				sentiment TEXT DEFAULT 'neutral',
				tags TEXT,
				event_time TEXT,
				create_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS datav_cache(
				id integer PRIMARY KEY AUTOINCREMENT,
				cache_key TEXT NOT NULL UNIQUE,
				cache_value TEXT NOT NULL,
				expire_at TEXT,
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS sentiment_analysis(
				id integer PRIMARY KEY AUTOINCREMENT,
				source_type TEXT NOT NULL,
				source_id INTEGER,
				source_record_id INTEGER,
				title TEXT,
				content TEXT NOT NULL,
				summary TEXT,
				sentiment TEXT DEFAULT 'neutral',
				sentiment_score REAL DEFAULT 0.5,
				confidence REAL DEFAULT 0.0,
				keywords TEXT,
				topics TEXT,
				hot_score REAL DEFAULT 0.0,
				risk_level TEXT DEFAULT 'low',
				risk_tags TEXT,
				location_lat REAL,
				location_lng REAL,
				location_name TEXT,
				publish_time TEXT,
				analyze_time TEXT NOT NULL DEFAULT(datetime('now')),
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS sentiment_analysis_log(
				id integer PRIMARY KEY AUTOINCREMENT,
				analysis_id INTEGER,
				action TEXT NOT NULL,
				status TEXT DEFAULT 'running',
				total_count INTEGER DEFAULT 0,
				success_count INTEGER DEFAULT 0,
				fail_count INTEGER DEFAULT 0,
				error_msg TEXT,
				duration_ms INTEGER DEFAULT 0,
				create_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS friendship(
				id integer PRIMARY KEY AUTOINCREMENT,
				user_id INTEGER NOT NULL,
				friend_id INTEGER NOT NULL,
				status TEXT DEFAULT 'pending',
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
				FOREIGN KEY (friend_id) REFERENCES user(id) ON DELETE CASCADE,
				UNIQUE(user_id, friend_id)
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS private_message(
				id integer PRIMARY KEY AUTOINCREMENT,
				from_user_id INTEGER NOT NULL,
				to_user_id INTEGER NOT NULL,
				content TEXT NOT NULL,
				is_read INTEGER DEFAULT 0,
				send_time TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (from_user_id) REFERENCES user(id) ON DELETE CASCADE,
				FOREIGN KEY (to_user_id) REFERENCES user(id) ON DELETE CASCADE
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS group_chat(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				avatar TEXT DEFAULT '👥',
				description TEXT,
				creator_id INTEGER NOT NULL,
				status TEXT DEFAULT 'active',
				is_public INTEGER DEFAULT 0,
				max_members INTEGER DEFAULT 200,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (creator_id) REFERENCES user(id) ON DELETE CASCADE
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS group_member(
				id integer PRIMARY KEY AUTOINCREMENT,
				group_id INTEGER NOT NULL,
				user_id INTEGER NOT NULL,
				role TEXT DEFAULT 'member',
				join_time TEXT NOT NULL DEFAULT(datetime('now')),
				last_active TEXT,
				is_muted INTEGER DEFAULT 0,
				is_banned INTEGER DEFAULT 0,
				FOREIGN KEY (group_id) REFERENCES group_chat(id) ON DELETE CASCADE,
				FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
				UNIQUE(group_id, user_id)
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS group_message(
				id integer PRIMARY KEY AUTOINCREMENT,
				group_id INTEGER NOT NULL,
				from_user_id INTEGER NOT NULL,
				content TEXT NOT NULL,
				message_type TEXT DEFAULT 'text',
				file_path TEXT,
				file_name TEXT,
				is_read INTEGER DEFAULT 0,
				mentioned_users TEXT,
				send_time TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (group_id) REFERENCES group_chat(id) ON DELETE CASCADE,
				FOREIGN KEY (from_user_id) REFERENCES user(id) ON DELETE CASCADE
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS chat_file(
				id integer PRIMARY KEY AUTOINCREMENT,
				file_hash TEXT NOT NULL UNIQUE,
				file_name TEXT NOT NULL,
				file_path TEXT NOT NULL,
				file_size INTEGER NOT NULL,
				content_type TEXT,
				uploader_id INTEGER,
				upload_time TEXT NOT NULL DEFAULT(datetime('now')),
				FOREIGN KEY (uploader_id) REFERENCES user(id) ON DELETE CASCADE
			)
			"""
		)

		conn.execute(
			"""
			CREATE TABLE IF NOT EXISTS chat_server(
				id integer PRIMARY KEY AUTOINCREMENT,
				name TEXT NOT NULL,
				host TEXT NOT NULL,
				port INTEGER DEFAULT 80,
				protocol TEXT DEFAULT 'http',
				is_active INTEGER DEFAULT 1,
				is_default INTEGER DEFAULT 0,
				weight INTEGER DEFAULT 1,
				description TEXT,
				create_at TEXT NOT NULL DEFAULT(datetime('now')),
				update_at TEXT NOT NULL DEFAULT(datetime('now'))
			)
			"""
		)

		conn.commit()

def init_default_users():
	"""初始化默认测试用户"""
	import hashlib
	import secrets
	
	def hash_password(password: str, salt: bytes) -> str:
		dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
		return dk.hex()
	
	default_users = [
		{"username": "Alice", "password": "test123", "role": "user"},
		{"username": "Bob", "password": "test123", "role": "user"},
		{"username": "Charlie", "password": "test123", "role": "user"},
		{"username": "David", "password": "test123", "role": "user"},
		{"username": "Eve", "password": "test123", "role": "user"},
	]
	
	with get_connection() as conn:
		for user in default_users:
			existing = conn.execute("SELECT id FROM user WHERE username = ?", (user["username"],)).fetchone()
			if not existing:
				salt = secrets.token_bytes(16)
				password_hash = hash_password(user["password"], salt)
				try:
					conn.execute(
						"INSERT INTO user(username, password_hash, salt, role) VALUES(?, ?, ?, ?)",
						(user["username"], password_hash, salt.hex(), user["role"])
					)
				except sqlite3.IntegrityError:
					pass
		conn.commit()

def init_scout_sources():
	"""初始化瞭望数据源示例数据"""
	BAIDU_NEWS_HEADERS = """Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate, br, zstd
Accept-Language: zh-CN,zh;q=0.9
Connection: keep-alive
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36
Referer: https://news.baidu.com/
sec-ch-ua: "Chromium";v="141", "Not?A_Brand";v="24"
sec-ch-ua-mobile: ?0
sec-ch-ua-platform: "Windows"
Sec-Fetch-Dest: document
Sec-Fetch-Mode: navigate
Sec-Fetch-Site: same-site
Sec-Fetch-User: ?1
Upgrade-Insecure-Requests: 1"""
	
	sample_sources = [
		{
			"name": "百度新闻搜索",
			"url_pattern": "https://www.baidu.com/s?rtt=1&bsst=1&cl=2&tn=news&rsv_dl=ns_pc&word={关键字}",
			"request_method": "GET",
			"headers": BAIDU_NEWS_HEADERS,
			"enabled": 1
		}
	]
	
	with get_connection() as conn:
		for source in sample_sources:
			try:
				existing = conn.execute("SELECT id FROM scout_source WHERE name = ?", (source["name"],)).fetchone()
				if not existing:
					conn.execute(
						"INSERT INTO scout_source(name, url_pattern, request_method, headers, enabled) VALUES(?, ?, ?, ?, ?)",
						(source["name"], source["url_pattern"], source["request_method"], source["headers"], source["enabled"])
					)
			except sqlite3.IntegrityError:
				pass
		conn.commit()

def init_digital_employees():
	"""初始化数字员工示例数据"""
	sample_employees = [
		{
			"name": "川小农",
			"alias": "川小农",
			"category": "AI",
			"description": "智能农业助手，基于大模型提供农业相关的智能问答服务",
			"prompt": "你是川小农，一个专业的智能农业助手。你精通农业种植、养殖、农产品加工、农业政策等领域的知识。请用专业、友好、简洁的方式回答用户关于农业的问题。如果问题超出农业领域，请礼貌地告知用户你的专业范围。",
			"model_id": None,
			"api_interface_id": None,
			"avatar": "🌾",
			"welcome_msg": "你好！我是川小农，你的智能农业助手。有什么农业方面的问题可以问我哦！",
			"enabled": 1
		},
		{
			"name": "天气助手",
			"alias": "天气",
			"category": "普通",
			"description": "天气查询助手，提供城市天气信息查询服务。使用方式：@天气 城市名称",
			"prompt": None,
			"model_id": None,
			"api_interface_id": 2,
			"avatar": "🌤️",
			"welcome_msg": "你好！我是天气助手，输入城市名称即可查询天气信息。例如：北京",
			"enabled": 1
		},
		{
			"name": "音乐助手",
			"alias": "音乐",
			"category": "普通",
			"description": "随机音乐推荐助手，提供网易云音乐随机歌曲推荐服务。使用方式：@音乐",
			"prompt": None,
			"model_id": None,
			"api_interface_id": 1,
			"avatar": "🎵",
			"welcome_msg": "你好！我是音乐助手，随时为你推荐好听的音乐！",
			"enabled": 1
		}
	]
	
	with get_connection() as conn:
		for employee in sample_employees:
			try:
				existing = conn.execute("SELECT id FROM digital_employee WHERE alias = ?", (employee["alias"],)).fetchone()
				if not existing:
					conn.execute(
						"INSERT INTO digital_employee(name, alias, category, description, prompt, model_id, api_interface_id, avatar, welcome_msg, enabled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
						(employee["name"], employee["alias"], employee["category"], employee["description"], employee["prompt"], employee["model_id"], employee["api_interface_id"], employee["avatar"], employee["welcome_msg"], employee["enabled"])
					)
			except sqlite3.IntegrityError:
				pass
		conn.commit()

def init_api_interfaces():
	"""初始化接口管理示例数据"""
	sample_interfaces = [
		{
			"name": "网易云随机音乐",
			"url": "https://api.52vmy.cn/api/music/wy/rand",
			"method": "GET",
			"response_format": "JSON",
			"example": "https://api.52vmy.cn/api/music/wy/rand",
			"qps_limit": "每2秒最多4次，携带Token可无限制",
			"token_required": 0,
			"remark": "获取网易云音乐随机歌曲",
			"enabled": 1
		},
		{
			"name": "天气查询",
			"url": "https://api.52vmy.cn/api/query/tian",
			"method": "GET",
			"response_format": "JSON",
			"example": "https://api.52vmy.cn/api/query/tian?city=北京市",
			"qps_limit": "每2秒最多4次，携带Token可无限制",
			"token_required": 0,
			"remark": "查询城市天气信息，参数city为城市名称",
			"enabled": 1
		}
	]
	
	with get_connection() as conn:
		for interface in sample_interfaces:
			try:
				existing = conn.execute("SELECT id FROM api_interface WHERE url = ?", (interface["url"],)).fetchone()
				if not existing:
					conn.execute(
						"INSERT INTO api_interface(name, url, method, response_format, example, qps_limit, token_required, remark, enabled) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
						(interface["name"], interface["url"], interface["method"], interface["response_format"], interface["example"], interface["qps_limit"], interface["token_required"], interface["remark"], interface["enabled"])
					)
			except sqlite3.IntegrityError:
				pass
		conn.commit()

def init_sentiment_samples():
	"""初始化舆情分析示例数据"""
	from datetime import datetime, timedelta
	
	sample_sentiments = [
		{
			"source_type": "scout",
			"title": "农业科技创新助力乡村振兴",
			"content": "近年来，我国农业科技创新取得显著进展，人工智能、大数据、物联网等新技术正在深刻改变传统农业生产方式。智慧农业、精准农业等新模式不断涌现，为乡村振兴注入了新动能。",
			"summary": "农业科技创新推动乡村振兴发展",
			"sentiment": "positive",
			"sentiment_score": 0.85,
			"confidence": 0.92,
			"keywords": "农业科技,乡村振兴,智慧农业,精准农业",
			"risk_level": "low",
			"hot_score": 85.5,
			"location_name": "北京市",
			"location_lat": 39.9042,
			"location_lng": 116.4074,
			"publish_time": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "scout",
			"title": "农产品价格波动引发市场关注",
			"content": "近期部分农产品价格出现较大波动，引起市场广泛关注。专家指出，气候异常、物流成本上升等因素是导致价格波动的主要原因，建议农户做好风险管理。",
			"summary": "农产品价格波动受多种因素影响",
			"sentiment": "neutral",
			"sentiment_score": 0.52,
			"confidence": 0.88,
			"keywords": "农产品,价格波动,市场,风险管理",
			"risk_level": "medium",
			"hot_score": 72.3,
			"location_name": "上海市",
			"location_lat": 31.2304,
			"location_lng": 121.4737,
			"publish_time": (datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "scout",
			"title": "极端天气对农作物造成严重影响",
			"content": "今年夏季多地遭遇极端高温天气，部分地区农作物受损严重。农业部门已启动应急预案，指导农户采取抗旱措施，尽量减少损失。",
			"summary": "极端高温天气影响农作物生长",
			"sentiment": "negative",
			"sentiment_score": 0.28,
			"confidence": 0.95,
			"keywords": "极端天气,高温,农作物,抗旱",
			"risk_level": "high",
			"risk_tags": "自然灾害",
			"hot_score": 92.8,
			"location_name": "河南省",
			"location_lat": 34.7466,
			"location_lng": 113.6253,
			"publish_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "chat",
			"title": "用户咨询农业贷款政策",
			"content": "用户询问农业贷款的申请条件和利率政策，客服详细解释了相关政策，并提供了申请流程指引。",
			"summary": "用户咨询农业贷款政策",
			"sentiment": "neutral",
			"sentiment_score": 0.55,
			"confidence": 0.85,
			"keywords": "农业贷款,政策,利率,申请",
			"risk_level": "low",
			"hot_score": 45.2,
			"publish_time": (datetime.now() - timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "scout",
			"title": "新型农药研发取得突破",
			"content": "国内某农业科技公司宣布在新型生物农药研发方面取得重大突破，该农药对环境友好，杀虫效果显著，有望在明年大面积推广应用。",
			"summary": "新型生物农药研发成功",
			"sentiment": "positive",
			"sentiment_score": 0.91,
			"confidence": 0.94,
			"keywords": "农药,生物农药,研发,环保",
			"risk_level": "low",
			"hot_score": 88.6,
			"location_name": "广东省",
			"location_lat": 23.1291,
			"location_lng": 113.2644,
			"publish_time": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "chat",
			"title": "用户投诉农产品质量问题",
			"content": "用户反映购买的农产品存在质量问题，要求退换货。客服已受理投诉，并承诺在24小时内给出处理结果。",
			"summary": "用户投诉农产品质量问题",
			"sentiment": "negative",
			"sentiment_score": 0.22,
			"confidence": 0.89,
			"keywords": "质量问题,投诉,退换货",
			"risk_level": "medium",
			"risk_tags": "质量投诉",
			"hot_score": 67.5,
			"publish_time": (datetime.now() - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "scout",
			"title": "农村电商助力农产品上行",
			"content": "农村电商平台发展迅速，越来越多的农产品通过网络销售到全国各地。直播带货、短视频推广等新模式让优质农产品走进千家万户。",
			"summary": "农村电商促进农产品销售",
			"sentiment": "positive",
			"sentiment_score": 0.82,
			"confidence": 0.90,
			"keywords": "农村电商,直播带货,农产品,销售",
			"risk_level": "low",
			"hot_score": 78.9,
			"location_name": "浙江省",
			"location_lat": 30.2741,
			"location_lng": 120.1552,
			"publish_time": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
		},
		{
			"source_type": "scout",
			"title": "农业保险政策进一步完善",
			"content": "国家出台新政策，进一步完善农业保险体系，扩大保险覆盖范围，提高赔付比例，为农户提供更全面的风险保障。",
			"summary": "农业保险政策完善",
			"sentiment": "positive",
			"sentiment_score": 0.88,
			"confidence": 0.93,
			"keywords": "农业保险,政策,风险保障",
			"risk_level": "low",
			"hot_score": 71.2,
			"location_name": "四川省",
			"location_lat": 30.5728,
			"location_lng": 104.0668,
			"publish_time": (datetime.now() - timedelta(hours=18)).strftime("%Y-%m-%d %H:%M:%S")
		}
	]
	
	with get_connection() as conn:
		count = conn.execute("SELECT COUNT(*) as total FROM sentiment_analysis").fetchone()["total"]
		if count == 0:
			for item in sample_sentiments:
				conn.execute(
					"""INSERT INTO sentiment_analysis(source_type, title, content, summary, sentiment,
					   sentiment_score, confidence, keywords, risk_level, risk_tags, hot_score,
					   location_name, location_lat, location_lng, publish_time)
					   VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
					(item["source_type"], item["title"], item["content"], item["summary"],
					 item["sentiment"], item["sentiment_score"], item["confidence"],
					 item["keywords"], item["risk_level"], item.get("risk_tags"),
					 item["hot_score"], item.get("location_name"), item.get("location_lat"),
					 item.get("location_lng"), item["publish_time"])
				)
			conn.commit()