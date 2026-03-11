"""数据库初始化脚本"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.models.database import init_db, engine
from backend.app.models import models


def main():
    """初始化数据库"""
    print("开始初始化数据库...")
    
    # 创建所有表
    init_db()
    
    print("数据库初始化完成！")
    print(f"数据库文件位置: {engine.url}")
    
    # 列出所有创建的表
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n创建的表: {', '.join(tables)}")


if __name__ == "__main__":
    main()
