from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QComboBox,
    QTextEdit, QMessageBox, QDialogButtonBox, QGroupBox, QTabWidget, QWidget
)
from PyQt5.QtCore import Qt
from src.core.redis_manager import RedisManager


class NewKeyDialog(QDialog):
    def __init__(self, parent=None, redis_manager: RedisManager = None):
        super().__init__(parent)
        self.redis_manager = redis_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("新建键")
        self.setMinimumWidth(700)
        self.setMinimumHeight(550)
        self.resize(750, 600)
        self.setModal(True)

        layout = QVBoxLayout(self)

        form_group = QGroupBox("键信息")
        form_layout = QFormLayout()

        self.key_name_edit = QLineEdit()
        self.key_name_edit.setPlaceholderText("例如: user:1001:name")
        form_layout.addRow("键名:", self.key_name_edit)

        self.key_type_combo = QComboBox()
        self.key_type_combo.addItem("String")
        self.key_type_combo.addItem("Hash")
        self.key_type_combo.addItem("List")
        self.key_type_combo.addItem("Set")
        self.key_type_combo.addItem("Zset")
        self.key_type_combo.currentIndexChanged.connect(self.on_combo_type_changed)
        form_layout.addRow("类型:", self.key_type_combo)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        self.tabs = QTabWidget()
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # String tab
        self.string_tab = QWidget()
        string_layout = QVBoxLayout(self.string_tab)
        self.string_value_edit = QTextEdit()
        self.string_value_edit.setPlaceholderText("输入字符串值...")
        string_layout.addWidget(self.string_value_edit)
        self.tabs.addTab(self.string_tab, "String")

        # Hash tab
        self.hash_tab = QWidget()
        hash_layout = QVBoxLayout(self.hash_tab)
        hash_info = QLabel("以 JSON 对象格式输入，例如: {\"name\": \"张三\", \"age\": 30}")
        hash_info.setWordWrap(True)
        hash_layout.addWidget(hash_info)
        self.hash_value_edit = QTextEdit()
        self.hash_value_edit.setPlaceholderText('{\n  "name": "张三",\n  "age": 30,\n  "email": "test@example.com"\n}')
        hash_layout.addWidget(self.hash_value_edit)
        self.tabs.addTab(self.hash_tab, "Hash")

        # List tab
        self.list_tab = QWidget()
        list_layout = QVBoxLayout(self.list_tab)
        list_info = QLabel("以 JSON 数组格式输入，例如: [\"item1\", \"item2\", \"item3\"]")
        list_info.setWordWrap(True)
        list_layout.addWidget(list_info)
        self.list_value_edit = QTextEdit()
        self.list_value_edit.setPlaceholderText('["item1", "item2", "item3"]')
        list_layout.addWidget(self.list_value_edit)
        self.tabs.addTab(self.list_tab, "List")

        # Set tab
        self.set_tab = QWidget()
        set_layout = QVBoxLayout(self.set_tab)
        set_info = QLabel("以 JSON 数组格式输入，例如: [\"member1\", \"member2\", \"member3\"]")
        set_info.setWordWrap(True)
        set_layout.addWidget(set_info)
        self.set_value_edit = QTextEdit()
        self.set_value_edit.setPlaceholderText('["member1", "member2", "member3"]')
        set_layout.addWidget(self.set_value_edit)
        self.tabs.addTab(self.set_tab, "Set")

        # Zset tab
        self.zset_tab = QWidget()
        zset_layout = QVBoxLayout(self.zset_tab)
        zset_info = QLabel("以 JSON 对象格式输入，键为成员，值为分数，例如: {\"member1\": 1.0, \"member2\": 2.0}")
        zset_info.setWordWrap(True)
        zset_layout.addWidget(zset_info)
        self.zset_value_edit = QTextEdit()
        self.zset_value_edit.setPlaceholderText('{\n  "member1": 1.0,\n  "member2": 2.0,\n  "member3": 3.0\n}')
        zset_layout.addWidget(self.zset_value_edit)
        self.tabs.addTab(self.zset_tab, "Zset")

        layout.addWidget(self.tabs)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.on_combo_type_changed()

    def on_combo_type_changed(self):
        type_name = self.key_type_combo.currentText()
        tab_map = {
            "String": 0,
            "Hash": 1,
            "List": 2,
            "Set": 3,
            "Zset": 4
        }
        self.tabs.setCurrentIndex(tab_map.get(type_name, 0))

    def on_tab_changed(self, index):
        type_map = {
            0: "String",
            1: "Hash",
            2: "List",
            3: "Set",
            4: "Zset"
        }
        type_name = type_map.get(index, "String")
        current = self.key_type_combo.currentText()
        if current != type_name:
            combo_index = self.key_type_combo.findText(type_name)
            if combo_index >= 0:
                self.key_type_combo.blockSignals(True)
                self.key_type_combo.setCurrentIndex(combo_index)
                self.key_type_combo.blockSignals(False)

    def get_key_data(self):
        key_name = self.key_name_edit.text().strip()
        key_type = self.key_type_combo.currentText().lower()
        
        value = ""
        if key_type == "string":
            value = self.string_value_edit.toPlainText()
        elif key_type == "hash":
            value = self.hash_value_edit.toPlainText()
        elif key_type == "list":
            value = self.list_value_edit.toPlainText()
        elif key_type == "set":
            value = self.set_value_edit.toPlainText()
        elif key_type == "zset":
            value = self.zset_value_edit.toPlainText()
        
        return key_name, key_type, value

    def validate_data(self):
        import json
        key_name, key_type, value = self.get_key_data()
        
        if not key_name:
            QMessageBox.warning(self, "验证失败", "键名不能为空")
            return False, "键名不能为空"
        
        if not value.strip():
            QMessageBox.warning(self, "验证失败", "值不能为空")
            return False, "值不能为空"
        
        if key_type == "hash":
            try:
                data = json.loads(value)
                if not isinstance(data, dict):
                    QMessageBox.warning(self, "验证失败", "Hash 值必须是 JSON 对象格式")
                    return False, "Hash 值必须是 JSON 对象格式"
            except json.JSONDecodeError as e:
                QMessageBox.warning(self, "验证失败", f"Hash 格式错误: JSON 解析失败 - {str(e)}")
                return False, f"Hash 格式错误: JSON 解析失败 - {str(e)}"
        
        elif key_type == "list":
            try:
                data = json.loads(value)
                if not isinstance(data, list):
                    QMessageBox.warning(self, "验证失败", "List 值必须是 JSON 数组格式")
                    return False, "List 值必须是 JSON 数组格式"
            except json.JSONDecodeError as e:
                QMessageBox.warning(self, "验证失败", f"List 格式错误: JSON 解析失败 - {str(e)}")
                return False, f"List 格式错误: JSON 解析失败 - {str(e)}"
        
        elif key_type == "set":
            try:
                data = json.loads(value)
                if not isinstance(data, list):
                    QMessageBox.warning(self, "验证失败", "Set 值必须是 JSON 数组格式")
                    return False, "Set 值必须是 JSON 数组格式"
            except json.JSONDecodeError as e:
                QMessageBox.warning(self, "验证失败", f"Set 格式错误: JSON 解析失败 - {str(e)}")
                return False, f"Set 格式错误: JSON 解析失败 - {str(e)}"
        
        elif key_type == "zset":
            try:
                data = json.loads(value)
                if not isinstance(data, dict):
                    QMessageBox.warning(self, "验证失败", "Zset 值必须是 JSON 对象格式")
                    return False, "Zset 值必须是 JSON 对象格式"
                for member, score in data.items():
                    try:
                        float(score)
                    except (ValueError, TypeError):
                        QMessageBox.warning(self, "验证失败", f"Zset 格式错误: 成员 '{member}' 的分数必须是数字")
                        return False, f"Zset 格式错误: 成员 '{member}' 的分数必须是数字"
            except json.JSONDecodeError as e:
                QMessageBox.warning(self, "验证失败", f"Zset 格式错误: JSON 解析失败 - {str(e)}")
                return False, f"Zset 格式错误: JSON 解析失败 - {str(e)}"
        
        return True, ""

    def accept(self):
        valid, message = self.validate_data()
        if valid:
            super().accept()
