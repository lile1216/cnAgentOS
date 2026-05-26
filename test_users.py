from app.models.db import init_db, get_connection

init_db()
conn = get_connection()
rows = conn.execute('SELECT * FROM user').fetchall()
print('Users:', [dict(row) for row in rows])
