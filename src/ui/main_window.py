from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QLabel,
    QPushButton, QComboBox, QGroupBox, QTextEdit,
    QMessageBox, QMenu, QAction, QProgressBar,
    QToolBar, QStatusBar, QTabWidget, QSpinBox,
    QAbstractItemView, QApplication, QInputDialog,
    QMenuBar, QFileDialog, QShortcut, QDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QFont, QColor, QKeySequence, QPixmap, QPainter
import time
from src.core.redis_manager import RedisManager
from src.core.config_manager import ConfigManager
from src.models.connection import ConnectionConfig
from src.models.key_data import KeyInfo, KeyValue, CommandHistory
from src.utils.formatters import DataFormatter
from src.utils.validators import DataValidator
from src.ui.connection_dialog import ConnectionDialog
from src.ui.new_key_dialog import NewKeyDialog
from src.services.backup_service import BackupService
from src.services.import_export import ImportExportService


class LoadKeysThread(QThread):
    finished = pyqtSignal(list, int)
    progress = pyqtSignal(int)

    def __init__(self, manager: RedisManager, pattern: str, page: int, page_size: int, key_type: str = None):
        super().__init__()
        self.manager = manager
        self.pattern = pattern
        self.page = page
        self.page_size = page_size
        self.key_type = key_type

    def run(self):
        keys = self.manager.get_keys(self.pattern, self.page, self.page_size, self.key_type)
        total = self.manager.get_key_count(self.pattern, self.key_type)
        self.finished.emit(keys, total)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.redis_manager = RedisManager()
        self.config_manager = ConfigManager()
        self.backup_service = BackupService()
        self.import_export_service = ImportExportService()
        self.current_page = 0
        self.page_size = 100
        self.current_pattern = "*"
        self.command_history: list[CommandHistory] = []
        self.operation_log: list[str] = []
        self.pending_select_key: str = None
        self.init_ui()
        self.load_connections()
        self.setup_shortcuts()

    def init_ui(self):
        self.setWindowTitle("Redis 桌面客户端")
        self.setMinimumSize(1200, 800)

        main_layout = QVBoxLayout(self)

        menubar = self.create_menubar()
        main_layout.setMenuBar(menubar)

        toolbar = self.create_toolbar()
        main_layout.addWidget(toolbar)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = self.create_left_panel()
        self.data_editor = self.create_data_editor_tab()
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.addWidget(self.data_editor)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        self.operation_log_widget = self.create_operation_log_widget()
        main_layout.addWidget(self.operation_log_widget)

        self.setStyleSheet(self.get_light_theme())

    def create_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextOnly)

        self.connection_combo = QComboBox()
        self.connection_combo.setMinimumWidth(200)
        self.connection_combo.currentIndexChanged.connect(self.on_connection_changed)
        toolbar.addWidget(self.connection_combo)

        self.status_indicator = QLabel()
        self.status_indicator.setFixedSize(12, 12)
        self.status_indicator.setStyleSheet("background-color: #FF4444; border-radius: 6px;")
        toolbar.addWidget(self.status_indicator)

        btn_add_conn = QPushButton("添加")
        btn_add_conn.clicked.connect(self.add_connection)
        toolbar.addWidget(btn_add_conn)

        btn_edit_conn = QPushButton("编辑")
        btn_edit_conn.clicked.connect(self.edit_connection)
        toolbar.addWidget(btn_edit_conn)

        btn_delete_conn = QPushButton("删除")
        btn_delete_conn.clicked.connect(self.delete_connection)
        toolbar.addWidget(btn_delete_conn)

        toolbar.addSeparator()

        btn_connect = QPushButton("连接")
        btn_connect.clicked.connect(self.connect_to_redis)
        toolbar.addWidget(btn_connect)

        btn_disconnect = QPushButton("断开")
        btn_disconnect.clicked.connect(self.disconnect_from_redis)
        toolbar.addWidget(btn_disconnect)

        toolbar.addSeparator()

        btn_refresh = QPushButton("刷新")
        btn_refresh.clicked.connect(self.refresh_keys)
        toolbar.addWidget(btn_refresh)

        return toolbar

    def create_left_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        search_layout = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("搜索键名（使用 * 作为通配符）...")
        self.search_edit.returnPressed.connect(self.search_keys)
        search_layout.addWidget(self.search_edit)

        btn_search = QPushButton("搜索")
        btn_search.clicked.connect(self.search_keys)
        search_layout.addWidget(btn_search)

        layout.addLayout(search_layout)

        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(5)
        
        type_label = QLabel("类型:")
        type_label.setFixedWidth(40)
        filter_layout.addWidget(type_label)
        
        self.type_filter = QComboBox()
        self.type_filter.addItem("All Types")
        self.type_filter.addItem("String")
        self.type_filter.addItem("Hash")
        self.type_filter.addItem("List")
        self.type_filter.addItem("Set")
        self.type_filter.addItem("Zset")
        self.type_filter.currentIndexChanged.connect(self.on_type_filter_changed)
        filter_layout.addWidget(self.type_filter)

        ttl_label = QLabel("TTL:")
        ttl_label.setFixedWidth(40)
        filter_layout.addWidget(ttl_label)
        
        self.ttl_filter = QComboBox()
        self.ttl_filter.addItem("所有 TTL")
        self.ttl_filter.addItem("无过期")
        self.ttl_filter.addItem("有过期")
        self.ttl_filter.currentIndexChanged.connect(self.refresh_keys)
        filter_layout.addWidget(self.ttl_filter)
        
        filter_layout.addStretch()

        layout.addLayout(filter_layout)

        self.key_tree = QTreeWidget()
        self.key_tree.setHeaderLabels(["键名", "类型", "TTL"])
        self.key_tree.setColumnWidth(0, 250)
        self.key_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.key_tree.itemClicked.connect(self.on_key_selected)
        self.key_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.key_tree.customContextMenuRequested.connect(self.show_key_context_menu)
        self.key_tree.setStyleSheet("""
            QTreeWidget {
                font-size: 12px;
                border: 1px solid #D0D5DD;
                border-radius: 4px;
                background-color: #FFFFFF;
            }
            QTreeWidget::item {
                padding: 3px 4px;
                border-bottom: 1px solid #F5F5F5;
            }
            QTreeWidget::item:selected {
                background-color: #D6E4F0;
                color: #1A1A1A;
                border-radius: 4px;
            }
            QTreeWidget::item:hover {
                background-color: #EEF2F7;
                border-radius: 4px;
            }
            QTreeWidget::branch {
                background: transparent;
            }
            QHeaderView::section {
                background-color: #E8EBF0;
                color: #333333;
                padding: 5px 4px;
                border: none;
                border-bottom: 1px solid #D0D5DD;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.key_tree)

        pagination_layout = QHBoxLayout()
        self.btn_prev = QPushButton("上一页")
        self.btn_prev.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.btn_prev)

        self.page_label = QLabel("第 1 页")
        pagination_layout.addWidget(self.page_label)

        self.btn_next = QPushButton("下一页")
        self.btn_next.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.btn_next)

        pagination_layout.addStretch()
        pagination_layout.addWidget(QLabel("每页:"))

        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(["50", "100", "200", "500"])
        self.page_size_combo.setCurrentText("100")
        self.page_size_combo.currentIndexChanged.connect(self.on_page_size_changed)
        pagination_layout.addWidget(self.page_size_combo)

        self.total_label = QLabel("总计: 0")
        pagination_layout.addWidget(self.total_label)

        layout.addLayout(pagination_layout)

        return panel

    def create_data_editor_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_layout = QHBoxLayout()
        self.key_name_label = QLabel("键名: ")
        self.key_name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        info_layout.addWidget(self.key_name_label)

        self.key_type_label = QLabel("类型: ")
        self.key_type_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        info_layout.addWidget(self.key_type_label)

        self.ttl_label = QLabel("TTL: ")
        self.ttl_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        info_layout.addWidget(self.ttl_label)

        info_layout.addStretch()

        btn_new_key = QPushButton("新建")
        btn_new_key.clicked.connect(self.create_new_key)
        info_layout.addWidget(btn_new_key)

        btn_delete_key = QPushButton("删除")
        btn_delete_key.clicked.connect(self.delete_selected_key)
        info_layout.addWidget(btn_delete_key)

        btn_rename_key = QPushButton("重命名")
        btn_rename_key.clicked.connect(self.rename_selected_key)
        info_layout.addWidget(btn_rename_key)

        btn_refresh_key = QPushButton("刷新")
        btn_refresh_key.clicked.connect(self.refresh_selected_key)
        info_layout.addWidget(btn_refresh_key)

        layout.addLayout(info_layout)

        self.value_editor = QTextEdit()
        self.value_editor.setFont(QFont("Consolas", 10))
        self.value_editor.setPlaceholderText("选择一个键以查看/编辑其值...")
        layout.addWidget(self.value_editor, stretch=1)

        # 将编辑器按钮区域和TTL编辑区域合并到一个小的控件中，减少空间占用
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        
        editor_buttons = QHBoxLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItem("自动检测")
        self.format_combo.addItem("JSON")
        self.format_combo.addItem("XML")
        self.format_combo.addItem("文本")
        self.format_combo.currentIndexChanged.connect(self.reformat_value)
        editor_buttons.addWidget(QLabel("格式:"))
        editor_buttons.addWidget(self.format_combo)

        editor_buttons.addStretch()

        btn_validate = QPushButton("验证")
        btn_validate.clicked.connect(self.validate_value)
        editor_buttons.addWidget(btn_validate)

        btn_format = QPushButton("格式化")
        btn_format.clicked.connect(self.format_value)
        editor_buttons.addWidget(btn_format)

        btn_save = QPushButton("保存")
        btn_save.clicked.connect(self.save_value)
        editor_buttons.addWidget(btn_save)

        bottom_layout.addLayout(editor_buttons)

        self.ttl_editor_layout = QHBoxLayout()
        self.ttl_editor_layout.addWidget(QLabel("TTL (秒):"))
        self.ttl_spin = QSpinBox()
        self.ttl_spin.setRange(-1, 999999999)
        self.ttl_spin.setValue(-1)
        self.ttl_spin.setSpecialValueText("永不过期")
        self.ttl_editor_layout.addWidget(self.ttl_spin)

        btn_set_ttl = QPushButton("设置 TTL")
        btn_set_ttl.clicked.connect(self.set_key_ttl)
        self.ttl_editor_layout.addWidget(btn_set_ttl)

        bottom_layout.addLayout(self.ttl_editor_layout)
        
        # 设置底部控件的高度
        bottom_widget.setMaximumHeight(80)
        
        layout.addWidget(bottom_widget)

        return widget

    def get_light_theme(self):
        return """
        QMainWindow, QWidget {
            background-color: #F5F7FA;
            color: #333333;
        }
        QToolBar {
            background-color: #E8EBF0;
            border: none;
            padding: 5px;
            spacing: 5px;
        }
        QPushButton {
            background-color: #4A90D9;
            color: white;
            border: none;
            padding: 5px 15px;
            border-radius: 4px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #5BA0E9;
        }
        QPushButton:pressed {
            background-color: #3A80C9;
        }
        QLineEdit, QTextEdit, QSpinBox, QComboBox {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #D0D5DD;
            padding: 5px;
            border-radius: 4px;
            font-size: 14px;
        }
        QTextEdit {
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 15px;
        }
        QLineEdit:focus, QTextEdit:focus {
            border: 1px solid #4A90D9;
        }
        QTreeWidget, QTableWidget {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #D0D5DD;
            gridline-color: #E8EBF0;
            alternate-background-color: #F9FAFB;
            font-size: 14px;
            outline: none;
        }
        QTreeWidget::item {
            padding: 4px 2px;
            border-bottom: 1px solid #F0F0F0;
        }
        QTreeWidget::item:selected {
            background-color: #D6E4F0;
            color: #333333;
            border-radius: 3px;
        }
        QTreeWidget::item:hover {
            background-color: #E8EBF0;
            border-radius: 3px;
        }
        QTreeWidget::branch {
            background: transparent;
        }
        QHeaderView::section {
            background-color: #E8EBF0;
            color: #333333;
            padding: 5px;
            border: 1px solid #D0D5DD;
            font-weight: bold;
        }
        QTabWidget::pane {
            border: 1px solid #D0D5DD;
            background-color: #FFFFFF;
            border-radius: 4px;
        }
        QTabBar::tab {
            background-color: #E8EBF0;
            color: #333333;
            padding: 8px 15px;
            border: 1px solid #D0D5DD;
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            margin-right: 2px;
        }
        QTabBar::tab:selected {
            background-color: #FFFFFF;
            border-bottom: 2px solid #4A90D9;
            font-weight: bold;
        }
        QTabBar::tab:hover:!selected {
            background-color: #F0F2F5;
        }
        QGroupBox {
            border: 1px solid #D0D5DD;
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 10px;
            font-weight: bold;
            background-color: #FAFBFC;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
            color: #4A90D9;
        }
        QStatusBar {
            background-color: #4A90D9;
            color: white;
        }
        QMenuBar {
            background-color: #E8EBF0;
            color: #333333;
            border-bottom: 1px solid #D0D5DD;
        }
        QMenuBar::item:selected {
            background-color: #D6E4F0;
            border-radius: 4px;
        }
        QMenu {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #D0D5DD;
            border-radius: 4px;
            padding: 5px;
        }
        QMenu::item:selected {
            background-color: #D6E4F0;
            border-radius: 4px;
        }
        QMenu::separator {
            height: 1px;
            background-color: #E8EBF0;
            margin: 5px 10px;
        }
        QProgressBar {
            border: 1px solid #D0D5DD;
            border-radius: 4px;
            text-align: center;
            background-color: #E8EBF0;
        }
        QProgressBar::chunk {
            background-color: #4A90D9;
            border-radius: 3px;
        }
        QLabel {
            color: #333333;
            font-size: 13px;
        }
        QSplitter::handle {
            background-color: #D0D5DD;
        }
        QSplitter::handle:hover {
            background-color: #4A90D9;
        }
        /* Console styling */
        #ConsoleWidget {
            background-color: #2B2B2B;
        }
        #ConsoleWidget QLabel {
            color: #D4D4D4;
        }
        #ConsoleWidget QTextEdit {
            background-color: #1E1E1E;
            color: #D4D4D4;
            border: 1px solid #3C3C3C;
        }
        #ConsoleWidget QLineEdit {
            background-color: #3C3C3C;
            color: #D4D4D4;
            border: 1px solid #555555;
        }
        #ConsoleWidget QPushButton {
            background-color: #0E639C;
            color: white;
            border: none;
            padding: 5px 15px;
            border-radius: 4px;
        }
        #ConsoleWidget QPushButton:hover {
            background-color: #1177BB;
        }
        """

    def create_menubar(self):
        menubar = QMenuBar()

        file_menu = menubar.addMenu("文件(&F)")

        action_add_conn = QAction("添加连接(&A)", self)
        action_add_conn.setShortcut("Ctrl+N")
        action_add_conn.triggered.connect(self.add_connection)
        file_menu.addAction(action_add_conn)

        action_edit_conn = QAction("编辑连接(&E)", self)
        action_edit_conn.setShortcut("Ctrl+E")
        action_edit_conn.triggered.connect(self.edit_connection)
        file_menu.addAction(action_edit_conn)

        action_delete_conn = QAction("删除连接(&D)", self)
        action_delete_conn.setShortcut("Ctrl+D")
        action_delete_conn.triggered.connect(self.delete_connection)
        file_menu.addAction(action_delete_conn)

        file_menu.addSeparator()

        action_connect = QAction("连接(&C)", self)
        action_connect.setShortcut("Ctrl+Shift+C")
        action_connect.triggered.connect(self.connect_to_redis)
        file_menu.addAction(action_connect)

        action_disconnect = QAction("断开连接(&I)", self)
        action_disconnect.setShortcut("Ctrl+Shift+D")
        action_disconnect.triggered.connect(self.disconnect_from_redis)
        file_menu.addAction(action_disconnect)

        file_menu.addSeparator()

        action_export_json = QAction("导出为 JSON(&J)", self)
        action_export_json.triggered.connect(self.export_to_json)
        file_menu.addAction(action_export_json)

        action_export_csv = QAction("导出为 CSV(&C)", self)
        action_export_csv.triggered.connect(self.export_to_csv)
        file_menu.addAction(action_export_csv)

        action_import_json = QAction("从 JSON 导入(&N)", self)
        action_import_json.triggered.connect(self.import_from_json)
        file_menu.addAction(action_import_json)

        action_import_csv = QAction("从 CSV 导入(&S)", self)
        action_import_csv.triggered.connect(self.import_from_csv)
        file_menu.addAction(action_import_csv)

        file_menu.addSeparator()

        action_backup = QAction("备份数据库(&B)", self)
        action_backup.triggered.connect(self.backup_database)
        file_menu.addAction(action_backup)

        action_restore = QAction("恢复数据库(&R)", self)
        action_restore.triggered.connect(self.restore_database)
        file_menu.addAction(action_restore)

        file_menu.addSeparator()

        action_exit = QAction("退出(&X)", self)
        action_exit.setShortcut("Alt+F4")
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)

        edit_menu = menubar.addMenu("编辑(&E)")

        action_refresh = QAction("刷新(&R)", self)
        action_refresh.setShortcut("Ctrl+R")
        action_refresh.triggered.connect(self.refresh_keys)
        edit_menu.addAction(action_refresh)

        action_search = QAction("搜索(&S)", self)
        action_search.setShortcut("Ctrl+F")
        action_search.triggered.connect(lambda: self.search_edit.setFocus())
        edit_menu.addAction(action_search)

        edit_menu.addSeparator()

        action_delete_key = QAction("删除键(&D)", self)
        action_delete_key.setShortcut("Delete")
        action_delete_key.triggered.connect(self.delete_selected_key)
        edit_menu.addAction(action_delete_key)

        action_rename_key = QAction("重命名键(&N)", self)
        action_rename_key.setShortcut("F2")
        action_rename_key.triggered.connect(self.rename_selected_key)
        edit_menu.addAction(action_rename_key)

        action_new_key = QAction("新建键(&K)", self)
        action_new_key.setShortcut("Ctrl+K")
        action_new_key.triggered.connect(self.create_new_key)
        edit_menu.addAction(action_new_key)

        view_menu = menubar.addMenu("视图(&V)")

        action_toggle_console = QAction("切换控制台(&C)", self)
        action_toggle_console.setShortcut("Ctrl+`")
        action_toggle_console.triggered.connect(self.toggle_console)
        view_menu.addAction(action_toggle_console)

        help_menu = menubar.addMenu("帮助(&H)")

        action_about = QAction("关于(&A)", self)
        action_about.triggered.connect(self.show_about)
        help_menu.addAction(action_about)

        return menubar

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.refresh_keys)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(lambda: self.search_edit.setFocus())
        QShortcut(QKeySequence("Delete"), self).activated.connect(self.delete_selected_key)
        QShortcut(QKeySequence("F2"), self).activated.connect(self.rename_selected_key)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.refresh_keys)

    def export_to_json(self):
        if not self.redis_manager.is_connected:
            QMessageBox.warning(self, "警告", "未连接到 Redis 服务器")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "导出为 JSON", "", "JSON 文件 (*.json)")
        if filepath:
            if self.import_export_service.export_to_json(self.redis_manager, filepath, self.current_pattern):
                self.add_operation_log(f"已导出到 {filepath}")
            else:
                QMessageBox.critical(self, "错误", "导出失败")

    def export_to_csv(self):
        if not self.redis_manager.is_connected:
            QMessageBox.warning(self, "警告", "未连接到 Redis 服务器")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "导出为 CSV", "", "CSV 文件 (*.csv)")
        if filepath:
            if self.import_export_service.export_to_csv(self.redis_manager, filepath, self.current_pattern):
                self.add_operation_log(f"已导出到 {filepath}")
            else:
                QMessageBox.critical(self, "错误", "导出失败")

    def import_from_json(self):
        if not self.redis_manager.is_connected:
            QMessageBox.warning(self, "警告", "未连接到 Redis 服务器")
            return

        filepath, _ = QFileDialog.getOpenFileName(self, "从 JSON 导入", "", "JSON 文件 (*.json)")
        if filepath:
            success, count = self.import_export_service.import_from_json(self.redis_manager, filepath)
            if success:
                self.add_operation_log(f"已导入 {count} 个键")
                self.refresh_keys()
            else:
                QMessageBox.critical(self, "错误", "导入失败")

    def import_from_csv(self):
        if not self.redis_manager.is_connected:
            QMessageBox.warning(self, "警告", "未连接到 Redis 服务器")
            return

        filepath, _ = QFileDialog.getOpenFileName(self, "从 CSV 导入", "", "CSV 文件 (*.csv)")
        if filepath:
            success, count = self.import_export_service.import_from_csv(self.redis_manager, filepath)
            if success:
                self.add_operation_log(f"已导入 {count} 个键")
                self.refresh_keys()
            else:
                QMessageBox.critical(self, "错误", "导入失败")

    def backup_database(self):
        if not self.redis_manager.is_connected:
            QMessageBox.warning(self, "警告", "未连接到 Redis 服务器")
            return

        filepath = self.backup_service.create_backup(self.redis_manager, self.current_pattern)
        if filepath:
            self.add_operation_log(f"备份已创建: {filepath}")
        else:
            QMessageBox.critical(self, "错误", "创建备份失败")

    def restore_database(self):
        if not self.redis_manager.is_connected:
            QMessageBox.warning(self, "警告", "未连接到 Redis 服务器")
            return

        filepath, _ = QFileDialog.getOpenFileName(self, "从备份恢复", "", "JSON 文件 (*.json)")
        if filepath:
            reply = QMessageBox.question(
                self, "确认恢复",
                "此操作将覆盖现有键。是否继续？",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                success, count = self.backup_service.restore_backup(self.redis_manager, filepath, overwrite=True)
                if success:
                    self.add_operation_log(f"已恢复 {count} 个键")
                    self.refresh_keys()
                else:
                    QMessageBox.critical(self, "错误", "恢复失败")

    def show_about(self):
        QMessageBox.about(
            self,
            "关于 Redis 桌面客户端",
            "<h2>Redis 桌面客户端</h2>"
            "<p>一款现代化、快速、用户友好的 Redis 桌面客户端。</p>"
            "<p><b>功能特性:</b></p>"
            "<ul>"
            "<li>多连接管理</li>"
            "<li>快速键搜索和筛选</li>"
            "<li>JSON/XML 数据格式化</li>"
            "<li>内置控制台</li>"
            "<li>实时监控</li>"
            "<li>备份和恢复</li>"
            "<li>导入/导出 (JSON, CSV)</li>"
            "</ul>"
            "<p>使用 Python 3 和 PyQt5 构建</p>"
        )

    def load_connections(self):
        self.connection_combo.clear()
        connections = self.config_manager.get_all_connections()
        for conn in connections:
            self.connection_combo.addItem(conn.name, userData=conn.id)
        if connections:
            self.connection_combo.setCurrentIndex(0)

    def on_connection_changed(self):
        if self.redis_manager.is_connected:
            self.redis_manager.disconnect()
            self.update_status_indicator(False)
        self.key_tree.clear()
        self.value_editor.clear()
        self.key_name_label.setText("键名: ")
        self.key_type_label.setText("类型: ")
        self.ttl_label.setText("TTL: ")
        self.add_operation_log("切换连接，已清空数据")

    def add_connection(self):
        dialog = ConnectionDialog(self)
        if dialog.exec_():
            config = dialog.get_config()
            self.config_manager.add_connection(config)
            self.load_connections()
            idx = self.connection_combo.findData(config.id)
            if idx >= 0:
                self.connection_combo.setCurrentIndex(idx)

    def edit_connection(self):
        current_id = self.connection_combo.currentData()
        if not current_id:
            QMessageBox.warning(self, "警告", "未选择连接")
            return

        config = self.config_manager.get_connection(current_id)
        if not config:
            return

        dialog = ConnectionDialog(self, config)
        if dialog.exec_():
            self.config_manager.update_connection(dialog.get_config())
            self.load_connections()

    def delete_connection(self):
        current_id = self.connection_combo.currentData()
        if not current_id:
            QMessageBox.warning(self, "警告", "未选择连接")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除此连接吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config_manager.delete_connection(current_id)
            self.load_connections()

    def connect_to_redis(self):
        current_id = self.connection_combo.currentData()
        if not current_id:
            QMessageBox.warning(self, "警告", "未选择连接")
            return

        config = self.config_manager.get_connection(current_id)
        if not config:
            return

        success, message = self.redis_manager.connect(config)
        if success:
            self.update_status_indicator(True)
            self.add_operation_log(f"已连接到 {config.name} ({config.host}:{config.port})")
            self.refresh_keys()
        else:
            QMessageBox.critical(self, "连接错误", message)

    def disconnect_from_redis(self):
        self.redis_manager.disconnect()
        self.key_tree.clear()
        self.value_editor.clear()
        self.key_name_label.setText("键名: ")
        self.key_type_label.setText("类型: ")
        self.ttl_label.setText("TTL: ")
        self.update_status_indicator(False)
        self.add_operation_log("已断开连接")

    def update_status_indicator(self, connected: bool):
        if connected:
            self.status_indicator.setStyleSheet("background-color: #44CC44; border-radius: 6px;")
        else:
            self.status_indicator.setStyleSheet("background-color: #FF4444; border-radius: 6px;")

    def create_operation_log_widget(self):
        widget = QWidget()
        widget.setFixedHeight(150)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)

        header_layout = QHBoxLayout()
        header_label = QLabel("操作记录")
        header_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #333;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()

        btn_clear_log = QPushButton("清空")
        btn_clear_log.setFixedSize(50, 20)
        btn_clear_log.setStyleSheet("QPushButton { background-color: #E0E0E0; color: #333; border-radius: 4px; font-size: 11px; }")
        btn_clear_log.clicked.connect(self.clear_operation_log)
        header_layout.addWidget(btn_clear_log)

        layout.addLayout(header_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 9))
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #2B2B2B;
                color: #D4D4D4;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 2px;
            }
        """)
        layout.addWidget(self.log_output)

        return widget

    def add_operation_log(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.operation_log.insert(0, log_entry)
        
        # Keep only the last 100 entries
        if len(self.operation_log) > 100:
            self.operation_log.pop()
        
        # Update the display
        self.log_output.clear()
        
        for entry in self.operation_log[:100]:
            self.log_output.insertHtml(f"<span style='color: #D4D4D4;'>{entry}</span><br>")
        self.log_output.moveCursor(self.log_output.textCursor().Start)

    def clear_operation_log(self):
        self.operation_log.clear()
        self.log_output.clear()

    def toggle_console(self):
        if self.operation_log_widget.isVisible():
            self.operation_log_widget.hide()
            self.add_operation_log("操作记录已隐藏")
        else:
            self.operation_log_widget.show()
            self.add_operation_log("操作记录已显示")

    def on_type_filter_changed(self):
        self.current_page = 0
        self.refresh_keys()

    def refresh_keys(self):
        if not self.redis_manager.is_connected:
            return

        self.key_tree.clear()
        search_text = self.search_edit.text().strip()
        if search_text:
            if '*' not in search_text:
                self.current_pattern = f"*{search_text}*"
            else:
                self.current_pattern = search_text
        else:
            self.current_pattern = "*"

        type_filter = self.type_filter.currentText()
        key_type = None
        if type_filter != "All Types":
            type_map = {
                "String": "string",
                "Hash": "hash",
                "List": "list",
                "Set": "set",
                "Zset": "zset"
            }
            key_type = type_map.get(type_filter, "")

        self.load_keys_thread = LoadKeysThread(
            self.redis_manager,
            self.current_pattern,
            self.current_page,
            self.page_size,
            key_type
        )
        self.load_keys_thread.finished.connect(self.on_keys_loaded)
        self.load_keys_thread.start()

    def on_keys_loaded(self, keys: list[KeyInfo], total: int):
        sorted_keys = sorted(keys, key=lambda k: k.key)
        
        root_items = {}
        
        folder_icon = self.create_folder_icon()
        key_icon = self.create_key_icon()
        
        for key_info in sorted_keys:
            parts = key_info.key.split(':')
            
            if len(parts) > 1:
                current_path = ""
                parent_item = None
                
                for i, part in enumerate(parts[:-1]):
                    current_path = current_path + part + ":" if i == 0 else current_path + ":" + part
                    
                    if current_path not in root_items:
                        folder_item = QTreeWidgetItem([part, "FOLDER", ""])
                        folder_item.setIcon(0, folder_icon)
                        folder_item.setForeground(1, QColor("#808080"))
                        folder_item.setFont(0, QFont("Microsoft YaHei", 11))
                        
                        if parent_item:
                            parent_item.addChild(folder_item)
                        else:
                            self.key_tree.addTopLevelItem(folder_item)
                        
                        root_items[current_path] = folder_item
                        parent_item = folder_item
                    else:
                        parent_item = root_items[current_path]
                
                key_item = QTreeWidgetItem([
                    parts[-1],
                    key_info.key_type.upper(),
                    DataFormatter.format_ttl(key_info.ttl)
                ])
                key_item.setIcon(0, key_icon)
                key_item.setData(0, Qt.UserRole, key_info.key)
                key_item.setFont(0, QFont("Consolas", 11))
                
                type_colors = {
                    "string": "#4ec9b0",
                    "hash": "#569cd6",
                    "list": "#dcdcaa",
                    "set": "#c586c0",
                    "zset": "#ce9178"
                }
                color = type_colors.get(key_info.key_type, "#333333")
                key_item.setForeground(1, QColor(color))
                
                if parent_item:
                    parent_item.addChild(key_item)
                else:
                    self.key_tree.addTopLevelItem(key_item)
            else:
                item = QTreeWidgetItem([
                    key_info.key,
                    key_info.key_type.upper(),
                    DataFormatter.format_ttl(key_info.ttl)
                ])
                item.setIcon(0, key_icon)
                item.setData(0, Qt.UserRole, key_info.key)
                item.setFont(0, QFont("Consolas", 11))
                
                type_colors = {
                    "string": "#4ec9b0",
                    "hash": "#569cd6",
                    "list": "#dcdcaa",
                    "set": "#c586c0",
                    "zset": "#ce9178"
                }
                color = type_colors.get(key_info.key_type, "#333333")
                item.setForeground(1, QColor(color))
                
                self.key_tree.addTopLevelItem(item)
        
        for i in range(self.key_tree.topLevelItemCount()):
            item = self.key_tree.topLevelItem(i)
            if item.childCount() > 0 and item.text(1) == "FOLDER":
                item.setExpanded(True)

        self.total_label.setText(f"总计: {total}")
        self.page_label.setText(f"第 {self.current_page + 1} 页")

        # Update pagination buttons state
        self.btn_prev.setEnabled(self.current_page > 0)
        has_more = total > (self.current_page + 1) * self.page_size
        self.btn_next.setEnabled(has_more)

        # If there's a pending key to select, select it now
        if self.pending_select_key:
            self.select_key_in_tree(self.pending_select_key)
            self.pending_select_key = None

    def create_folder_icon(self):
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#F0C040"))
        painter.setPen(QColor("#D4A020"))
        painter.drawRoundedRect(1, 4, 14, 10, 2, 2)
        painter.setBrush(QColor("#F0C040"))
        painter.drawRoundedRect(1, 2, 6, 4, 2, 2)
        painter.end()
        return QIcon(pixmap)

    def create_key_icon(self):
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor("#4A90D9"))
        painter.setPen(QColor("#3A70B0"))
        painter.drawEllipse(2, 2, 12, 12)
        painter.setPen(QColor("#FFFFFF"))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(5, 5, 6, 6)
        painter.end()
        return QIcon(pixmap)

    def search_keys(self):
        self.current_page = 0
        search_text = self.search_edit.text().strip()
        if search_text:
            if '*' not in search_text:
                self.current_pattern = f"*{search_text}*"
            else:
                self.current_pattern = search_text
        else:
            self.current_pattern = "*"
        self.refresh_keys_with_pattern()

    def refresh_keys_with_pattern(self):
        if not self.redis_manager.is_connected:
            return

        self.key_tree.clear()

        type_filter = self.type_filter.currentText()
        if type_filter != "All Types":
            type_map = {
                "String": "string",
                "Hash": "hash",
                "List": "list",
                "Set": "set",
                "Zset": "zset"
            }
            type_name = type_map.get(type_filter, "")
            if type_name:
                self.current_pattern = f"*:{type_name}*" if self.current_pattern == "*" else self.current_pattern

        self.load_keys_thread = LoadKeysThread(
            self.redis_manager,
            self.current_pattern,
            self.current_page,
            self.page_size
        )
        self.load_keys_thread.finished.connect(self.on_keys_loaded)
        self.load_keys_thread.start()

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_keys()

    def next_page(self):
        self.current_page += 1
        self.refresh_keys()

    def on_page_size_changed(self):
        self.page_size = int(self.page_size_combo.currentText())
        self.current_page = 0
        self.refresh_keys()

    def on_key_selected(self, item, column):
        key_name = item.data(0, Qt.UserRole)
        if key_name:
            self.load_key_value(key_name)

    def load_key_value(self, key: str):
        kv = self.redis_manager.get_key_value(key)
        if not kv:
            return

        self.key_name_label.setText(f"键名: {key}")
        self.key_type_label.setText(f"类型: {kv.key_type.upper()}")
        self.ttl_label.setText(f"TTL: {DataFormatter.format_ttl(kv.ttl)}")

        if kv.ttl > 0:
            self.ttl_spin.setValue(kv.ttl)
        else:
            self.ttl_spin.setValue(-1)

        formatted_value = DataFormatter.format_value(kv.value, kv.key_type)
        self.value_editor.setPlainText(formatted_value)
        
        cmd_map = {
            "string": "GET",
            "hash": "HGETALL",
            "list": "LRANGE",
            "set": "SMEMBERS",
            "zset": "ZRANGE"
        }
        cmd = cmd_map.get(kv.key_type, "GET")
        self.add_operation_log(f"{cmd} {key}")

    def create_new_key(self):
        if not self.redis_manager.is_connected:
            QMessageBox.warning(self, "警告", "未连接到 Redis 服务器")
            return

        dialog = NewKeyDialog(self, self.redis_manager)
        if dialog.exec_():
            key_name, key_type, value, ttl = dialog.get_key_data()
            
            try:
                import json
                success = False
                if key_type == "string":
                    success = self.redis_manager.client.set(key_name, value, ex=ttl if ttl > 0 else None)
                elif key_type == "hash":
                    data = json.loads(value)
                    success = self.redis_manager.client.hset(key_name, mapping=data)
                elif key_type == "list":
                    items = json.loads(value)
                    if items:
                        success = self.redis_manager.client.rpush(key_name, *items)
                    else:
                        success = True
                elif key_type == "set":
                    members = json.loads(value)
                    if members:
                        success = self.redis_manager.client.sadd(key_name, *members)
                    else:
                        success = True
                elif key_type == "zset":
                    mapping = json.loads(value)
                    mapping = {k: float(v) for k, v in mapping.items()}
                    success = self.redis_manager.client.zadd(key_name, mapping)
                
                # 对于非 String 类型，单独设置 TTL
                if success and key_type != "string" and ttl > 0:
                    self.redis_manager.client.expire(key_name, ttl)
                
                if success:
                    QMessageBox.information(self, "成功", f"键 '{key_name}' 创建成功")
                    cmd_map = {
                        "string": "SET",
                        "hash": "HSET",
                        "list": "RPUSH",
                        "set": "SADD",
                        "zset": "ZADD"
                    }
                    cmd = cmd_map.get(key_type, "SET")
                    display_value = value[:50] + "..." if len(value) > 50 else value
                    ttl_info = f" EX {ttl}" if ttl > 0 else ""
                    self.add_operation_log(f"{cmd} {key_name} {display_value}{ttl_info}")
                    # Set pending key to select after refresh completes
                    self.pending_select_key = key_name
                    self.refresh_keys()
                else:
                    QMessageBox.critical(self, "错误", "创建键失败")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建键失败: {str(e)}")

    def delete_selected_key(self):
        selected_items = self.key_tree.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "警告", "未选择键")
            return

        # Filter out folder items
        actual_keys = []
        for item in selected_items:
            key_name = item.data(0, Qt.UserRole)
            if key_name:
                actual_keys.append(key_name)

        if not actual_keys:
            QMessageBox.warning(self, "警告", "未选择键")
            return

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {len(actual_keys)} 个键吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            deleted = self.redis_manager.delete_keys(actual_keys)
            keys_str = ", ".join(actual_keys[:3])
            if len(actual_keys) > 3:
                keys_str += "..."
            self.add_operation_log(f"DEL {keys_str}")
            
            # If the currently selected key was deleted, clear the right panel
            current_item = self.key_tree.currentItem()
            if current_item:
                current_key = current_item.data(0, Qt.UserRole)
                if current_key in actual_keys:
                    self.key_tree.clearSelection()
                    self.value_editor.clear()
                    self.key_name_label.setText("键名: ")
                    self.key_type_label.setText("类型: ")
                    self.ttl_label.setText("TTL: ")
            
            self.refresh_keys()

    def rename_selected_key(self):
        current_item = self.key_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "未选择键")
            return

        old_key = current_item.data(0, Qt.UserRole)
        if not old_key:
            QMessageBox.warning(self, "警告", "未选择键")
            return

        # 使用自定义对话框以支持更宽的输入框
        dialog = QDialog(self)
        dialog.setWindowTitle("重命名键")
        dialog.setMinimumWidth(600)
        dialog.setModal(True)
        
        layout = QVBoxLayout(dialog)
        
        info_label = QLabel("当前键名:")
        info_label.setStyleSheet("color: #808080; font-size: 12px;")
        layout.addWidget(info_label)
        
        old_key_label = QLabel(old_key)
        old_key_label.setStyleSheet("background-color: #F5F5F5; padding: 8px; border-radius: 4px; font-family: Consolas, monospace; font-size: 14px;")
        old_key_label.setWordWrap(True)
        layout.addWidget(old_key_label)
        
        layout.addSpacing(10)
        
        new_key_label = QLabel("新键名:")
        layout.addWidget(new_key_label)
        
        new_key_edit = QLineEdit(old_key)
        new_key_edit.setMinimumHeight(35)
        new_key_edit.setStyleSheet("font-family: Consolas, monospace; font-size: 14px; padding: 5px;")
        layout.addWidget(new_key_edit)
        
        layout.addSpacing(10)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_ok = QPushButton("确定")
        btn_ok.setStyleSheet("QPushButton { background-color: #4A90D9; color: white; padding: 8px 20px; border-radius: 4px; font-weight: bold; }")
        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet("QPushButton { background-color: #E0E0E0; color: #333; padding: 8px 20px; border-radius: 4px; }")
        
        buttons_layout.addWidget(btn_ok)
        buttons_layout.addWidget(btn_cancel)
        layout.addLayout(buttons_layout)
        
        btn_ok.clicked.connect(dialog.accept)
        btn_cancel.clicked.connect(dialog.reject)
        
        # 设置焦点到输入框
        new_key_edit.selectAll()
        new_key_edit.setFocus()
        
        if dialog.exec_() == QDialog.Accepted:
            new_key = new_key_edit.text().strip()
            if new_key and new_key != old_key:
                if self.redis_manager.rename_key(old_key, new_key):
                    self.add_operation_log(f"RENAME {old_key} {new_key}")
                    # Set pending key to select after refresh completes
                    self.pending_select_key = new_key
                    self.refresh_keys()
                else:
                    QMessageBox.critical(self, "错误", "重命名键失败")

    def refresh_selected_key(self):
        current_item = self.key_tree.currentItem()
        if current_item:
            key = current_item.data(0, Qt.UserRole)
            if key:
                self.load_key_value(key)

    def select_key_in_tree(self, key_name: str):
        """Find and select a key in the tree, then load its value"""
        iterator = QTreeWidgetItemIterator(self.key_tree)
        while iterator.value():
            item = iterator.value()
            item_key = item.data(0, Qt.UserRole)
            if item_key == key_name:
                self.key_tree.setCurrentItem(item)
                self.load_key_value(key_name)
                return
            iterator += 1

    def reformat_value(self):
        current_text = self.value_editor.toPlainText()
        fmt = self.format_combo.currentText()

        if fmt == "JSON":
            self.value_editor.setPlainText(DataFormatter.format_json(current_text))
        elif fmt == "XML":
            self.value_editor.setPlainText(DataFormatter.format_xml(current_text))

    def validate_value(self):
        current_text = self.value_editor.toPlainText()
        key_type = self.key_type_label.text().replace("类型: ", "").lower()

        valid, message = DataValidator.validate_value(current_text, key_type)
        if valid:
            QMessageBox.information(self, "验证", "值有效")
        else:
            QMessageBox.warning(self, "验证", message)

    def format_value(self):
        self.reformat_value()

    def save_value(self):
        current_item = self.key_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "未选择键")
            return

        key = current_item.data(0, Qt.UserRole)
        if not key:
            QMessageBox.warning(self, "警告", "未选择键")
            return

        key_type = self.key_type_label.text().replace("类型: ", "").lower()
        value = self.value_editor.toPlainText()

        try:
            # 使用 parse_value_for_save 解析编辑后的值
            parsed_value = DataFormatter.parse_value_for_save(value, key_type)

            if self.redis_manager.set_key_value(key, key_type, parsed_value):
                QMessageBox.information(self, "成功", f"键 '{key}' 保存成功")
                cmd_map = {
                    "string": "SET",
                    "hash": "HSET",
                    "list": "RPUSH",
                    "set": "SADD",
                    "zset": "ZADD"
                }
                cmd = cmd_map.get(key_type, "SET")
                display_value = value[:120] + "..." if len(value) > 120 else value
                self.add_operation_log(f"{cmd} {key} {display_value}")
                self.refresh_selected_key()
            else:
                QMessageBox.critical(self, "错误", "保存值失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存值失败: {str(e)}")

    def set_key_ttl(self):
        current_item = self.key_tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "未选择键")
            return

        key = current_item.data(0, Qt.UserRole)
        if not key:
            QMessageBox.warning(self, "警告", "未选择键")
            return
        
        ttl = self.ttl_spin.value()
        
        if ttl == -1:
            if self.redis_manager.set_ttl(key, ttl):
                self.add_operation_log(f"PERSIST {key}")
                self.refresh_selected_key()
            else:
                QMessageBox.critical(self, "错误", "设置 TTL 失败")
        elif ttl > 0:
            if self.redis_manager.set_ttl(key, ttl):
                self.add_operation_log(f"EXPIRE {key} {ttl}")
                self.refresh_selected_key()
            else:
                QMessageBox.critical(self, "错误", "设置 TTL 失败")
        else:
            QMessageBox.warning(self, "警告", "TTL 值无效")

    def show_key_context_menu(self, position):
        menu = QMenu()

        action_refresh = QAction("刷新", self)
        action_refresh.triggered.connect(self.refresh_keys)
        menu.addAction(action_refresh)

        action_delete = QAction("删除选中", self)
        action_delete.triggered.connect(self.delete_selected_key)
        menu.addAction(action_delete)

        action_rename = QAction("重命名", self)
        action_rename.triggered.connect(self.rename_selected_key)
        menu.addAction(action_rename)

        menu.addSeparator()

        action_export = QAction("导出", self)
        menu.addAction(action_export)

        menu.exec_(self.key_tree.viewport().mapToGlobal(position))
