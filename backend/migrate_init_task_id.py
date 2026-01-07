#!/usr/bin/env python3
"""
初始化历史任务记录的task_id
为flight_results表中的历史记录分配task_id
"""

from datetime import datetime
from database_config import DATABASE_URL
from sqlalchemy import create_engine, text
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def migrate_init_task_id():
    """为历史航班记录初始化task_id"""
    try:
        # 创建数据库连接
        engine = create_engine(DATABASE_URL)

        with engine.connect() as conn:
            # 首先检查表是否存在
            result = conn.execute(text("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='flight_results'
            """))

            if result.fetchone() is None:
                print("⚠️ flight_results 表不存在，请先运行数据库初始化脚本。")
                return

            # 检查task_id字段是否存在
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM pragma_table_info('flight_results')
                WHERE name = 'task_id'
            """))

            if result.fetchone()[0] == 0:
                print("⚠️ task_id 字段不存在，请先运行 migrate_add_task_id.py")
                return

            # 获取所有缺少task_id的航班记录
            result = conn.execute(text("""
                SELECT id, scrape_time, source
                FROM flight_results
                WHERE task_id IS NULL
                ORDER BY scrape_time ASC
            """))

            flights_without_id = result.fetchall()
            print(f"✅ 找到 {len(flights_without_id)} 条缺少task_id的航班记录")

            if not flights_without_id:
                print("✅ 所有航班记录都已分配task_id，无需迁移")
                return

            # 获取所有任务记录，按创建时间排序
            result = conn.execute(text("""
                SELECT id, created_at, task_name
                FROM task_records
                ORDER BY created_at ASC
            """))

            tasks = result.fetchall()
            print(f"✅ 找到 {len(tasks)} 个任务记录")

            if not tasks:
                print("⚠️ 没有找到任务记录，无法分配task_id")
                return

            # 为航班记录分配task_id
            # 策略：根据创建时间匹配到最接近的任务
            updated_count = 0

            for flight in flights_without_id:
                flight_id, flight_scrape_time, flight_source = flight

                # 找到创建时间最接近的任务
                best_task = None
                min_time_diff = float('inf')

                for task in tasks:
                    task_id, task_created_at, task_name = task

                    # 计算时间差（绝对值）
                    if flight_scrape_time and task_created_at:
                        try:
                            # 解析时间字符串
                            if isinstance(flight_scrape_time, str):
                                flight_time = datetime.fromisoformat(
                                    flight_scrape_time.replace('Z', '+00:00'))
                            else:
                                flight_time = flight_scrape_time

                            if isinstance(task_created_at, str):
                                task_time = datetime.fromisoformat(
                                    task_created_at.replace('Z', '+00:00'))
                            else:
                                task_time = task_created_at

                            time_diff = abs(
                                (flight_time - task_time).total_seconds())
                            if time_diff < min_time_diff:
                                min_time_diff = time_diff
                                best_task = task
                        except Exception as e:
                            print(f"⚠️ 时间解析失败: {e}")
                            continue

                if best_task:
                    task_id = best_task[0]

                    # 更新航班记录的task_id
                    conn.execute(text("""
                        UPDATE flight_results
                        SET task_id = :task_id
                        WHERE id = :flight_id
                    """), {"task_id": task_id, "flight_id": flight_id})

                    updated_count += 1
                    print(
                        f"✅ 航班记录 {flight_id} 分配到任务 {task_id} ({
                            best_task[2]})")
                else:
                    print(f"⚠️ 航班记录 {flight_id} 无法匹配到合适的任务")

            conn.commit()
            print(f"✅ 成功为 {updated_count} 条航班记录分配了task_id")

            # 验证结果
            result = conn.execute(text("""
                SELECT COUNT(*) as count
                FROM flight_results
                WHERE task_id IS NOT NULL
            """))

            total_with_id = result.fetchone()[0]
            print(f"✅ 现在有 {total_with_id} 条航班记录包含task_id")

    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 开始初始化历史任务记录的task_id...")
    migrate_init_task_id()
    print("✅ 迁移完成")
