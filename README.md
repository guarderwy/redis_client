# Redis Desktop Client

一款使用 Python 3 和 PyQt5 构建的现代化、快速、用户友好的 Redis 桌面客户端，旨在提供比 Redis Desktop Manager 更好的使用体验。

## 功能特性

### 核心功能
- **多连接管理**：管理多个 Redis 服务器连接，支持快速切换，连接状态实时指示（绿色/红色圆点）
- **Key 浏览器**：支持通配符搜索、类型筛选、分页浏览，树形结构展示（按冒号分隔自动折叠）
- **数据编辑器**：所有类型数据以 JSON 格式展示和编辑，支持格式化、验证和保存
- **命令行控制台**：直接执行 Redis 命令，支持历史记录
- **操作日志**：实时记录所有操作命令（SET、HGETALL、EXPIRE 等），保留最近 100 条

### 数据管理
- **新建 Key**：支持所有类型（String、Hash、List、Set、Zset），带表单验证和 TTL 设置
- **编辑 Key**：JSON 格式编辑，保存时自动验证格式并转换
- **重命名 Key**：宽屏对话框，完整显示键名
- **删除 Key**：支持单个和批量删除
- **TTL 管理**：设置过期时间或取消过期（永不过期）

### 高级功能
- **批量操作**：批量删除 Key、批量导入/导出
- **备份与恢复**：创建和恢复数据库备份
- **导入/导出**：支持 JSON 和 CSV 格式
- **定时任务**：自动备份和命令执行
- **主题支持**：亮色/暗色主题切换
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
运行 `build.bat` 生成独立的 Windows 可执行文件（无需安装 Python 即可运行）。

## 使用说明

### 添加连接
1. 点击工具栏中的"添加"按钮
2. 输入连接详情（主机、端口、密码等）
3. 点击"测试连接"验证配置
4. 点击"确定"保存
5. 连接成功后，状态栏显示绿色圆点

### 浏览 Key
- 在搜索框中使用通配符（例如：`user:*`、`*session*`）
- 按类型筛选（String、Hash、List、Set、Zset）
- 树形结构自动按冒号分层，可展开/折叠
- 使用"上一页"/"下一页"按钮进行分页导航
- 调整每页显示数量（50、100、200、500）

### 新建 Key
1. 点击"新建键"按钮
2. 选择类型（String、Hash、List、Set、Zset）
3. 输入键名和值（Hash/Zset 使用 JSON 对象格式，List/Set 使用 JSON 数组格式）
4. 可选：设置 TTL 过期时间（秒/分钟/小时/天）
5. 点击"确定"保存

### 编辑数据
1. 从列表中选择一个 Key
2. 在编辑器中查看/编辑值（JSON 格式）
3. 使用"格式化"按钮美化 JSON
4. 点击"验证"检查格式
5. 点击"保存"应用更改

### TTL 设置
- 在底部 TTL 输入框中输入秒数（-1 表示永不过期）
- 点击"设置 TTL"按钮应用

### 使用控制台
- 直接输入 Redis 命令（例如：`GET mykey`、`SET mykey value`）
- 使用上/下方向键浏览命令历史
- 查看执行时间和结果

### 操作日志
- 底部操作日志显示所有执行的 Redis 命令
- 包含完整命令和参数（例如：`SET user:1001 {"name": "张三"}`）
- 保留最近 100 条记录
- 最新的记录显示在最前面

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
│   │   ├── new_key_dialog.py  # 新建键对话框
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
- **Hash**：字段-值对（JSON 对象格式展示和编辑）
- **List**：有序集合（JSON 数组格式展示和编辑）
- **Set**：无序唯一集合（JSON 数组格式展示和编辑）
- **Sorted Set (Zset)**：带分数的有序集合（JSON 对象格式展示和编辑）

## 与 Redis Desktop Manager 对比

| 特性 | Redis Desktop Client | Redis Desktop Manager |
|------|---------------------|----------------------|
| 启动速度 | 快速（轻量级） | 较慢（笨重） |
| Key 搜索 | 快速分页加载 | 大数据库时较慢 |
| 数据编辑 | JSON 格式化编辑 | 基础编辑 |
| 控制台 | 内置带历史记录 | 功能有限 |
| 操作日志 | 完整命令记录 | 无 |
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

### 打包 Windows 可执行文件
```bash
.\build.bat
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

### 数据编辑问题
- Hash/Zset 使用 JSON 对象格式：`{"key": "value"}`
- List/Set 使用 JSON 数组格式：`["item1", "item2"]`
- 保存前可使用"验证"按钮检查格式

## 许可证

MIT 许可证 - 详见 LICENSE 文件

## 贡献

欢迎贡献代码！请提交 Pull Request 或为 Bug 和功能需求创建 Issue。

## 技术支持

如需技术支持，请在项目仓库中创建 Issue。
