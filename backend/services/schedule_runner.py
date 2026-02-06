"""
定时/循环任务调度：定期检查已到时的 scheduled/recurring 任务并启动执行；
计划开始时间超过 10 分钟未执行且当前无运行中任务时，将定时任务标记为超时失效。
"""
import logging
import threading
import time
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# 定时任务超时阈值：计划开始时间超过该时长未执行则自动失效
SCHEDULED_TASK_TIMEOUT_MINUTES = 10


def _run_schedule_loop():
    """后台循环：首次 5 秒后检查，之后每 5 秒检查已到时的定时/循环任务并启动；超时未执行的定时任务标记为失败。"""
    try:
        import pytz
        from core.database import SessionLocal
        from models.task_record import TaskRecord
        from services.task_scheduler import TaskScheduler
    except ImportError as e:
        logger.warning(f"schedule_runner 依赖不可用: {e}")
        return
    shanghai_tz = pytz.timezone("Asia/Shanghai")
    logger.info("定时调度线程已启动，每 5 秒检查一次")
    time.sleep(5)  # 启动后 5 秒做第一次检查，之后每 5 秒
    loop_count = 0
    while True:
        try:
            time.sleep(5)
            loop_count += 1
            db = SessionLocal()
            try:
                run_mode_col = getattr(TaskRecord, 'run_mode', None)
                schedule_time_col = getattr(TaskRecord, 'schedule_time', None)
                if run_mode_col is None or schedule_time_col is None:
                    if loop_count == 1:
                        logger.warning("schedule_runner: run_mode 或 schedule_time 列不存在，跳过调度")
                    db.close()
                    continue
                now = datetime.now(shanghai_tz).replace(tzinfo=None)
                running = db.query(TaskRecord).filter(TaskRecord.status == 'running').count()
                # 无运行中任务时：将「计划开始时间已过 10 分钟」的定时任务标记为超时失效
                if running == 0:
                    timeout_threshold = now - timedelta(minutes=SCHEDULED_TASK_TIMEOUT_MINUTES)
                    overdue = (
                        db.query(TaskRecord)
                        .filter(
                            TaskRecord.status == 'waiting',
                            run_mode_col == 'scheduled',
                            schedule_time_col < timeout_threshold,
                        )
                        .all()
                    )
                    for task in overdue:
                        task.status = 'failed'
                        task.current_step = '超时未执行'
                        task.error_message = f'计划开始时间已超过{SCHEDULED_TASK_TIMEOUT_MINUTES}分钟未执行，自动失效'
                        logger.info(f"⏱ 定时任务超时失效: {task.id} - {task.task_name}")
                    if overdue:
                        db.commit()
                if running > 0:
                    db.close()
                    continue
                # 已到时的定时或循环任务（schedule_time <= now），取最早一条
                due = (
                    db.query(TaskRecord)
                    .filter(
                        TaskRecord.status == 'waiting',
                        TaskRecord.run_mode.in_(['scheduled', 'recurring']),
                        TaskRecord.schedule_time <= now,
                    )
                    .order_by(TaskRecord.schedule_time)
                    .first()
                )
                if not due:
                    continue
                task_id = due.id
                due.status = 'running'
                due.current_step = '等待执行'
                if not due.start_time:
                    due.start_time = now
                db.commit()
                logger.info(f"⏰ 定时调度启动任务: {task_id} - {due.task_name}")
                scheduler = TaskScheduler(db)
                t = threading.Thread(
                    target=scheduler.run_task_and_continue,
                    args=(task_id,),
                    daemon=True,
                    name=f"Schedule-{task_id}",
                )
                t.start()
            finally:
                db.close()
        except Exception as e:
            logger.error(f"schedule_runner 本轮异常: {e}", exc_info=True)
