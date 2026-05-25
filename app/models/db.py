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