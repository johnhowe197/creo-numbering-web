# 发布备忘（Web 版）

本地打包 → GitHub Release 的完整流程。

## 发布流程

1. **更新版本号**：修改 `creo编号器-web/version_info.txt`（filevers / FileVersion / ProductVersion）。

2. **构建前端**（如改过 `web/src/`）：
   ```bash
   cd creo编号器-web/web
   npm run build
   ```

3. **PyInstaller 打包**（onedir）：
   ```bash
   cd creo编号器-web
   pyinstaller build.spec --clean --noconfirm
   ```
   产物：`dist\Creo编号器Web\`（含 `Creo编号器Web.exe`，绿色版可直接拷贝使用）。

4. **生成安装包**（需 NSIS）：
   ```bash
   cd creo编号器-web
   "D:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
   ```
   产物：`creo编号器-web\Creo编号器Web_安装程序.exe`。

5. **提交并推送代码**：
   ```bash
   git add -A
   git commit -m "发布 vX.Y.Z：..."
   git push
   ```

6. **发布 GitHub Release**（安装包用 ASCII 文件名，避免 gh 上传中文乱码）：
   ```bash
   Copy-Item 'creo编号器-web\Creo编号器Web_安装程序.exe' "C:\tmp\CreoNumberingWeb-Setup-vX.Y.Z.exe"
   gh release create vX.Y.Z "C:\tmp\CreoNumberingWeb-Setup-vX.Y.Z.exe" `
     --title "Creo 模型树自动取号器 Web 版 vX.Y.Z" `
     --notes "更新说明" `
     --target main
   ```

## 注意

- 安装包文件名使用 ASCII（如 `CreoNumberingWeb-Setup-v1.0.0.exe`），中文文件名会被 gh 上传成乱码。
- 安装包/构建产物不入 git（`.gitignore` 已忽略 `*.exe`、`dist/`、`build/`、`web/dist/`）。
- 安装包内不含业务数据；卸载程序保留安装目录 `data\`（业务数据不删除）。
- 安装时请选择**可写目录**（如 `D:\Creo编号器Web`），不要装到 Program Files。
