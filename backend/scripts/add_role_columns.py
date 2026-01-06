"""
手动添加角色标签相关的数据库列
运行方式: python -m scripts.add_role_columns
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import text


def add_columns():
    app = create_app()
    
    with app.app_context():
        engine = db.engine
        dialect = engine.dialect.name
        
        def _exec(stmt):
            with engine.begin() as conn:
                conn.execute(text(stmt))
        
        def has_column_mysql(table: str, column: str) -> bool:
            with engine.begin() as conn:
                rows = conn.execute(text(
                    """
                    SELECT 1
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = :table
                      AND COLUMN_NAME = :column
                    LIMIT 1
                    """
                ), {"table": table, "column": column}).all()
                return bool(rows)
        
        print(f"数据库类型: {dialect}")
        
        # 添加 teacher_posts.required_roles_json
        if dialect in {"mysql", "mariadb"}:
            if not has_column_mysql("teacher_posts", "required_roles_json"):
                print("添加 teacher_posts.required_roles_json 列...")
                _exec("ALTER TABLE teacher_posts ADD COLUMN required_roles_json TEXT NULL")
                print("完成!")
            else:
                print("teacher_posts.required_roles_json 列已存在")
            
            # 添加 cooperation_requests.applied_roles_json
            if not has_column_mysql("cooperation_requests", "applied_roles_json"):
                print("添加 cooperation_requests.applied_roles_json 列...")
                _exec("ALTER TABLE cooperation_requests ADD COLUMN applied_roles_json TEXT NULL")
                print("完成!")
            else:
                print("cooperation_requests.applied_roles_json 列已存在")
            
            # 添加 cooperation_requests.suggested_roles_json
            if not has_column_mysql("cooperation_requests", "suggested_roles_json"):
                print("添加 cooperation_requests.suggested_roles_json 列...")
                _exec("ALTER TABLE cooperation_requests ADD COLUMN suggested_roles_json TEXT NULL")
                print("完成!")
            else:
                print("cooperation_requests.suggested_roles_json 列已存在")
        
        print("\n所有列添加完成!")


if __name__ == "__main__":
    add_columns()
