#!/usr/bin/env python3
import os
import sqlite3
import glob
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def remove_result_files():
    result_dirs = [
        ROOT / 'results',                 # repo 根部结果目录
        ROOT / 'backend' / 'results',     # backend 下结果目录（若存在）
        ROOT / 'backend',                 # 直接在 backend/ 下产生的历史抓取文件
    ]
    patterns = [
        'flight_data_*.txt',
        'flight_page_source_*.xml',
        'flight_scraper_final_*.png',
        'parsed_flights_*.json',
        'manual_run_*.log',
        'task-*.log',
        # 可能的错误截图/页面
        'flight_scraper_error_*.png',
        'flight_scraper_error_*.xml',
    ]
    removed = 0
    for d in result_dirs:
        if not d.exists():
            continue
        for pat in patterns:
            for p in d.glob(pat):
                try:
                    p.unlink()
                    removed += 1
                except Exception:
                    pass
    print(f"Removed {removed} result files")


def purge_sqlite(db_path: Path):
    if not db_path.exists():
        print(f"DB not found: {db_path}")
        return
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        # purge tables if exist
        cur.execute("DELETE FROM flight_results;")
        cur.execute("DELETE FROM task_records;")
        conn.commit()
        # vacuum to reclaim space
        cur.execute("VACUUM;")
        print(f"Purged tables in {db_path}")
    except Exception as e:
        print(f"Purge failed on {db_path}: {e}")
    finally:
        conn.close()


def main():
    remove_result_files()
    # 使用统一的数据库配置
    import sys
    sys.path.insert(0, str(ROOT / 'backend'))
    from database_config import DATABASE_LOCATIONS

    candidates = list(DATABASE_LOCATIONS.values())
    for db in candidates:
        purge_sqlite(db)
    print("Cleanup done.")


if __name__ == '__main__':
    main()
