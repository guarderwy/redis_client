from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from src.core.redis_manager import RedisManager


class ConsoleWidget(QWidget):
    def __init__(self, redis_manager: RedisManager):
        super().__init__()
        self.redis_manager = redis_manager
        self.command_history = []
        self.history_index = -1
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        info_label = QLabel("Redis 控制台 - 直接输入命令（例如：GET key, SET key value）")
        layout.addWidget(info_label)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 10))
        layout.addWidget(self.output)

        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel(">"))

        self.command_input = QLineEdit()
        self.command_input.setFont(QFont("Consolas", 10))
        self.command_input.returnPressed.connect(self.execute_command)
        self.command_input.installEventFilter(self)
        input_layout.addWidget(self.command_input)

        btn_execute = QPushButton("执行")
        btn_execute.clicked.connect(self.execute_command)
        input_layout.addWidget(btn_execute)

        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self.clear_output)
        input_layout.addWidget(btn_clear)

        layout.addLayout(input_layout)

    def execute_command(self):
        command = self.command_input.text().strip()
        if not command:
            return

        self.command_history.append(command)
        self.history_index = len(self.command_history)

        self.output.append(f"<span style='color: #569cd6;'>{command}</span>")

        if not self.redis_manager.is_connected:
            self.output.append("<span style='color: #f44747;'>未连接到 Redis 服务器</span>")
            return

        result, duration, success = self.redis_manager.execute_command(command)

        if success:
            result_str = self.format_result(result)
            self.output.append(f"<span style='color: #4ec9b0;'>{result_str}</span>")
        else:
            self.output.append(f"<span style='color: #f44747;'>(error) {result}</span>")

        self.output.append(f"<span style='color: #808080;'>({duration:.2f}ms)</span>")
        self.output.append("")

        self.command_input.clear()

    def format_result(self, result) -> str:
        if result is None:
            return "(nil)"
        elif isinstance(result, bytes):
            return result.decode("utf-8", errors="replace")
        elif isinstance(result, (list, tuple)):
            lines = []
            for i, item in enumerate(result):
                lines.append(f"{i+1}) {self.format_result(item)}")
            return "\n".join(lines)
        elif isinstance(result, dict):
            lines = []
            for key, value in result.items():
                lines.append(f"{key}: {self.format_result(value)}")
            return "\n".join(lines)
        elif isinstance(result, bool):
            return "1" if result else "0"
        else:
            return str(result)

    def clear_output(self):
        self.output.clear()

    def eventFilter(self, obj, event):
        if obj == self.command_input and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Up:
                if self.history_index > 0:
                    self.history_index -= 1
                    self.command_input.setText(self.command_history[self.history_index])
                return True
            elif event.key() == Qt.Key_Down:
                if self.history_index < len(self.command_history) - 1:
                    self.history_index += 1
                    self.command_input.setText(self.command_history[self.history_index])
                else:
                    self.history_index = len(self.command_history)
                    self.command_input.clear()
                return True
        return super().eventFilter(obj, event)
