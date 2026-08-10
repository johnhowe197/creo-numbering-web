# Creo 模型树自动取号器（Web 版）

浏览器端模型树图号编号工具，支持**本地安装使用**与**服务器多人共享**两种形态。

## 功能

- **模型树管理**：图号 / 名称 / 备注 / 状态色（红黄绿蓝），双击就地编辑，行内操作按钮 + 右键菜单，展开/折叠
- **编号规则 v2**：组件追加法、零件分叉法、字母组件（如 `-ZBC`）与主机层（如 `-00`）、字母组件零件宿主共享序列
- **多项目**：项目列表、项目中文名称、导入桌面版 JSON 数据
- **本地打包**：PyInstaller 打包 exe + NSIS 安装包，数据存本地 SQLite（跟随安装目录）

## 快速开始

### 安装包使用（推荐）

从 [Releases](https://github.com/johnhowe197/creo-numbering-web/releases) 下载安装程序，双击安装后桌面快捷方式启动，浏览器自动打开。

### 开发运行

```bash
cd creo编号器-web
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器打开 http://127.0.0.1:8000/ 。

### 本地打包

```bash
cd creo编号器-web
pyinstaller build.spec --clean --noconfirm   # 产出 dist\Creo编号器Web\
makensis installer.nsi                        # 生成安装包（需 NSIS）
```

## 技术栈

- 后端：FastAPI + SQLite（编号分配在事务中原子完成）
- 前端：React 18 + Vite
- 打包：PyInstaller + NSIS

## 文档

- 详细说明：`creo编号器-web/README.md`
- 编号规则 v2：`Creo 模型树图号层级与编号规则（开发说明）.md`
- 服务器部署预案：`creo编号器-web/deploy/部署预案.md`
