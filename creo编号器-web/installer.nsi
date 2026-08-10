; Creo模型树自动取号器（Web 本地版）安装脚本
; 使用方法：安装 NSIS 后右键本文件 -> Compile NSIS Script，
; 或在命令行执行 makensis installer.nsi（需先执行 build.spec 打包）

!include "MUI2.nsh"

Name "Creo模型树自动取号器（Web 版）"
OutFile "Creo编号器Web_安装程序.exe"
; 默认安装到用户可写目录（无需管理员权限，数据可直接写入）
InstallDir "$LOCALAPPDATA\Programs\Creo编号器Web"
RequestExecutionLevel user

!define MUI_ABORTWARNING

!define MUI_DIRECTORYPAGE_TEXT_TOP "请选择您有写入权限的目录（例如 D:\Creo编号器Web）。请不要安装到 Program Files，否则程序将无法写入数据。"
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "安装位置"


!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"

Section "安装" SecMain
  SetOutPath "$INSTDIR"
  ; 打包产物（dist\Creo编号器Web\ 下的全部文件）
  File /r "dist\Creo编号器Web\*.*"

  ; 桌面快捷方式
  CreateShortcut "$DESKTOP\Creo模型树自动取号器.lnk" "$INSTDIR\Creo编号器Web.exe"

  ; 开始菜单
  CreateDirectory "$SMPROGRAMS\Creo模型树自动取号器"
  CreateShortcut "$SMPROGRAMS\Creo模型树自动取号器\Creo模型树自动取号器.lnk" "$INSTDIR\Creo编号器Web.exe"
  CreateShortcut "$SMPROGRAMS\Creo模型树自动取号器\卸载.lnk" "$INSTDIR\Uninstall.exe"

  ; 卸载信息
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web" "DisplayName" "Creo模型树自动取号器（Web 版）"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web" "DisplayIcon" "$INSTDIR\Creo编号器Web.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web" "Publisher" "Creo Tools"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web" "NoRepair" 1
SectionEnd

Section "Uninstall"
  ; 注意：data\ 目录存放业务数据，卸载时保留，不会删除
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$INSTDIR\Creo编号器Web.exe"
  RMDir /r "$INSTDIR\_internal"
  RMDir /r "$INSTDIR\logs"
  RMDir "$INSTDIR"

  Delete "$DESKTOP\Creo模型树自动取号器.lnk"
  RMDir /r "$SMPROGRAMS\Creo模型树自动取号器"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web"
SectionEnd
