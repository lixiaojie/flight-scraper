#!/usr/bin/env python3
"""
清理没有 task_id 的历史航班数据
"""

import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime


def find_database():
    """查找数据库文件"""
    project_root = Path(__file__).parent.parent
    possible_locations = [
        project_root / "backend" / "flight_scraper.db",
        project_root / "data" / "flight_scraper.db",
        project_root / "flight_scraper.db",
    ]

    for db_path in possible_locations:
        if db_path.exists():
            return str(db_path)

    # 如果都不存在，尝试从环境变量获取
    db_url = os.getenv("DATABASE_URL", "")
    if db_url and db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
        if os.path.exists(db_path):
            return db_path

    return None


def cleanup_flights_without_task_id(dry_run=True):
    """清理没有 task_id 的航班数据"""
    db_path = find_database()
    if not db_path:
        print("❌ 未找到数据库文件")
        return

    print(f"📁 数据库文件: {db_path}")
    print(f"🔍 模式: {'预览模式（不会删除数据）' if dry_run else '执行模式（将删除数据）'}")
    print("=" * 80)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        with conn:
            # 1. 统计没有 task_id 的航班数
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM flight_results
                WHERE status = 'active' AND task_id IS NULL
            """)
            total_without_task_id = cursor.fetchone()['count']
            print(f"\n📊 没有 task_id 的航班总数: {total_without_task_id}")

            if total_without_task_id == 0:
                print("✅ 没有需要清理的数据")
                return

            # 2. 按抓取时间分组统计
            print(f"\n📋 按抓取时间分组统计（最近20组）:")
            print("-" * 80)
            cursor.execute("""
                SELECT
                    DATE(scrape_time) as scrape_date,
                    COUNT(*) as count
                FROM flight_results
                WHERE status = 'active' AND task_id IS NULL
                GROUP BY DATE(scrape_time)
                ORDER BY scrape_date DESC
                LIMIT 20
            """)

            print(f"{'抓取日期':<15} {'航班数':<10}")
            print("-" * 80)
            for row in cursor.fetchall():
                print(f"{row['scrape_date']:<15} {row['count']:<10}")

            # 3. 询问是否继续
            if dry_run:
                print(
                    f"\n⚠️  预览模式：将删除 {total_without_task_id} 条没有 task_id 的航班数据")
                print(
                    "   要执行删除，请运行: python3 scripts/cleanup_flights_without_task_id.py --execute")
            else:
                # 执行删除
                print(
                    f"\n🗑️  开始删除 {total_without_task_id} 条没有 task_id 的航班数据...")
                cursor.execute("""
                    DELETE FROM flight_results
                    WHERE status = 'active' AND task_id IS NULL
                """)
                deleted_count = cursor.rowcount
                conn.commit()
                print(f"✅ 已删除 {deleted_count} 条航班数据")

                # 验证删除结果
                cursor.execute("""
                    SELECT COUNT(*) as count
                    FROM flight_results
                    WHERE status = 'active' AND task_id IS NULL
                """)
                remaining = cursor.fetchone()['count']
                print(f"📊 剩余没有 task_id 的航班数: {remaining}")

        print("\n" + "=" * 80)
        print("✅ 清理完成")
        print("=" * 80)

    except Exception as e:
        print(f"❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='清理没有 task_id 的历史航班数据')
    parser.add_argument('--execute', action='store_true', help='执行删除（默认是预览模式）')
    args = parser.parse_args()

    cleanup_flights_without_task_id(dry_run=not args.execute)
