from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QSpinBox,
    QCheckBox, QComboBox, QMessageBox, QGroupBox,
    QDialogButtonBox
)
from PyQt5.QtCore import Qt
import uuid
from src.models.connection import ConnectionConfig


class ConnectionDialog(QDialog):
    def __init__(self, parent=None, config: ConnectionConfig = None):
        super().__init__(parent)
        self.config = config
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("添加连接" if not self.config else "编辑连接")
        self.setMinimumWidth(550)
        self.setMinimumHeight(500)
        self.resize(600, 550)
        self.setModal(True)

        layout = QVBoxLayout(self)

        form_group = QGroupBox("连接设置")
        form_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("我的 Redis 服务器")
        form_layout.addRow("名称:", self.name_edit)

        self.host_edit = QLineEdit()
        self.host_edit.setText("localhost")
        form_layout.addRow("主机:", self.host_edit)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(6379)
        form_layout.addRow("端口:", self.port_spin)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText("可选")
        form_layout.addRow("密码:", self.password_edit)

        self.db_spin = QSpinBox()
        self.db_spin.setRange(0, 15)
        form_layout.addRow("数据库:", self.db_spin)

        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText("可选 (Redis 6+)")
        form_layout.addRow("用户名:", self.username_edit)

        self.separator_edit = QLineEdit()
        self.separator_edit.setText(":")
        self.separator_edit.setMaxLength(1)
        form_layout.addRow("键分隔符:", self.separator_edit)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        ssl_group = QGroupBox("SSL 设置")
        ssl_layout = QVBoxLayout()

        self.ssl_checkbox = QCheckBox("启用 SSL")
        ssl_layout.addWidget(self.ssl_checkbox)

        form_layout2 = QFormLayout()
        self.ssl_cert_edit = QLineEdit()
        self.ssl_cert_edit.setPlaceholderText("SSL 证书路径")
        form_layout2.addRow("证书文件:", self.ssl_cert_edit)

        self.ssl_key_edit = QLineEdit()
        self.ssl_key_edit.setPlaceholderText("SSL 密钥路径")
        form_layout2.addRow("密钥文件:", self.ssl_key_edit)

        self.ssl_ca_edit = QLineEdit()
        self.ssl_ca_edit.setPlaceholderText("CA 证书路径")
        form_layout2.addRow("CA 文件:", self.ssl_ca_edit)

        ssl_layout.addLayout(form_layout2)
        ssl_group.setLayout(ssl_layout)
        layout.addWidget(ssl_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        test_btn = QPushButton("测试连接")
        test_btn.clicked.connect(self.test_connection)
        buttons.addButton(test_btn, QDialogButtonBox.ResetRole)

        layout.addWidget(buttons)

        if self.config:
            self.load_config()

    def load_config(self):
        self.name_edit.setText(self.config.name)
        self.host_edit.setText(self.config.host)
        self.port_spin.setValue(self.config.port)
        if self.config.password:
            self.password_edit.setText(self.config.password)
        self.db_spin.setValue(self.config.db)
        if self.config.username:
            self.username_edit.setText(self.config.username)
        self.separator_edit.setText(self.config.separator)
        self.ssl_checkbox.setChecked(self.config.ssl)
        if self.config.ssl_certfile:
            self.ssl_cert_edit.setText(self.config.ssl_certfile)
        if self.config.ssl_keyfile:
            self.ssl_key_edit.setText(self.config.ssl_keyfile)
        if self.config.ssl_ca_certs:
            self.ssl_ca_edit.setText(self.config.ssl_ca_certs)

    def get_config(self) -> ConnectionConfig:
        if self.config:
            self.config.name = self.name_edit.text() or "Redis Server"
            self.config.host = self.host_edit.text() or "localhost"
            self.config.port = self.port_spin.value()
            self.config.password = self.password_edit.text() or None
            self.config.db = self.db_spin.value()
            self.config.username = self.username_edit.text() or None
            self.config.separator = self.separator_edit.text() or ":"
            self.config.ssl = self.ssl_checkbox.isChecked()
            self.config.ssl_certfile = self.ssl_cert_edit.text() or None
            self.config.ssl_keyfile = self.ssl_key_edit.text() or None
            self.config.ssl_ca_certs = self.ssl_ca_edit.text() or None
            from datetime import datetime
            self.config.updated_at = datetime.now().isoformat()
            return self.config
        else:
            return ConnectionConfig(
                id=str(uuid.uuid4()),
                name=self.name_edit.text() or "Redis Server",
                host=self.host_edit.text() or "localhost",
                port=self.port_spin.value(),
                password=self.password_edit.text() or None,
                db=self.db_spin.value(),
                username=self.username_edit.text() or None,
                separator=self.separator_edit.text() or ":",
                ssl=self.ssl_checkbox.isChecked(),
                ssl_certfile=self.ssl_cert_edit.text() or None,
                ssl_keyfile=self.ssl_key_edit.text() or None,
                ssl_ca_certs=self.ssl_ca_edit.text() or None,
            )

    def test_connection(self):
        from src.core.redis_manager import RedisManager
        config = self.get_config()
        manager = RedisManager()
        success, message = manager.test_connection(config)

        if success:
            QMessageBox.information(self, "连接测试", f"成功: {message}")
        else:
            QMessageBox.critical(self, "连接测试", f"失败: {message}")
