# Creo模型树自动取号器（桌面版）

用于 Creo 模型树图号自动编号的桌面应用程序（PyQt6，树形界面，数据存本地 JSON）。
编号规则 v2 支持组件追加法、零件分叉法、字母组件与主机层。

> Web 版（数据存服务器、支持多电脑共享）见 `../creo编号器-web/`。

## 快速开始

```bash
pip install -r requirements.txt
python start.py        # 或双击 run.bat
```

## 文档导航

详细文档已归档到 `docs/`：

| 文档 | 说明 |
|---|---|
| `docs/USER_GUIDE.md` | 使用说明（树形界面、编号规则 v2、快捷键） |
| `docs/INSTALL.md` | 安装与运行指南 |
| `docs/BUILD.md` | EXE 打包与安装程序构建 |
| `docs/TESTING.md` | 测试框架与用例说明 |
| `docs/SUMMARY.md` | 项目开发总结 |
| `docs/LICENSE.txt` | 许可证 |

编号规则完整说明见仓库根目录
`Creo 模型树图号层级与编号规则（开发说明）.md`；
业务编码规范见仓库根目录 `命名规范.md`。

## 目录结构

```text
creo编号器/
├── start.py / main.py     # 程序入口（start.py 为 v2 推荐入口）
├── run.bat                # Windows 启动脚本
├── core/                  # 核心逻辑（解析、生成、树模型）
├── ui/                    # PyQt6 界面
├── docs/                  # 文档归档
├── test_core.py           # 核心功能测试
├── harness.py             # 测试框架（含 test_cases.json）
├── build.spec / build.bat # PyInstaller 打包
├── installer.nsi          # NSIS 安装程序
└── version_info.txt       # 版本信息（打包用）
```
