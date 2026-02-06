"""
任务调度器服务
支持批量任务创建和按计划顺序执行
"""

import threading
import time
import json
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import pytz

from models.task_record import TaskRecord
from services.task_service import TaskService

logger = logging.getLogger(__name__)

# 全局任务执行锁，确保同一时间只有一个任务在执行
_task_execution_lock = threading.Lock()
_current_executing_task_id = None
_lock_acquired_time = None  # 记录锁获取时间，用于检测卡住的任务


class TaskScheduler:
    """任务调度器，支持批量任务按顺序执行"""

    def __init__(self, db: Session):
        self.db = db
        self.task_service = TaskService(db)
        self.running_tasks = {}  # {task_id: thread}
        self.task_queue = []  # 待执行任务队列

    def create_batch_tasks(
        self,
        tasks: List[Dict[str, Any]],
        execute_immediately: bool = True,
        sequential: bool = True
    ) -> List[TaskRecord]:
        """
        批量创建任务
        
        Args:
            tasks: 任务配置列表，每个任务包含：
                - task_name: 可选的任务名称
                - task_type: 任务类型，默认 'flight_scraper'
                - source: 数据源，默认 '12306'
                - config: 任务配置字典
                - airline: 可选，指定航空公司
            execute_immediately: 是否立即执行，默认True
            sequential: 是否按顺序执行，默认True（一个任务完成后执行下一个）
        
        Returns:
            创建的任务记录列表
        """
        created_tasks = []
        
        try:
            shanghai_tz = pytz.timezone('Asia/Shanghai')

            def _parse_dt(s):
                if not s:
                    return None
                try:
                    from datetime import datetime as dt
                    if isinstance(s, dt):
                        return s.astimezone(shanghai_tz).replace(tzinfo=None) if s.tzinfo else s
                    s = str(s).replace('Z', '+00:00').strip()
                    d = dt.fromisoformat(s)
                    return d.astimezone(shanghai_tz).replace(tzinfo=None) if d.tzinfo else shanghai_tz.localize(d).replace(tzinfo=None)
                except Exception:
                    return None

            for task_config in tasks:
                schedule_time = _parse_dt(task_config.get('schedule_time'))
                recurrence_end_at = _parse_dt(task_config.get('recurrence_end_at'))
                task_record = self.task_service.create_task_record(
                    task_name=task_config.get('task_name'),
                    task_type=task_config.get('task_type', 'flight_scraper'),
                    source=task_config.get('source', '12306'),
                    config=task_config.get('config'),
                    airline=task_config.get('airline'),
                    run_mode=task_config.get('run_mode', 'immediate'),
                    schedule_time=schedule_time,
                    recurrence_interval_hours=task_config.get('recurrence_interval_hours'),
                    recurrence_end_type=task_config.get('recurrence_end_type'),
                    recurrence_max_runs=task_config.get('recurrence_max_runs'),
                    recurrence_end_at=recurrence_end_at,
                    recurrence_run_index=1,
                )
                created_tasks.append(task_record)
                logger.info(f"任务已创建: {task_record.id} - {task_record.task_name}")
            
            # 如果需要立即执行
            if execute_immediately:
                if sequential:
                    # 全部先设为 waiting，再启动「当前可运行」的第一个（立即 或 已到时的定时/循环）
                    shanghai_tz = pytz.timezone('Asia/Shanghai')
                    now = datetime.now(shanghai_tz).replace(tzinfo=None)
                    for task in created_tasks:
                        task.status = 'waiting'
                        task.current_step = '排队等待中'
                        run_mode = getattr(task, 'run_mode', None) or 'immediate'
                        if run_mode in ('scheduled', 'recurring'):
                            task.current_step = '定时等待中' if run_mode == 'scheduled' else '循环等待中'
                    self.db.commit()
                    start_index = None
                    for i, task in enumerate(created_tasks):
                        run_mode = getattr(task, 'run_mode', None) or 'immediate'
                        st = getattr(task, 'schedule_time', None)
                        if run_mode == 'immediate' or (st is not None and st <= now):
                            start_index = i
                            task.status = 'running'
                            task.current_step = '等待执行'
                            self.db.commit()
                            break
                    if start_index is not None:
                        self._execute_sequential(created_tasks, start_index)
                else:
                    # 并行执行：所有任务同时启动，都设置为running
                    for task in created_tasks:
                        task.status = 'running'
                        task.current_step = '等待执行'
                    self.db.commit()
                    self._execute_parallel(created_tasks)
            else:
                # 不立即执行，所有任务设置为waiting状态
                for task in created_tasks:
                    task.status = 'waiting'
                    task.current_step = '等待执行'
                self.db.commit()
            
            return created_tasks
            
        except Exception as e:
            logger.error(f"批量创建任务失败: {e}", exc_info=True)
            raise e

    def _execute_sequential(self, tasks: List[TaskRecord], start_index: int = 0):
        """从 start_index 起执行一个任务；完成后由 run_task_and_continue 从 DB 中选下一个可运行任务。"""
        if not tasks or start_index >= len(tasks):
            return
        task = tasks[start_index]
        logger.info(f"开始执行任务 {start_index + 1}/{len(tasks)}: {task.task_name}")
        thread = threading.Thread(
            target=self.run_task_and_continue,
            args=(task.id,),
            daemon=True
        )
        thread.start()
        self.running_tasks[task.id] = thread

    def _execute_parallel(self, tasks: List[TaskRecord]):
        """并行执行所有任务"""
        for task in tasks:
            logger.info(f"启动并行任务: {task.task_name}")
            thread = threading.Thread(
                target=self._run_single_task,
                args=(task.id,),
                daemon=True
            )
            thread.start()
            self.running_tasks[task.id] = thread

    def _run_task_and_continue(
        self,
        task_id: int,
        task_list: List[TaskRecord],
        current_index: int
    ):
        """执行任务并在完成后继续下一个"""
        try:
            # 更新任务状态为running
            task = self.db.query(TaskRecord).filter(
                TaskRecord.id == task_id
            ).first()
            if task:
                if task.status == 'waiting':
                    task.status = 'running'
                    task.current_step = '正在执行'
                    import pytz
                    from datetime import datetime
                    shanghai_tz = pytz.timezone('Asia/Shanghai')
                    task.start_time = datetime.now(shanghai_tz).replace(tzinfo=None)
                    self.db.commit()
                    logger.info(f"🟢 任务 {task_id} 状态从waiting更新为running")
            
            logger.info(f"🟢 顺序执行：开始执行任务 {task_id} ({current_index + 1}/{len(task_list)})")
            
            # 执行任务（同步执行，_run_scraper_and_update 会等待子进程完成）
            self._run_single_task(task_id)
            
            # 由于 _run_scraper_and_update 是同步的，任务应该已经完成
            # 但为了确保状态已更新，再等待一小段时间并检查状态
            logger.info(f"🟡 任务 {task_id} 子进程已完成，等待状态更新...")
            time.sleep(1)  # 等待状态更新
            
            # 验证任务状态
            task = self.db.query(TaskRecord).filter(
                TaskRecord.id == task_id
            ).first()
            
            if task:
                logger.info(f"✅ 任务 {task_id} 执行完成，最终状态: {task.status}, 成功: {task.success}")
            else:
                logger.warning(f"⚠️ 任务 {task_id} 不存在")
            
            # 如果还有下一个任务，继续执行
            next_index = current_index + 1
            if next_index < len(task_list):
                next_task = task_list[next_index]
                # 确保下一个任务状态为waiting（如果还是waiting的话）
                next_task_db = self.db.query(TaskRecord).filter(
                    TaskRecord.id == next_task.id
                ).first()
                if next_task_db and next_task_db.status == 'waiting':
                    logger.info(f"🟢 任务 {task_id} 已完成，准备执行下一个任务: {next_task.task_name} (ID: {next_task.id})")
                    # 递归调用，继续执行下一个任务
                    self._run_task_and_continue(next_task.id, task_list, next_index)
                else:
                    logger.warning(f"⚠️ 下一个任务 {next_task.id} 状态不是waiting，跳过")
            else:
                logger.info(f"🎉 所有任务执行完成，共 {len(task_list)} 个任务")
                
        except Exception as e:
            logger.error(f"❌ 执行任务链失败: {e}", exc_info=True)

    def _run_single_task(self, task_id: int):
        """执行单个任务（同步执行，会等待任务完成）"""
        global _task_execution_lock, _current_executing_task_id, _lock_acquired_time
        
        # 使用全局锁确保同一时间只有一个任务在执行
        logger.info(f"🔵 任务 {task_id} 等待执行锁... (当前执行任务: {_current_executing_task_id})")
        
        try:
            with _task_execution_lock:
                _current_executing_task_id = task_id
                _lock_acquired_time = time.time()
                logger.info(f"🔵 任务 {task_id} 获得执行锁，开始执行（同步模式，将等待完成）")
                
                try:
                    # 确保任务状态为running
                    task = self.db.query(TaskRecord).filter(
                        TaskRecord.id == task_id).first()
                    if not task:
                        logger.error(f"❌ 任务 {task_id} 不存在")
                        return
                    
                    if task.status != 'running':
                        task.status = 'running'
                        task.current_step = '正在执行'
                        import pytz
                        from datetime import datetime
                        shanghai_tz = pytz.timezone('Asia/Shanghai')
                        if not task.start_time:
                            task.start_time = datetime.now(shanghai_tz).replace(tzinfo=None)
                        self.db.commit()
                        logger.info(f"🔵 任务 {task_id} 状态已更新为running")
                    
                    # 导入任务执行函数
                    import sys
                    import os
                    # 由当前文件位置得到 backend 根目录（__file__ 可能为相对路径，线程 cwd 可能为 /）
                    _cur_file = os.path.abspath(__file__)
                    backend_dir = os.path.dirname(os.path.dirname(_cur_file))
                    docker_main_path = os.path.join(backend_dir, 'docker_main.py')
                    # Docker 下 backend 根目录为 /app，若上面算出的是 / 或文件不存在则回退到 /app
                    if not os.path.isfile(docker_main_path) and os.path.isfile('/app/docker_main.py'):
                        backend_dir = '/app'
                        docker_main_path = '/app/docker_main.py'
                    
                    logger.info(f"🔵 查找 docker_main.py: {docker_main_path}, 存在: {os.path.exists(docker_main_path)}")
                    
                    if os.path.exists(docker_main_path):
                        import importlib.util
                        spec = importlib.util.spec_from_file_location(
                            "docker_main", docker_main_path)
                        docker_main = importlib.util.module_from_spec(spec)
                        sys.path.insert(0, backend_dir)
                        logger.info(f"🔵 加载 docker_main 模块...")
                        spec.loader.exec_module(docker_main)
                        _run_scraper_and_update = getattr(
                            docker_main, '_run_scraper_and_update', None)
                        
                        if _run_scraper_and_update:
                            logger.info(f"🔵 找到 _run_scraper_and_update 函数，准备执行任务 {task_id}")
                            # 获取任务配置
                            task = self.db.query(TaskRecord).filter(
                                TaskRecord.id == task_id).first()
                            if task:
                                logger.info(f"🔵 调用 _run_scraper_and_update 执行任务 {task_id}，将等待子进程完成...")
                                logger.info(f"🔵 任务配置: {task.config[:200] if task.config else 'None'}...")
                                # 同步调用，会等待子进程完成
                                _run_scraper_and_update(task_id, task.config)
                                logger.info(f"✅ 任务 {task_id} 执行完成（_run_scraper_and_update 已返回）")
                            else:
                                logger.error(f"❌ 任务 {task_id} 不存在（在获取配置时）")
                        else:
                            logger.error("❌ 未找到_run_scraper_and_update函数")
                            # 更新任务状态为failed
                            task = self.db.query(TaskRecord).filter(
                                TaskRecord.id == task_id).first()
                            if task:
                                task.status = 'failed'
                                task.current_step = '执行失败'
                                task.error_message = '未找到_run_scraper_and_update函数'
                                self.db.commit()
                    else:
                        logger.error(f"❌ 未找到docker_main.py: {docker_main_path}")
                        # 更新任务状态为failed
                        task = self.db.query(TaskRecord).filter(
                            TaskRecord.id == task_id).first()
                        if task:
                            task.status = 'failed'
                            task.current_step = '执行失败'
                            task.error_message = f'未找到docker_main.py: {docker_main_path}'
                            self.db.commit()
                        
                except Exception as e:
                    logger.error(f"❌ 执行任务 {task_id} 失败: {e}", exc_info=True)
                    # 更新任务状态为failed
                    try:
                        task = self.db.query(TaskRecord).filter(
                            TaskRecord.id == task_id).first()
                        if task:
                            task.status = 'failed'
                            task.current_step = '执行失败'
                            task.error_message = str(e)[:1000]
                            import pytz
                            from datetime import datetime
                            shanghai_tz = pytz.timezone('Asia/Shanghai')
                            task.end_time = datetime.now(shanghai_tz).replace(tzinfo=None)
                            self.db.commit()
                            logger.info(f"✅ 任务 {task_id} 状态已更新为failed")
                    except Exception as e2:
                        logger.error(f"❌ 更新任务状态失败: {e2}", exc_info=True)
                finally:
                    _current_executing_task_id = None
                    _lock_acquired_time = None
                    logger.info(f"🔵 任务 {task_id} 释放执行锁")
                    # 从运行列表中移除
                    if task_id in self.running_tasks:
                        del self.running_tasks[task_id]
        except Exception as e:
            logger.error(f"❌ 获取执行锁失败: {e}", exc_info=True)
            # 更新任务状态为failed
            try:
                task = self.db.query(TaskRecord).filter(
                    TaskRecord.id == task_id).first()
                if task:
                    task.status = 'failed'
                    task.current_step = '执行失败'
                    task.error_message = f'获取执行锁失败: {str(e)[:500]}'
                    self.db.commit()
            except Exception:
                pass

    def run_task_and_continue(self, task_id: int):
        """执行指定任务，完成后：若为循环任务则创建下次运行；再若有排队中或已到时的任务则启动下一个。"""
        self._run_single_task(task_id)
        shanghai_tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(shanghai_tz).replace(tzinfo=None)

        # 若刚完成的是循环任务且未到终止条件，创建下一次运行
        try:
            completed = self.db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
            if completed and getattr(completed, 'run_mode', None) == 'recurring':
                interval_h = getattr(completed, 'recurrence_interval_hours', None) or 0
                end_type = getattr(completed, 'recurrence_end_type', None)
                max_runs = getattr(completed, 'recurrence_max_runs', None) or 0
                end_at = getattr(completed, 'recurrence_end_at', None)
                run_index = getattr(completed, 'recurrence_run_index', None) or 1
                if interval_h and end_type:
                    next_run_index = run_index + 1
                    stop = False
                    if end_type == 'count' and max_runs and next_run_index > max_runs:
                        stop = True
                    if end_type == 'end_time' and end_at and now >= end_at:
                        stop = True
                    if not stop:
                        from datetime import timedelta
                        next_time = now + timedelta(hours=interval_h)
                        cfg = {}
                        if completed.config:
                            try:
                                cfg = json.loads(completed.config) if isinstance(completed.config, str) else (completed.config or {})
                            except Exception:
                                pass
                        next_task = self.task_service.create_task_record(
                            task_name=completed.task_name,
                            task_type=completed.task_type,
                            source=completed.source,
                            config=cfg,
                            airline=completed.airline,
                            run_mode='recurring',
                            schedule_time=next_time,
                            recurrence_interval_hours=interval_h,
                            recurrence_end_type=end_type,
                            recurrence_max_runs=max_runs,
                            recurrence_end_at=end_at,
                            recurrence_run_index=next_run_index,
                        )
                        next_task.status = 'waiting'
                        next_task.current_step = '循环等待中'
                        self.db.commit()
                        logger.info(f"🔄 已创建循环下一次运行: 任务 {next_task.id} 计划于 {next_time}")
        except Exception as e:
            logger.error(f"创建循环下次运行失败: {e}", exc_info=True)

        # 启动下一个：排队中且当前可运行（立即 或 已到时的定时/循环），优先立即任务
        try:
            from sqlalchemy import or_, and_, case
            run_mode_col = getattr(TaskRecord, 'run_mode', None)
            schedule_time_col = getattr(TaskRecord, 'schedule_time', None)
            if run_mode_col is not None and schedule_time_col is not None:
                q = self.db.query(TaskRecord).filter(
                    TaskRecord.status == 'waiting',
                    or_(
                        run_mode_col == 'immediate',
                        and_(run_mode_col.in_(['scheduled', 'recurring']), schedule_time_col <= now)
                    )
                )
                next_task = q.order_by(
                    case((run_mode_col == 'immediate', 0), else_=1),
                    schedule_time_col.asc().nullslast()
                ).first()
            else:
                next_task = self.db.query(TaskRecord).filter(
                    TaskRecord.status == 'waiting'
                ).order_by(TaskRecord.id).first()
            if next_task:
                next_id = next_task.id
                next_name = next_task.task_name
                next_task.status = 'running'
                next_task.current_step = '等待执行'
                if not next_task.start_time:
                    next_task.start_time = now
                self.db.commit()
                logger.info(f"🟢 启动下一个任务: {next_id} - {next_name}")
                t = threading.Thread(
                    target=self.run_task_and_continue,
                    args=(next_id,),
                    daemon=True,
                    name=f"Task-{next_id}"
                )
                t.start()
        except Exception as e:
            logger.error(f"启动下一个任务失败: {e}", exc_info=True)

    def get_running_tasks(self) -> List[int]:
        """获取正在运行的任务ID列表"""
        return list(self.running_tasks.keys())
    
    @staticmethod
    def get_current_executing_task() -> Optional[Dict[str, Any]]:
        """获取当前正在执行的任务ID（用于调试）"""
        global _current_executing_task_id, _lock_acquired_time
        if _current_executing_task_id and _lock_acquired_time:
            elapsed = time.time() - _lock_acquired_time
            return {
                'task_id': _current_executing_task_id,
                'elapsed_seconds': elapsed,
                'is_stuck': elapsed > 3600  # 超过1小时认为卡住
            }
        return None
