# Redis Desktop Client

一款使用 Python 3 和 PyQt5 构建的现代化、快速、用户友好的 Redis 桌面客户端，旨在提供比 Redis Desktop Manager 更好的使用体验。

## 功能特性

### 核心功能
- **多连接管理**：管理多个 Redis 服务器连接，支持快速切换
- **Key 浏览器**：支持通配符的快速 Key 搜索、类型筛选和分页浏览
- **数据编辑器**：支持 JSON/XML 格式化和语法高亮的数据查看与编辑
- **命令行控制台**：直接执行 Redis 命令，支持历史记录
- **服务器监控**：实时监控内存使用、连接数、命中率等关键指标

### 高级功能
- **批量操作**：批量删除 Key、批量导入/导出
- **备份与恢复**：创建和恢复数据库备份
- **导入/导出**：支持 JSON 和 CSV 格式
- **定时任务**：自动备份和命令执行
- **主题支持**：暗色主题，舒适的使用体验
- **操作历史**：追踪并重新执行历史操作

## 安装

### 前置要求
- Python 3.8 或更高版本
- Redis 服务器（用于测试）

### 安装步骤
1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 运行程序：
   ```bash
   python main.py
   ```

### Windows 可执行文件
运行 `build.bat` 生成独立的 Windows 可执行文件。

## 使用说明

### 添加连接
1. 点击工具栏中的"添加"按钮
2. 输入连接详情（主机、端口、密码等）
3. 点击"测试连接"验证配置
4. 点击"确定"保存

### 浏览 Key
- 在搜索框中使用通配符（例如：`user:*`、`*session*`）
- 按类型筛选（String、Hash、List、Set、Sorted Set）
- 使用"上一页"/"下一页"按钮进行分页导航
- 调整每页显示数量（50、100、200、500）

### 编辑数据
1. 从列表中选择一个 Key
2. 在"数据编辑器"选项卡中查看/编辑值
3. 使用"格式化"按钮美化 JSON/XML
4. 点击"保存"应用更改
5. 使用 TTL 编辑器设置过期时间

### 使用控制台
- 直接输入 Redis 命令（例如：`GET mykey`、`SET mykey value`）
- 使用上/下方向键浏览命令历史
- 查看执行时间和结果

### 服务器监控
- 点击"开始监控"查看实时统计数据
- 监控内存使用率、命中率、已连接客户端数
- 追踪每秒操作数和 Key 数量

### 备份与恢复
- 使用控制台命令：`BGSAVE`、`SAVE`
- 将 Key 导出为 JSON/CSV 格式
- 从备份文件导入数据

## 项目结构

```
redis_desktop_client/
├── main.py                    # 程序入口
├── requirements.txt           # Python 依赖列表
├── setup.bat                  # Windows 安装脚本
├── run.bat                    # Windows 运行脚本
├── build.bat                  # Windows 构建脚本
├── config/
│   └── connections.json       # 连接配置存储
├── src/
│   ├── core/
│   │   ├── redis_manager.py   # Redis 连接和操作
│   │   └── config_manager.py  # 配置管理
│   ├── models/
│   │   ├── connection.py      # 连接数据模型
│   │   └── key_data.py        # Key 和值数据模型
│   ├── ui/
│   │   ├── main_window.py     # 主程序窗口
│   │   ├── connection_dialog.py # 连接配置对话框
│   │   ├── console.py         # Redis 命令控制台
│   │   └── monitor.py         # 服务器监控面板
│   ├── utils/
│   │   ├── formatters.py      # 数据格式化工具
│   │   └── validators.py      # 数据验证工具
│   └── services/
│       ├── backup_service.py  # 备份和恢复
│       ├── import_export.py   # 导入/导出功能
│       └── scheduler.py       # 定时任务
├── resources/
│   ├── icons/                 # 应用程序图标
│   └── themes/                # 主题文件
└── tests/                     # 测试文件
```

## 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| Ctrl+R | 刷新 Key 列表 |
| Ctrl+F | 聚焦搜索框 |
| Ctrl+Enter | 执行控制台命令 |
| 上/下方向键 | 浏览命令历史 |
| Delete | 删除选中的 Key |
| F2 | 重命名选中的 Key |
| F5 | 刷新当前视图 |

## 支持的 Redis 数据类型

- **String**：文本、JSON、XML、二进制数据
- **Hash**：字段-值对
- **List**：有序集合
- **Set**：无序唯一集合
- **Sorted Set**：带分数的有序集合

## 与 Redis Desktop Manager 对比

| 特性 | Redis Desktop Client | Redis Desktop Manager |
|------|---------------------|----------------------|
| 启动速度 | 快速（轻量级） | 较慢（笨重） |
| Key 搜索 | 快速分页加载 | 大数据库时较慢 |
| 数据编辑 | JSON/XML 格式化 | 基础编辑 |
| 控制台 | 内置带历史记录 | 功能有限 |
| 监控面板 | 实时仪表盘 | 基础信息 |
| 批量操作 | 支持 | 有限 |
| 备份/恢复 | 免费 | 付费功能 |
| 定时任务 | 支持 | 不支持 |
| 价格 | 免费 | 收费 |
| 开源 | 是 | 否 |

## 开发指南

### 运行测试
```bash
python -m pytest tests/
```

### 代码规范
遵循 PEP 8 规范。运行代码检查：
```bash
flake8 src/
```

## 常见问题

### 连接问题
- 确认 Redis 服务器正在运行
- 检查主机、端口和密码是否正确
- 确保防火墙允许连接

### 性能问题
- 对于大型数据库，减少每页显示数量
- 使用具体的搜索模式代替 `*`
- 关闭未使用的连接

### 显示问题
- 尝试不同的字体设置
- 检查 Qt5 依赖是否正确安装

## 许可证

MIT 许可证 - 详见 LICENSE 文件

## 贡献

欢迎贡献代码！请提交 Pull Request 或为 Bug 和功能需求创建 Issue。

## 技术支持

如需技术支持，请在项目仓库中创建 Issue。
