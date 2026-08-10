# Creo 模型树自动取号器（Web 版）

浏览器端模型树取号工具，数据存储在服务器 SQLite 中，供多台电脑/多人共享。
编号规则与桌面版一致（复用 `creo编号器/core` 核心逻辑），并支持字母组件等特殊规则。

## 技术栈

- 后端：FastAPI + SQLite（标准库 `sqlite3`）
- 前端：React 18 + Vite（构建产物由 FastAPI 托管）
- 依赖：见 `requirements.txt`（后端）与 `web/package.json`（前端）

## 本地运行

```bash
# 1. 安装后端依赖
pip install -r requirements.txt

# 2. 安装前端依赖并构建
cd web
npm install
npm run build
cd ..

# 3. 启动服务（FastAPI 同时托管前端构建产物）
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

浏览器打开 http://127.0.0.1:8000/ 即可使用。

前端开发模式（热更新，需后端同时运行）：

```bash
cd web
npm run dev   # http://localhost:5173，已配置 /api 代理到 8000
```

## 打包为本地应用（exe）

把 Web 版打包成可执行程序，双击即启动本地服务并自动打开浏览器，数据存本地：

```bash
# 1. 确保前端已构建（web/dist 存在）
cd web && npm run build && cd ..

# 2. PyInstaller 打包（onedir，输出 dist\Creo编号器Web\）
pyinstaller build.spec --clean --noconfirm

# 3. 生成安装包（需安装 NSIS）
makensis installer.nsi
```

- 启动器：`launcher.py`（自动选空闲端口并打开浏览器）
- 数据位置：exe 所在目录的 `data\numbering.db`；可用环境变量 `NUMBERING_DATA_DIR` 覆盖
- 日志：`logs\error.log`（无窗口模式下 print/异常都写入这里）
- 卸载程序保留 `data\` 目录，不会删除业务数据

## 数据存储

- 数据库文件：`data/numbering.db`（运行时自动创建）
- 导入桌面版数据：页面右上「导入数据」，选择桌面版保存的 JSON（`project/nodes` 结构）
- 开发模式数据目录：`creo编号器-web/data/`；打包版：exe 旁 `data/`

## 编号规则（v2）

- 根图号：创建组件 → `根-00`、`-01`…（两位数字）
- 主机层（根的直接子级两位数字，如 `-00`）：只放字母组件（手动输入，如 `-ZBC`），**不创建零件**
- 字母组件（如 `-ZBC`）：
  - 创建组件 → 根前缀 + 两位数字（全局编号，从 01 起，如 `05S01101-01`）
  - 创建零件 → 宿主（字母组件的父级）的零件序列，所有字母组件共享（如 `05S01101-00-1`、`-00-2`）
- 普通数字组件（如 `-10`）：创建组件 → 追加法（`-1001`）；创建零件 → 分叉法（`-10-1`）
- 零件不能作为父级；组件图号不能以 `-数字` 结尾

## 测试

```bash
python -m unittest discover -s tests
```

## 数据

- 数据库文件：`data/numbering.db`（运行时自动创建）
- 导入桌面版数据：页面右上「导入数据」，选择桌面版保存的 JSON（`project/nodes` 结构）

## 目录结构

```text
creo编号器-web/
├── app/
│   ├── main.py          # FastAPI 入口与全部路由
│   ├── database.py      # SQLite 访问层
│   ├── numbering.py     # 编号核心逻辑包装（复用 creo编号器/core）
│   └── static/          # （预留）
├── web/                 # React + Vite 前端
│   └── dist/            # 构建产物（FastAPI 托管）
├── tests/test_api.py    # 后端 API 测试（unittest）
└── data/                # SQLite 数据库（运行时生成）
```

> 部署到服务器时，需连同 `creo编号器/core` 目录一起上传（`app/numbering.py` 依赖它）。
> 桌面版 `creo编号器/` 不纳入 git 管理，core 目录从本地开发机拷贝即可。
