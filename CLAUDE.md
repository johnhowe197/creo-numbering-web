# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

Creo模型树自动取号器 - 用于Creo模型树图号自动编号的桌面应用程序。基于 PyQt6 构建，支持组件（追加法）和零件（分叉法）两种编号规则。

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

## 架构

### 核心模块 (`creo编号器/core/`)

- **parser.py** - 图号解析器：解析图号结构、判断类型（组件/零件）、验证父级有效性
- **generator.py** - 图号生成器：根据父级图号生成下一个可用图号
- **tree_model.py** - 树形数据模型：管理层级结构、节点CRUD、JSON持久化

### UI模块 (`creo编号器/ui/`)

- **main_window.py** - PyQt6主窗口：树形视图、拖拽支持、右键菜单、工具栏

### 数据流

```
用户输入父级图号 → parser解析 → generator生成新图号 → TreeModel管理 → JSON文件持久化
```

## 编号规则

- **组件（追加法）**：父级图号 + 两位数字（01~99），如 `03S01201-10010103`
- **组件（字母）**：层级码可含字母（如 `LS001-ZBC` 功能模块）；字母组件下新建组件使用「根前缀 + 两位数字」全局编号，如 `LS001-ZBC` 下新建得到 `LS001-01`
- **典型结构**：根 `LS001` → 主机 `LS001-00` → 字母模块 `LS001-ZBC` → 数字组件 `LS001-01`（层级由模型树显式表达，图号不完整编码层级）
- **零件（分叉法）**：父级图号 + `-` + 顺序数字，如 `03S01201-100101-3`
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
- 组件图号：`03S01201-100101`（横杠后为纯数字）
- 零件图号：`03S01201-100101-1`（末尾为 `-数字`）

## 关键文件

- `numbers.json` - 图号数据存储（运行时生成）
- `test_cases.json` - 测试用例配置
- `build.spec` - PyInstaller打包配置
- `installer.nsi` - NSIS安装程序脚本
