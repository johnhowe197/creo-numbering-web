"""
Creo模型树自动取号器 - 主程序入口
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from ui import MainWindow


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    # 设置样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 15px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QLineEdit {
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 3px;
            font-size: 14px;
        }
        QLineEdit:focus {
            border: 1px solid #4CAF50;
        }
        QPushButton {
            padding: 8px 16px;
            border: 1px solid #ddd;
            border-radius: 3px;
            background-color: white;
        }
        QPushButton:hover {
            background-color: #e8e8e8;
        }
        QListWidget {
            border: 1px solid #ddd;
            border-radius: 3px;
            background-color: white;
        }
        QListWidget::item {
            padding: 5px;
        }
        QListWidget::item:selected {
            background-color: #e3f2fd;
        }
    """)

    # 创建并显示主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
