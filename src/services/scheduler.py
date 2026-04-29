import json
import os
from typing import List, Callable, Optional
from datetime import datetime
from PyQt5.QtCore import QTimer, QObject


class ScheduledTask:
    def __init__(self, task_id: str, name: str, interval_seconds: int, callback: Callable, enabled: bool = True):
        self.task_id = task_id
        self.name = name
        self.interval_seconds = interval_seconds
        self.callback = callback
        self.enabled = enabled
        self.last_run: Optional[str] = None
        self.run_count = 0


class SchedulerService(QObject):
    SCHEDULE_FILE = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "config",
        "scheduled_tasks.json"
    )

    def __init__(self):
        super().__init__()
        self.tasks: List[ScheduledTask] = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_tasks)
        self.timer.start(1000)
        self.load_tasks()

    def add_task(self, task: ScheduledTask):
        self.tasks.append(task)
        self.save_tasks()

    def remove_task(self, task_id: str):
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        self.save_tasks()

    def enable_task(self, task_id: str, enabled: bool):
        for task in self.tasks:
            if task.task_id == task_id:
                task.enabled = enabled
                self.save_tasks()
                break

    def get_tasks(self) -> List[ScheduledTask]:
        return self.tasks.copy()

    def check_tasks(self):
        now = datetime.now()
        for task in self.tasks:
            if not task.enabled:
                continue

            if task.last_run:
                last_run_time = datetime.fromisoformat(task.last_run)
                elapsed = (now - last_run_time).total_seconds()
                if elapsed >= task.interval_seconds:
                    self.run_task(task)
            else:
                self.run_task(task)

    def run_task(self, task: ScheduledTask):
        try:
            task.callback()
            task.last_run = datetime.now().isoformat()
            task.run_count += 1
            self.save_tasks()
        except Exception as e:
            print(f"Task {task.name} failed: {e}")

    def save_tasks(self):
        data = []
        for task in self.tasks:
            data.append({
                "task_id": task.task_id,
                "name": task.name,
                "interval_seconds": task.interval_seconds,
                "enabled": task.enabled,
                "last_run": task.last_run,
                "run_count": task.run_count
            })

        with open(self.SCHEDULE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_tasks(self):
        if not os.path.exists(self.SCHEDULE_FILE):
            return

        try:
            with open(self.SCHEDULE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    task = ScheduledTask(
                        task_id=item["task_id"],
                        name=item["name"],
                        interval_seconds=item["interval_seconds"],
                        callback=lambda: None,
                        enabled=item.get("enabled", True)
                    )
                    task.last_run = item.get("last_run")
                    task.run_count = item.get("run_count", 0)
                    self.tasks.append(task)
        except:
            pass
