import os
import psycopg2
import psycopg2.extras
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Database:
    def __init__(self):
        self.connection: Optional[psycopg2.extensions.connection] = None
        
    def connect(self):
        """创建数据库连接"""
        if self.connection is None or self.connection.closed:
            try:
                # 使用后端数据库配置
                self.connection = psycopg2.connect(
                    host=os.getenv("POSTGRES_HOST"),
                    port=os.getenv("POSTGRES_PORT", "5432"),
                    database=os.getenv("POSTGRES_DB"),
                    user=os.getenv("POSTGRES_USER"),
                    password=os.getenv("POSTGRES_PASSWORD")
                )
                self.connection.autocommit = True
            except Exception as e:
                print(f"Database connection error: {e}")
                raise
    
    def disconnect(self):
        """关闭数据库连接"""
        if self.connection and not self.connection.closed:
            self.connection.close()
            self.connection = None
    
    def fetch_all(self, query: str, params=None) -> List[Dict[str, Any]]:
        """执行查询并返回所有结果"""
        self.connect()
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Query error: {e}")
            raise
    
    def fetch_one(self, query: str, params=None) -> Optional[Dict[str, Any]]:
        """执行查询并返回单个结果"""
        self.connect()
        try:
            with self.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            print(f"Query error: {e}")
            raise
    
    def execute(self, query: str, params=None) -> str:
        """执行非查询语句"""
        self.connect()
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.statusmessage
        except Exception as e:
            print(f"Execute error: {e}")
            raise

# 全局数据库实例
database = Database()

# 数据库连接依赖
def get_database():
    return database