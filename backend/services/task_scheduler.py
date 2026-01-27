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
            for task_config in tasks:
                task_record = self.task_service.create_task_record(
                    task_name=task_config.get('task_name'),
                    task_type=task_config.get('task_type', 'flight_scraper'),
                    source=task_config.get('source', '12306'),
                    config=task_config.get('config'),
                    airline=task_config.get('airline')
                )
                created_tasks.append(task_record)
                logger.info(f"任务已创建: {task_record.id} - {task_record.task_name}")
            
            # 如果需要立即执行
            if execute_immediately:
                if sequential:
                    # 按顺序执行：第一个任务立即执行，后续任务等待前一个完成
                    self._execute_sequential(created_tasks)
                else:
                    # 并行执行：所有任务同时启动
                    self._execute_parallel(created_tasks)
            
            return created_tasks
            
        except Exception as e:
            logger.error(f"批量创建任务失败: {e}", exc_info=True)
            raise e

    def _execute_sequential(self, tasks: List[TaskRecord]):
        """按顺序执行任务"""
        if not tasks:
            return
        
        def execute_task_chain(task_list: List[TaskRecord], index: int = 0):
            """递归执行任务链"""
            if index >= len(task_list):
                return
            
            task = task_list[index]
            logger.info(f"开始执行任务 {index + 1}/{len(task_list)}: {task.task_name}")
            
            # 执行当前任务
            thread = threading.Thread(
                target=self._run_task_and_continue,
                args=(task.id, task_list, index),
                daemon=True
            )
            thread.start()
            self.running_tasks[task.id] = thread
        
        # 启动第一个任务
        execute_task_chain(tasks, 0)

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
            # 执行任务
            self._run_single_task(task_id)
            
            # 如果还有下一个任务，继续执行
            next_index = current_index + 1
            if next_index < len(task_list):
                next_task = task_list[next_index]
                logger.info(f"任务 {task_id} 完成，开始执行下一个任务: {next_task.task_name}")
                self._run_task_and_continue(next_task.id, task_list, next_index)
            else:
                logger.info(f"所有任务执行完成，共 {len(task_list)} 个任务")
                
        except Exception as e:
            logger.error(f"执行任务链失败: {e}", exc_info=True)

    def _run_single_task(self, task_id: int):
        """执行单个任务"""
        try:
            # 导入任务执行函数
            import sys
            import os
            backend_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(__file__)))
            docker_main_path = os.path.join(backend_dir, 'docker_main.py')
            
            if os.path.exists(docker_main_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "docker_main", docker_main_path)
                docker_main = importlib.util.module_from_spec(spec)
                sys.path.insert(0, backend_dir)
                spec.loader.exec_module(docker_main)
                _run_scraper_and_update = getattr(
                    docker_main, '_run_scraper_and_update', None)
                
                if _run_scraper_and_update:
                    # 获取任务配置
                    task = self.db.query(TaskRecord).filter(
                        TaskRecord.id == task_id).first()
                    if task:
                        _run_scraper_and_update(task_id, task.config)
                    else:
                        logger.error(f"任务 {task_id} 不存在")
                else:
                    logger.error("未找到_run_scraper_and_update函数")
            else:
                logger.error(f"未找到docker_main.py: {docker_main_path}")
                
        except Exception as e:
            logger.error(f"执行任务 {task_id} 失败: {e}", exc_info=True)
        finally:
            # 从运行列表中移除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]

    def get_running_tasks(self) -> List[int]:
        """获取正在运行的任务ID列表"""
        return list(self.running_tasks.keys())
