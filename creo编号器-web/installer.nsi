; Creo模型树自动取号器（Web 本地版）安装脚本
; 使用方法：安装 NSIS 后右键本文件 -> Compile NSIS Script，
; 或在命令行执行 makensis installer.nsi（需先执行 build.spec 打包）

!include "MUI2.nsh"
!include "FileFunc.nsh"

Name "Creo模型树自动取号器（Web 版）"
OutFile "Creo编号器Web_安装程序.exe"
; 默认安装到用户可写目录（无需管理员权限，数据可直接写入）
InstallDir "$LOCALAPPDATA\Programs\Creo编号器Web"
RequestExecutionLevel user

; 安装前：若检测到之前安装过的目录，自动沿用作为默认安装位置
Function .onInit
  ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web" "InstallLocation"
  ${If} $0 == ""
    ReadRegStr $0 HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web" "UninstallString"
    ${If} $0 != ""
      ; UninstallString 形如 "D:\...\Uninstall.exe"，去掉首尾引号后取所在目录
      StrCpy $1 "$0" "" 1
      StrCpy $1 "$1" -1
      ${GetParent} "$1" $0
    ${EndIf}
  ${EndIf}
  ${If} $0 != ""
    StrCpy $INSTDIR "$0"
  ${EndIf}
FunctionEnd

!define MUI_ABORTWARNING

!define MUI_DIRECTORYPAGE_TEXT_TOP "请选择您有写入权限的目录（例如 D:\Creo编号器Web）。请不要安装到 Program Files，否则程序将无法写入数据。"
!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "安装位置"

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"

Section "安装" SecMain
  ; 检测旧版是否在运行：是则提示用户确认后关闭，避免文件占用
  nsExec::ExecToStack 'powershell -NoProfile -Command "if (Get-Process -Name Creo编号器Web -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }"'
  Pop $0
  ${If} $0 == "1"
    MessageBox MB_YESNO|MB_ICONQUESTION "检测到 Creo模型树自动取号器正在运行。$\r$\n安装前需要关闭它，是否关闭并继续安装？" IDYES lbl_kill
    Abort
    lbl_kill:
    nsExec::ExecToStack 'powershell -NoProfile -Command "Stop-Process -Name Creo编号器Web -Force -ErrorAction SilentlyContinue"'
    Pop $0
    Sleep 500
  ${EndIf}

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
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web" "InstallLocation" "$INSTDIR"
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器Web" "NoRepair" 1
SectionEnd

Section "Uninstall"
  ; 检测并提示关闭正在运行的程序
  nsExec::ExecToStack 'powershell -NoProfile -Command "if (Get-Process -Name Creo编号器Web -ErrorAction SilentlyContinue) { exit 1 } else { exit 0 }"'
  Pop $0
  ${If} $0 == "1"
    MessageBox MB_YESNO|MB_ICONQUESTION "Creo模型树自动取号器正在运行，卸载前需要关闭它，是否关闭并继续？" IDYES lbl_ukill
    Abort
    lbl_ukill:
    nsExec::ExecToStack 'powershell -NoProfile -Command "Stop-Process -Name Creo编号器Web -Force -ErrorAction SilentlyContinue"'
    Pop $0
    Sleep 500
  ${EndIf}

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
