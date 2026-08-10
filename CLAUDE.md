# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Creo模型树自动取号器 - 用于Creo模型树图号自动编号的工具，含两个版本：

- **桌面版**（`creo编号器/`）：PyQt6 桌面应用，数据存本地 JSON，支持树形视图、拖拽、备忘录、状态标记。
- **Web 版**（`creo编号器-web/`）：FastAPI + SQLite 后端 + React 前端，数据存服务器，支持多电脑/多人共享，编号在服务端原子分配。

两版共用 `creo编号器/core` 核心编号逻辑，编号规则（v2）完全一致。

## 常用命令

### 运行程序
```bash
# 直接运行
python creo编号器/main.py

# Windows批处理
creo编号器/run.bat
```

### 测试
```bash
# 单元测试
python creo编号器/test_core.py

# 完整测试套件（含性能基准）
python creo编号器/harness.py
```

### 构建
```bash
# 安装构建依赖
pip install pyinstaller pillow

# 一键构建
creo编号器/build.bat

# 或手动构建
cd creo编号器
pyinstaller build.spec --clean --noconfirm
```

输出目录：`creo编号器/dist/Creo编号器/`

### Web 版
```bash
# 后端（FastAPI，同时托管前端构建产物）
cd creo编号器-web
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 前端构建（改前端源码后执行）
cd creo编号器-web/web
npm install
npm run build

# 后端 API 测试
cd creo编号器-web
python -m unittest discover -s tests
```

## 架构

### 核心模块 (`creo编号器/core/`)

- **parser.py** - 图号解析器：解析图号结构、判断类型（组件/零件）、验证父级有效性
- **generator.py** - 图号生成器：根据父级图号生成下一个可用图号
- **tree_model.py** - 树形数据模型：管理层级结构、节点CRUD、JSON持久化

### UI模块 (`creo编号器/ui/`)

- **main_window.py** - PyQt6主窗口：树形视图、拖拽支持、右键菜单、工具栏

### Web 模块 (`creo编号器-web/`)

- **app/main.py** - FastAPI 入口与全部路由（项目/节点/编号/导入）
- **app/database.py** - SQLite 访问层（编号分配在 `BEGIN IMMEDIATE` 事务中原子完成）
- **app/numbering.py** - 编号核心逻辑包装（复用 `creo编号器/core`）
- **web/** - React + Vite 前端（构建产物 `web/dist/` 由 FastAPI 托管）
- **deploy/部署预案.md** - 服务器部署预案（待审阅）

### 数据流

```
用户输入父级图号 → parser解析 → generator生成新图号 → TreeModel管理 → JSON文件持久化
```

## 编号规则

编号规则 v2 详见 `Creo 模型树图号层级与编号规则（开发说明）.md`，要点：

- **组件（追加法）**：父级图号 + 两位数字（01~99），如 `03S01201-10010103`
- **组件（字母）**：层级码可含字母（如 `LS001-ZBC` 功能模块）；字母组件下新建组件使用「根前缀 + 两位数字」全局编号（从 01 起）
- **主机层**：根的直接子级两位数字（如 `-00`），只放字母组件（手动输入），**不创建零件**
- **字母组件下零件**：使用**宿主**（字母组件父级）的共享零件序列，如 `-ZBC`、`-KTC` 下零件依次为 `-00-1`、`-00-2`…
- **典型结构**：根 `LS001` → 主机 `LS001-00` → 字母模块 `LS001-ZBC` → 数字组件 `LS001-01`（层级由模型树显式表达，图号不完整编码层级）
- **零件（分叉法）**：父级图号 + `-` + 顺序数字，如 `03S01201-100101-3`；数字组件下零件为 `-10-1`
- 零件不能作为父级（不能在其下创建子级）

## 新增功能

### 状态标记（第四列圆形图标）
- 右键菜单 → 设置颜色
- 快捷键：`Ctrl+0` 无色、`Ctrl+1` 红、`Ctrl+2` 黄、`Ctrl+3` 绿、`Ctrl+4` 蓝
- 圆形图标显示在状态列

### 备忘录（第三列）
- 双击直接编辑
- 工具栏按钮或右键菜单编辑
- 快捷键：`Ctrl+M`

## 图号格式

参考 `命名规范.md`：
- 根图号：`03S01201`（无横杠）
- 组件图号：`03S01201-100101`（横杠后为纯数字）或 `05S01101-ZBC`（含字母）
- 零件图号：`03S01201-100101-1`（末尾为 `-数字`）

## 关键文件

- `numbers.json` - 图号数据存储（运行时生成）
- `test_cases.json` - 测试用例配置
- `build.spec` - PyInstaller打包配置
- `installer.nsi` - NSIS安装程序脚本
- `creo编号器-web/` - Web 版（详见其 `README.md`）
- `05S01101.json` - 真实业务数据样例（不入 git 版本库）
