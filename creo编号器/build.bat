@echo off
echo ========================================
echo  Creo模型树自动取号器 - 构建脚本
echo ========================================
echo.

echo [1/3] 清理旧的构建文件...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "__pycache__" rmdir /s /q "__pycache__"

echo [2/3] 创建应用图标...
python create_icon.py
if errorlevel 1 (
    echo 图标创建失败！
    pause
    exit /b 1
)

echo [3/3] 开始打包...
pyinstaller build.spec --clean --noconfirm
if errorlevel 1 (
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo  构建完成！
echo ========================================
echo.
echo 输出目录: dist\Creo编号器
echo 可执行文件: dist\Creo编号器\Creo编号器.exe
echo.
pause
