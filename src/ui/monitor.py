from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QProgressBar, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer
from src.core.redis_manager import RedisManager


class MonitorWidget(QWidget):
    def __init__(self, redis_manager: RedisManager):
        super().__init__()
        self.redis_manager = redis_manager
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.update_monitor)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        controls = QHBoxLayout()
        self.btn_start_monitor = QPushButton("开始监控")
        self.btn_start_monitor.clicked.connect(self.toggle_monitoring)
        controls.addWidget(self.btn_start_monitor)

        self.interval_label = QLabel("间隔:")
        controls.addWidget(self.interval_label)

        self.lbl_status = QLabel("已停止")
        controls.addWidget(self.lbl_status)
        controls.addStretch()

        layout.addLayout(controls)

        info_group = QGroupBox("服务器信息")
        info_layout = QGridLayout()

        self.lbl_version = QLabel("版本: -")
        info_layout.addWidget(self.lbl_version, 0, 0)

        self.lbl_uptime = QLabel("运行时间: -")
        info_layout.addWidget(self.lbl_uptime, 0, 1)

        self.lbl_clients = QLabel("客户端: -")
        info_layout.addWidget(self.lbl_clients, 0, 2)

        self.lbl_ops = QLabel("操作/秒: -")
        info_layout.addWidget(self.lbl_ops, 1, 0)

        self.lbl_db_size = QLabel("键数量: -")
        info_layout.addWidget(self.lbl_db_size, 1, 1)

        self.lbl_hit_rate = QLabel("命中率: -")
        info_layout.addWidget(self.lbl_hit_rate, 1, 2)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        memory_group = QGroupBox("内存使用")
        memory_layout = QVBoxLayout()

        self.memory_progress = QProgressBar()
        self.memory_progress.setTextVisible(True)
        memory_layout.addWidget(self.memory_progress)

        mem_info_layout = QGridLayout()
        self.lbl_used_memory = QLabel("已使用: -")
        mem_info_layout.addWidget(self.lbl_used_memory, 0, 0)

        self.lbl_peak_memory = QLabel("峰值: -")
        mem_info_layout.addWidget(self.lbl_peak_memory, 0, 1)

        self.lbl_rss_memory = QLabel("RSS: -")
        mem_info_layout.addWidget(self.lbl_rss_memory, 1, 0)

        self.lbl_fragmentation = QLabel("碎片率: -")
        mem_info_layout.addWidget(self.lbl_fragmentation, 1, 1)

        memory_layout.addLayout(mem_info_layout)
        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)

        stats_group = QGroupBox("统计信息")
        stats_layout = QGridLayout()

        self.lbl_hits = QLabel("命中: -")
        stats_layout.addWidget(self.lbl_hits, 0, 0)

        self.lbl_misses = QLabel("未命中: -")
        stats_layout.addWidget(self.lbl_misses, 0, 1)

        self.lbl_evicted = QLabel("驱逐: -")
        stats_layout.addWidget(self.lbl_evicted, 1, 0)

        self.lbl_expired = QLabel("过期: -")
        stats_layout.addWidget(self.lbl_expired, 1, 1)

        self.lbl_connections = QLabel("总连接数: -")
        stats_layout.addWidget(self.lbl_connections, 2, 0)

        self.lbl_commands = QLabel("总命令数: -")
        stats_layout.addWidget(self.lbl_commands, 2, 1)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        layout.addStretch()

    def toggle_monitoring(self):
        if self.monitor_timer.isActive():
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        self.monitor_timer.start(2000)
        self.btn_start_monitor.setText("停止监控")
        self.lbl_status.setText("运行中")
        self.update_monitor()

    def stop_monitoring(self):
        self.monitor_timer.stop()
        self.btn_start_monitor.setText("开始监控")
        self.lbl_status.setText("已停止")

    def update_monitor(self):
        if not self.redis_manager.is_connected:
            return

        info = self.redis_manager.get_server_info()
        if not info:
            return

        self.lbl_version.setText(f"版本: {info.get('redis_version', '-')}")

        uptime = info.get("uptime_in_seconds", 0)
        if uptime > 86400:
            days = uptime // 86400
            hours = (uptime % 86400) // 3600
            self.lbl_uptime.setText(f"运行时间: {days}天 {hours}小时")
        elif uptime > 3600:
            hours = uptime // 3600
            minutes = (uptime % 3600) // 60
            self.lbl_uptime.setText(f"运行时间: {hours}小时 {minutes}分钟")
        else:
            minutes = uptime // 60
            seconds = uptime % 60
            self.lbl_uptime.setText(f"运行时间: {minutes}分钟 {seconds}秒")

        self.lbl_clients.setText(f"客户端: {info.get('connected_clients', 0)}")
        self.lbl_ops.setText(f"操作/秒: {info.get('instantaneous_ops_per_sec', 0)}")
        self.lbl_db_size.setText(f"键数量: {info.get('db_size', 0)}")

        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        if total > 0:
            hit_rate = (hits / total) * 100
            self.lbl_hit_rate.setText(f"命中率: {hit_rate:.2f}%")
        else:
            self.lbl_hit_rate.setText("命中率: 无数据")

        self.lbl_used_memory.setText(f"已使用: {info.get('used_memory_human', '-')}")
        self.lbl_peak_memory.setText(f"峰值: {info.get('used_memory_peak_human', '-')}")
        self.lbl_rss_memory.setText(f"RSS: {info.get('used_memory_rss_human', '-')}")
        self.lbl_fragmentation.setText(f"碎片率: {info.get('mem_fragmentation_ratio', 0)}")

        self.lbl_hits.setText(f"命中: {hits}")
        self.lbl_misses.setText(f"未命中: {misses}")
        self.lbl_evicted.setText(f"驱逐: {info.get('evicted_keys', 0)}")
        self.lbl_expired.setText(f"过期: {info.get('expired_keys', 0)}")
        self.lbl_connections.setText(f"总连接数: {info.get('total_connections_received', 0)}")
        self.lbl_commands.setText(f"总命令数: {info.get('total_commands_processed', 0)}")
