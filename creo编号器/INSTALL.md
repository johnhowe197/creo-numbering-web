# 安装和使用指南

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

**Windows:**
```bash
双击 run.bat
```

**或使用命令行:**
```bash
python start.py
```

## 功能说明

### 核心功能

1. **图号解析**
   - 输入父级图号，程序自动识别组件/零件类型
   - 显示该父级下的所有子图号

2. **自动编号**
   - **组件生成**：追加法（父级图号 + 两位数字）
     - 示例：`03S01201-100101` → `03S01201-10010101`
   - **零件生成**：分叉法（父级图号 + `-` + 顺序数字）
     - 示例：`03S01201-100101` → `03S01201-100101-1`

3. **历史记录**
   - 自动保存编号历史
   - 支持清空历史记录

## Web 版

Web 版（`creo编号器-web/`）将数据存到服务器，支持多电脑共享，编号规则与桌面版一致：

```bash
cd creo编号器-web
pip install -r requirements.txt
cd web && npm install && npm run build && cd ..
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器打开 http://127.0.0.1:8000/ 。服务器部署预案见
`creo编号器-web/deploy/部署预案.md`。

### 使用步骤

1. 在"父级图号"输入框中输入父级图号
2. 点击"解析"按钮，查看已有子图号
3. 选择新建类型（组件或零件）
4. 点击"生成新图号"按钮
5. 查看生成的新图号

## 项目结构

```
creo编号器/
├── start.py              # 启动脚本
├── main.py               # 主程序（备用）
├── core/
│   ├── __init__.py
│   ├── parser.py         # 图号解析器
│   └── generator.py      # 图号生成器
├── ui/
│   ├── __init__.py
│   └── main_window.py    # 主窗口界面
├── requirements.txt      # 依赖
├── run.bat               # Windows启动脚本
├── test_core.py          # 测试脚本
├── README.md             # 项目说明
└── INSTALL.md            # 本文件
```

## 测试

运行测试脚本验证核心功能：

```bash
python test_core.py
```

## 数据存储

程序会自动创建 `numbers.json` 文件保存编号数据。

## 故障排除

### 问题：PyQt6安装失败

尝试使用管理员权限运行：

```bash
pip install --user PyQt6
```

### 问题：中文显示乱码

确保系统已安装中文字体（如微软雅黑）。

### 问题：程序无法启动

检查Python版本是否为3.8+：

```bash
python --version
```

## 开发说明

### 核心模块

- **parser.py**：图号解析、验证
- **generator.py**：图号生成算法

### 扩展建议

1. 集成到Creo二次开发
2. 添加批量生成功能
3. 支持自定义编码规则
