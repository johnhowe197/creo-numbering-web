# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Creo 模型树自动取号器（Web 版）- 浏览器端模型树图号编号工具：

- 技术栈：FastAPI + SQLite 后端、React + Vite 前端、编号核心逻辑内置 `creo编号器-web/core/`（自包含）
- 两种运行形态：本地安装版（数据跟随安装目录）与服务器部署（多电脑共享）
- 本地打包：PyInstaller 产出 exe + NSIS 安装包

## 常用命令

### 运行（开发模式）

```bash
cd creo编号器-web
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# 浏览器打开 http://127.0.0.1:8000/
```

### 前端

```bash
cd creo编号器-web/web
npm install
npm run build     # 构建产物 web/dist，由后端托管
npm run dev       # 开发热更新（已代理 /api 到 8000）
```

### 测试

```bash
cd creo编号器-web
python -m unittest discover -s tests
```

### 打包本地应用

```bash
cd creo编号器-web
pyinstaller build.spec --clean --noconfirm   # 产出 dist\Creo编号器Web\
makensis installer.nsi                        # 生成安装包（需 NSIS）
```

## 架构（`creo编号器-web/`）

- **app/main.py** - FastAPI 入口与全部路由（项目/节点/编号/导入/项目改名）
- **app/database.py** - SQLite 访问层（编号分配在 `BEGIN IMMEDIATE` 事务中原子完成；数据目录按「环境变量 `NUMBERING_DATA_DIR` → 打包版 exe 旁 `data\` → 开发模式 `data\`」解析）
- **app/numbering.py** - 编号核心逻辑包装（复用本目录 `core/`）
- **core/** - 编号核心（parser/generator/tree_model），Web 版自包含
- **web/** - React + Vite 前端（构建产物 `web/dist/` 由 FastAPI 托管）
- **launcher.py** - 本地打包启动器（自动选择空闲端口并打开浏览器，日志写入 `logs\error.log`）
- **build.spec / installer.nsi** - 本地打包与 NSIS 安装包
- **deploy/部署预案.md** - 服务器部署预案（待审阅）

### 数据流

```
浏览器 → HTTP API → FastAPI → core 计算编号 → SQLite 原子落库
```

## 编号规则

编号规则 v2 详见 `Creo 模型树图号层级与编号规则（开发说明）.md`，要点：

- **组件（追加法）**：父级图号 + 两位数字（01~99），如 `03S01201-10010103`
- **组件（字母）**：层级码可含字母（如 `LS001-ZBC` 功能模块）；字母组件下新建组件使用「根前缀 + 两位数字」全局编号（从 01 起）
- **主机层**：根的直接子级两位数字（如 `-00`），只放字母组件（手动输入），**不创建零件**
- **字母组件下零件**：使用**宿主**（字母组件父级）的共享零件序列，如 `-ZBC`、`-KTC` 下零件依次为 `-00-1`、`-00-2`…
- **典型结构**：根 `LS001` → 主机 `LS001-00` → 字母模块 `LS001-ZBC` → 数字组件 `LS001-01`（层级由模型树显式表达，图号不完整编码层级）
- **零件（分叉法）**：父级图号 + `-` + 顺序数字，如 `03S01201-100101-3`
- 零件不能作为父级；组件图号不能以 `-数字` 结尾

## 界面功能

- 模型树：图号/名称/备注/状态色（红黄绿蓝），双击编辑名称与备注，行内操作按钮（+组件/+零件/重命名/删除），右键菜单
- 项目：多项目管理、项目中文名称（可随时修改）、导入桌面版 JSON、展开/折叠全部

## 关键文件

- `creo编号器-web/README.md` - 使用、运行、打包、部署说明
- `app/main.py`、`app/database.py`、`app/numbering.py`、`core/` - 后端与核心
- `web/src/` - 前端源码（App.jsx、components/、styles.css）
- `Creo 模型树图号层级与编号规则（开发说明）.md` - 编号规则 v2 完整文档
