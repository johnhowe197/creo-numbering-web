# 构建和安装指南

## 快速构建

### 方法1：使用构建脚本（推荐）

```batch
build.bat
```

这将自动：
1. 清理旧的构建文件
2. 创建应用图标
3. 使用PyInstaller打包

### 方法2：手动构建

```batch
# 1. 安装依赖
pip install -r requirements.txt
pip install pyinstaller pillow

# 2. 创建图标
python create_icon.py

# 3. 打包
pyinstaller build.spec --clean --noconfirm
```

## 构建输出

构建完成后，在 `dist/Creo编号器/` 目录下会生成：

```
dist/Creo编号器/
├── Creo编号器.exe      # 主程序
└── _internal/          # 依赖文件
    ├── ...
    └── ...
```

## 创建安装程序

### 使用NSIS（推荐）

1. 下载并安装 [NSIS](https://nsis.sourceforge.io/)
2. 右键点击 `installer.nsi`
3. 选择 "Compile NSIS Script"
4. 生成的安装程序在当前目录

### 使用批处理脚本

```batch
# 如果已安装NSIS
makensis installer.nsi
```

## 安装程序功能

安装程序提供：

- ✅ 安装到 Program Files
- ✅ 创建桌面快捷方式
- ✅ 创建开始菜单快捷方式
- ✅ 注册到Windows卸载程序
- ✅ 支持静默安装

## 静默安装

```batch
Creo编号器_安装程序.exe /S
```

## 卸载

通过控制面板 → 程序和功能 → Creo模型树自动取号器

或运行安装目录下的 `uninstall.exe`

## 分发

### 最小分发

只需分发 `dist/Creo编号器/` 目录下的所有文件。

### 完整分发

使用NSIS创建的安装程序。

## 系统要求

- Windows 10/11
- 无需安装Python或其他依赖

## 常见问题

### Q: 打包后的程序无法运行？

A: 确保所有依赖都已正确安装，并且使用了正确的Python版本。

### Q: 如何更新版本？

A: 修改 `version_info.txt` 中的版本号，然后重新构建。

### Q: 如何自定义图标？

A: 替换 `app_icon.ico` 文件，然后重新构建。
