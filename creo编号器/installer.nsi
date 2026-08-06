; Creo模型树自动取号器 安装脚本
; 使用NSIS编译

!include "MUI2.nsh"

; 安装程序属性
Name "Creo模型树自动取号器 v2.1"
OutFile "Creo编号器_安装程序.exe"
InstallDir "$PROGRAMFILES\CreoTools\Creo编号器"
InstallDirRegKey HKLM "Software\CreoTools\Creo编号器" "InstallDir"

; 请求管理员权限
RequestExecutionLevel admin

; 界面设置
!define MUI_ABORTWARNING
!define MUI_ICON "app_icon.ico"
!define MUI_UNICON "app_icon.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "app_icon.png"
!define MUI_WELCOMEFINISHPAGE_BITMAP "app_icon.png"

; 欢迎页面
!insertmacro MUI_PAGE_WELCOME

; 许可协议页面
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"

; 组件选择页面
!insertmacro MUI_PAGE_COMPONENTS

; 安装目录选择页面
!insertmacro MUI_PAGE_DIRECTORY

; 安装页面
!insertmacro MUI_PAGE_INSTFILES

; 完成页面
!insertmacro MUI_PAGE_FINISH

; 卸载确认页面
!insertmacro MUI_UNPAGE_CONFIRM

; 卸载页面
!insertmacro MUI_UNPAGE_INSTFILES

; 语言设置
!insertmacro MUI_LANGUAGE "SimpChinese"

; 安装-section
Section "Creo编号器 (必须)" SecMain
    SectionIn RO

    ; 设置输出路径
    SetOutPath "$INSTDIR"

    ; 安装文件
    File "dist\Creo编号器\Creo编号器.exe"
    File /r "dist\Creo编号器\_internal\*.*"

    ; 创建卸载程序
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; 写入注册表信息
    WriteRegStr HKLM "Software\CreoTools\Creo编号器" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\CreoTools\Creo编号器" "Version" "2.1.0"

    ; 创建开始菜单快捷方式
    CreateDirectory "$SMPROGRAMS\CreoTools"
    CreateShortCut "$SMPROGRAMS\CreoTools\Creo编号器.lnk" "$INSTDIR\Creo编号器.exe" "" "$INSTDIR\Creo编号器.exe"
    CreateShortCut "$SMPROGRAMS\CreoTools\卸载 Creo编号器.lnk" "$INSTDIR\uninstall.exe"

    ; 创建桌面快捷方式
    CreateShortCut "$DESKTOP\Creo编号器.lnk" "$INSTDIR\Creo编号器.exe" "" "$INSTDIR\Creo编号器.exe"

    ; 写入卸载信息
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器" "DisplayName" "Creo模型树自动取号器"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器" "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器" "DisplayIcon" '"$INSTDIR\Creo编号器.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器" "Publisher" "Creo Tools"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器" "NoModify" 1
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器" "NoRepair" 1
SectionEnd

; 可选组件
Section "桌面快捷方式" SecDesktop
    CreateShortCut "$DESKTOP\Creo编号器.lnk" "$INSTDIR\Creo编号器.exe" "" "$INSTDIR\Creo编号器.exe"
SectionEnd

Section "开始菜单快捷方式" SecStartMenu
    CreateDirectory "$SMPROGRAMS\CreoTools"
    CreateShortCut "$SMPROGRAMS\CreoTools\Creo编号器.lnk" "$INSTDIR\Creo编号器.exe" "" "$INSTDIR\Creo编号器.exe"
    CreateShortCut "$SMPROGRAMS\CreoTools\卸载 Creo编号器.lnk" "$INSTDIR\uninstall.exe"
SectionEnd

; 卸载-section
Section "Uninstall"
    ; 删除文件
    RMDir /r "$INSTDIR"

    ; 删除快捷方式
    Delete "$DESKTOP\Creo编号器.lnk"
    RMDir /r "$SMPROGRAMS\CreoTools"

    ; 删除注册表信息
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\Creo编号器"
    DeleteRegKey HKLM "Software\CreoTools\Creo编号器"
SectionEnd

; 组件描述
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecMain} "安装Creo编号器主程序"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "在桌面创建快捷方式"
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "在开始菜单创建快捷方式"
!insertmacro MUI_FUNCTION_DESCRIPTION_END
