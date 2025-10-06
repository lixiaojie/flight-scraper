#!/usr/bin/env python3
"""
数据库迁移脚本：为航班结果表添加新字段
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """执行数据库迁移"""
    # 获取数据库文件路径
    db_path = Path(__file__).parent / "flight_scraper.db"
    
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return False
    
    try:
        # 连接数据库
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        print("🔍 检查现有表结构...")
        cursor.execute("PRAGMA table_info(flight_results)")
        columns = cursor.fetchall()
        existing_columns = [col[1] for col in columns]
        print(f"现有列: {existing_columns}")
        
        # 需要添加的新列
        new_columns = [
            ("departure_date", "TEXT"),
            ("flight_duration", "TEXT")
        ]
        
        # 需要修改的列（增加长度）
        modify_columns = [
            ("departure_airport", "VARCHAR(50)"),
            ("arrival_airport", "VARCHAR(50)")
        ]
        
        # 添加新列
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                print(f"➕ 添加列: {col_name} {col_type}")
                cursor.execute(f"ALTER TABLE flight_results ADD COLUMN {col_name} {col_type}")
            else:
                print(f"✅ 列已存在: {col_name}")
        
        # 修改现有列长度（SQLite不支持直接修改列类型，需要重建表）
        print("🔄 更新机场列长度...")
        
        # 获取所有列信息
        cursor.execute("PRAGMA table_info(flight_results)")
        columns_info = cursor.fetchall()
        
        # 创建新表结构
        create_sql = """
        CREATE TABLE flight_results_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            airline VARCHAR(100) NOT NULL,
            flight_number VARCHAR(20) NOT NULL,
            departure_date TEXT,
            departure_time VARCHAR(10) NOT NULL,
            departure_airport VARCHAR(50) NOT NULL,
            arrival_time VARCHAR(10) NOT NULL,
            arrival_airport VARCHAR(50) NOT NULL,
            flight_duration TEXT,
            price FLOAT NOT NULL,
            currency VARCHAR(10) DEFAULT 'CNY',
            scrape_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            source VARCHAR(50) DEFAULT '12306',
            status VARCHAR(20) DEFAULT 'active',
            raw_data TEXT,
            notes TEXT
        )
        """
        
        # 创建新表
        cursor.execute(create_sql)
        
        # 复制数据
        cursor.execute("""
            INSERT INTO flight_results_new 
            SELECT 
                id, airline, flight_number, 
                NULL as departure_date,  -- 新字段设为NULL
                departure_time, departure_airport, 
                arrival_time, arrival_airport,
                NULL as flight_duration,  -- 新字段设为NULL
                price, currency, scrape_time, source, status, raw_data, notes
            FROM flight_results
        """)
        
        # 删除旧表
        cursor.execute("DROP TABLE flight_results")
        
        # 重命名新表
        cursor.execute("ALTER TABLE flight_results_new RENAME TO flight_results")
        
        # 创建索引
        indexes = [
            "CREATE INDEX idx_flight_number ON flight_results(flight_number)",
            "CREATE INDEX idx_departure_time ON flight_results(departure_time)",
            "CREATE INDEX idx_price ON flight_results(price)",
            "CREATE INDEX idx_scrape_time ON flight_results(scrape_time)",
            "CREATE INDEX idx_airline ON flight_results(airline)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
            except sqlite3.OperationalError as e:
                if "already exists" not in str(e):
                    print(f"⚠️  索引创建警告: {e}")
        
        # 提交更改
        conn.commit()
        
        print("✅ 数据库迁移完成")
        return True
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
