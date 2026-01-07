#!/usr/bin/env python3
"""
检查数据库中航班数据的 task_id 是否正常
"""

import sys
import os
import sqlite3
from pathlib import Path

# 查找数据库文件


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


def check_task_ids():
    """检查数据库中航班数据的 task_id"""
    db_path = find_database()
    if not db_path:
        print("❌ 未找到数据库文件")
        return

    print(f"📁 数据库文件: {db_path}")

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        with conn:
            print("=" * 80)
            print("📊 检查数据库中航班数据的 task_id")
            print("=" * 80)

            # 1. 统计总航班数
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM flight_results
                WHERE status = 'active'
            """)
            total_flights = cursor.fetchone()['total']
            print(f"\n✅ 总航班数（active状态）: {total_flights}")

            # 2. 统计有 task_id 的航班数
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM flight_results
                WHERE status = 'active' AND task_id IS NOT NULL
            """)
            flights_with_task_id = cursor.fetchone()['total']
            print(f"✅ 有 task_id 的航班数: {flights_with_task_id}")

            # 3. 统计没有 task_id 的航班数
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM flight_results
                WHERE status = 'active' AND task_id IS NULL
            """)
            flights_without_task_id = cursor.fetchone()['total']
            print(f"⚠️  没有 task_id 的航班数: {flights_without_task_id}")

            # 4. 按 task_id 分组统计
            print(f"\n📋 按 task_id 分组统计:")
            print("-" * 80)
            cursor.execute("""
                SELECT
                    task_id,
                    COUNT(*) as flight_count,
                    MIN(scrape_time) as earliest_scrape,
                    MAX(scrape_time) as latest_scrape
                FROM flight_results
                WHERE status = 'active' AND task_id IS NOT NULL
                GROUP BY task_id
                ORDER BY task_id DESC
                LIMIT 20
            """)

            print(f"{'任务ID':<10} {'航班数':<10} {'最早抓取时间':<25} {'最晚抓取时间':<25}")
            print("-" * 80)
            for row in cursor.fetchall():
                task_id = row['task_id']
                count = row['flight_count']
                earliest = row['earliest_scrape']
                latest = row['latest_scrape']
                earliest_str = str(earliest) if earliest else 'N/A'
                latest_str = str(latest) if latest else 'N/A'
                print(
                    f"{task_id:<10} {count:<10} {earliest_str:<25} {latest_str:<25}")

            # 5. 检查 task_id 是否在 task_records 表中存在
            print(f"\n🔍 检查 task_id 是否在 task_records 表中存在:")
            print("-" * 80)
            cursor.execute("""
                SELECT DISTINCT fr.task_id
                FROM flight_results fr
                WHERE fr.status = 'active'
                  AND fr.task_id IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM task_records tr
                      WHERE tr.id = fr.task_id
                  )
            """)

            orphaned_task_ids = cursor.fetchall()
            if orphaned_task_ids:
                print(
                    f"⚠️  发现 {
                        len(orphaned_task_ids)} 个孤立的 task_id（在 task_records 中不存在）:")
                for row in orphaned_task_ids:
                    print(f"   - task_id: {row['task_id']}")
            else:
                print("✅ 所有 task_id 都在 task_records 表中存在")

            # 6. 检查每个任务的航班数量是否与 task_records 中的 flights_count 一致
            print(f"\n🔍 检查任务记录的航班数量是否一致:")
            print("-" * 80)
            cursor.execute("""
                SELECT
                    tr.id as task_id,
                    tr.flights_count as recorded_count,
                    COUNT(fr.id) as actual_count
                FROM task_records tr
                LEFT JOIN flight_results fr ON fr.task_id = tr.id AND fr.status = 'active'
                GROUP BY tr.id, tr.flights_count
                HAVING tr.flights_count != COUNT(fr.id) OR (tr.flights_count IS NULL AND COUNT(fr.id) > 0)
                ORDER BY tr.id DESC
                LIMIT 20
            """)

            mismatches = cursor.fetchall()
            if mismatches:
                print(f"⚠️  发现 {len(mismatches)} 个任务记录的航班数量不一致:")
                print(f"{'任务ID':<10} {'记录数量':<12} {'实际数量':<12}")
                print("-" * 80)
                for row in mismatches:
                    task_id = row['task_id']
                    recorded = row['recorded_count']
                    actual = row['actual_count']
                    print(f"{task_id:<10} {recorded or 0:<12} {actual:<12}")
            else:
                print("✅ 所有任务记录的航班数量都一致")

            # 7. 显示最近的任务及其航班数
            print(f"\n📋 最近的任务及其航班数:")
            print("-" * 80)
            cursor.execute("""
                SELECT
                    tr.id,
                    tr.task_name,
                    tr.status,
                    tr.flights_count,
                    tr.start_time,
                    tr.end_time,
                    COUNT(fr.id) as actual_flight_count
                FROM task_records tr
                LEFT JOIN flight_results fr ON fr.task_id = tr.id AND fr.status = 'active'
                GROUP BY tr.id, tr.task_name, tr.status, tr.flights_count, tr.start_time, tr.end_time
                ORDER BY tr.id DESC
                LIMIT 10
            """)

            print(
                f"{
                    '任务ID':<10} {
                    '任务名称':<30} {
                    '状态':<12} {
                    '记录数':<10} {
                        '实际数':<10}")
            print("-" * 80)
            for row in cursor.fetchall():
                task_id = row['id']
                task_name = row['task_name']
                status = row['status']
                recorded_count = row['flights_count']
                actual_count = row['actual_flight_count']
                task_name_short = (task_name or 'N/A')[:28]
                print(
                    f"{
                        task_id:<10} {
                        task_name_short:<30} {
                        status or 'N/A':<12} {
                        recorded_count or 0:<10} {
                        actual_count:<10}")

            print("\n" + "=" * 80)
            print("✅ 检查完成")
            print("=" * 80)

    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_task_ids()
