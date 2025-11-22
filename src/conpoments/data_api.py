"""
数据API模块

功能：
- 提供用户数据和投诉数据的存储、查询、修改接口，支持多数据库文件。
- 支持初始化数据库表结构。

主要接口：
- init_db(db_path='csbot.db'): 初始化数据库（创建表结构），可指定数据库文件名。
- get_user_info(user_id, db_path='csbot.db'): 查询指定用户信息，返回字典。
- update_user_info(user_id, field, value, db_path='csbot.db'): 更新指定用户的某个字段，返回是否成功。
- add_complaint(user_id, content, db_path='csbot.db'): 添加投诉记录。

用法示例：
    # 初始化数据库
    init_db('my_script.db')
    # 查询用户
    info = get_user_info('user1', db_path='my_script.db')
    # 更新用户
    update_user_info('user1', 'amount', 100.0, db_path='my_script.db')
    # 添加投诉
    add_complaint('user1', '服务态度不好', db_path='my_script.db')

命令行初始化数据库：
    python data_api.py my_script.db
"""

import sqlite3

DB_PATH = 'csbot.db'

class DatabaseAPI:
    """
    数据库接口类，根据脚本文件名自动选择数据库文件。
    用法示例：
        db = DatabaseAPI('myscript.txt')
        db.init_db()
        db.get_user_info('user1')
        db.update_user_info('user1', 'amount', 100.0)
        db.add_complaint('user1', '服务态度不好')
    """
    def __init__(self, script_filename):
        # 以脚本文件名为基础生成数据库文件名
        import os
        base = os.path.splitext(os.path.basename(script_filename))[0]
        self.db_path = f"{base}.db"

    def get_connection(self):
        import sqlite3
        return sqlite3.connect(self.db_path)

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                amount REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaint (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                content TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def get_user_info(self, user_id):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, name, amount FROM user WHERE user_id=?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'user_id': row[0], 'name': row[1], 'amount': row[2]}
        return None

    def update_user_info(self, user_id, field, value):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f'UPDATE user SET {field}=? WHERE user_id=?', (value, user_id))
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated

    def add_complaint(self, user_id, content):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO complaint (user_id, content) VALUES (?, ?)', (user_id, content))
        conn.commit()
        conn.close()
        return True

def get_connection(db_path='csbot.db'):
    return sqlite3.connect(db_path)

def init_db(db_path='csbot.db'):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            amount REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS complaint (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_user_info(user_id, db_path='csbot.db'):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, name, amount FROM user WHERE user_id=?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {'user_id': row[0], 'name': row[1], 'amount': row[2]}
    return None

def update_user_info(user_id, field, value, db_path='csbot.db'):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(f'UPDATE user SET {field}=? WHERE user_id=?', (value, user_id))
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated

def add_complaint(user_id, content, db_path='csbot.db'):
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO complaint (user_id, content) VALUES (?, ?)', (user_id, content))
    conn.commit()
    conn.close()
    return True

# 初始化数据库（首次运行时调用）
if __name__ == '__main__':
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'csbot.db'
    init_db(db_path)
