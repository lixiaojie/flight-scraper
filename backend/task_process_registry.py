"""按 task_id 登记运行中的抓取子进程，供取消时终止。"""
import threading
from typing import Dict, Optional
import subprocess

_processes: Dict[int, subprocess.Popen] = {}
_lock = threading.Lock()


def register(task_id: int, proc: subprocess.Popen) -> None:
    with _lock:
        _processes[task_id] = proc


def unregister(task_id: int) -> None:
    with _lock:
        _processes.pop(task_id, None)


def cancel_task(task_id: int) -> bool:
    """终止该任务对应的子进程（若存在），返回是否曾登记并已终止。"""
    with _lock:
        proc = _processes.get(task_id)
        if not proc:
            return False
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        _processes.pop(task_id, None)
        return True
