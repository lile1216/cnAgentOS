import os
import sys
import traceback

os.chdir(r'c:\Users\47146\cnAgentOS')

try:
    print("Starting server...")
    
    # Import all required modules
    import tornado.ioloop
    import tornado.web
    from tornado.httpserver import HTTPServer
    
    print("Tornado imported")
    
    # Import app modules
    from app.models.db import init_db, init_default_users, init_scout_sources, init_api_interfaces, init_digital_employees, init_sentiment_samples
    from app.models.user import UserRepository
    
    print("Database modules imported")
    
    # Initialize database
    print("Initializing database...")
    init_db()
    print("init_db done")
    
    init_default_users()
    print("init_default_users done")
    
    init_scout_sources()
    print("init_scout_sources done")
    
    init_api_interfaces()
    print("init_api_interfaces done")
    
    init_digital_employees()
    print("init_digital_employees done")
    
    init_sentiment_samples()
    print("init_sentiment_samples done")
    
    # Import make_app
    from app import make_app
    print("make_app imported")
    
    # Create and start server
    app = make_app()
    print("App created")
    
    app.listen(8888)
    print("Server listening on port 8888")
    
    print("====== Server 启动成功 ====== 端口：8888 =======")
    
    # Keep server running
    tornado.ioloop.IOLoop.current().start()
    
except Exception as e:
    print(f"Error starting server: {e}")
    traceback.print_exc()
    input("Press Enter to exit...")
