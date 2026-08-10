"""
主窗口界面 - Creo模型树自动取号器（树形视图版本）
"""

import os
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QSplitter,
    QToolBar, QStatusBar, QLabel, QGroupBox,
    QMessageBox, QInputDialog, QMenu, QFileDialog,
    QSizePolicy, QTextEdit, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QSize, QMimeData, QRect
from PyQt6.QtGui import QFont, QIcon, QAction, QDrag, QColor, QBrush, QPainter, QPixmap

from core import (
    TreeModel, TreeNode,
    parse_drawing_number,
    validate_parent, generate_number,
    is_component, is_part, is_alpha_component, is_host_level
)


class TreeWidget(QTreeWidget):
    """自定义树形控件，支持拖拽"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)

    def startDrag(self, actions):
        """开始拖拽"""
        item = self.currentItem()
        if item and item.data(0, Qt.ItemDataRole.UserRole):
            drag = QDrag(self)
            mime_data = QMimeData()
            mime_data.setText(item.data(0, Qt.ItemDataRole.UserRole))
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.MoveAction)


class MainWindow(QMainWindow):
    """主窗口类"""

    def __init__(self):
        super().__init__()
        self.tree_model = TreeModel()
        self.is_modified = False  # 跟踪是否有未保存的修改
        self.init_ui()
        self.setup_connections()
        self.update_statistics()

    def init_ui(self):
        """初始化用户界面"""
        # 窗口设置
        self.setWindowTitle("Creo模型树自动取号器")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 创建工具栏
        self.create_toolbar()

        # 树形视图
        tree_group = QGroupBox("模型树")
        tree_layout = QVBoxLayout(tree_group)

        self.tree_widget = TreeWidget()
        self.tree_widget.setHeaderLabels(["图号", "名称", "备注", "状态"])
        self.tree_widget.setColumnWidth(0, 280)
        self.tree_widget.setColumnWidth(1, 200)
        self.tree_widget.setColumnWidth(2, 200)
        self.tree_widget.setColumnWidth(3, 50)
        self.tree_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        # 只允许双击编辑，选中时不编辑
        self.tree_widget.setEditTriggers(QTreeWidget.EditTrigger.DoubleClicked)
        # 启用根节点装饰器（展开/折叠按钮）
        self.tree_widget.setRootIsDecorated(True)
        # 设置选择模式
        self.tree_widget.setSelectionMode(QTreeWidget.SelectionMode.SingleSelection)
        # 设置焦点策略
        self.tree_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        tree_layout.addWidget(self.tree_widget)

        main_layout.addWidget(tree_group)

        # 状态栏
        self.statusBar().showMessage("就绪")

        # 统计标签
        self.stats_label = QLabel()
        self.statusBar().addPermanentWidget(self.stats_label)

    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar("工具栏")
        toolbar.setIconSize(QSize(16, 16))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # 新建项目
        self.new_action = QAction("新建项目", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(self.on_new_project)
        toolbar.addAction(self.new_action)

        # 打开项目
        self.open_action = QAction("打开项目", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.triggered.connect(self.on_open_project)
        toolbar.addAction(self.open_action)

        # 保存项目
        self.save_action = QAction("保存项目", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.triggered.connect(self.on_save_project)
        toolbar.addAction(self.save_action)

        toolbar.addSeparator()

        # 添加组件
        self.add_component_action = QAction("添加组件", self)
        self.add_component_action.setShortcut("Ctrl+Shift+C")
        self.add_component_action.triggered.connect(self.on_add_component)
        toolbar.addAction(self.add_component_action)

        # 添加零件
        self.add_part_action = QAction("添加零件", self)
        self.add_part_action.setShortcut("Ctrl+Shift+P")
        self.add_part_action.triggered.connect(self.on_add_part)
        toolbar.addAction(self.add_part_action)

        toolbar.addSeparator()

        # 删除节点
        self.delete_action = QAction("删除", self)
        self.delete_action.setShortcut("Delete")
        self.delete_action.triggered.connect(self.on_delete_node)
        toolbar.addAction(self.delete_action)

        # 重命名
        self.rename_action = QAction("重命名", self)
        self.rename_action.setShortcut("F2")
        self.rename_action.triggered.connect(self.on_rename_node)
        toolbar.addAction(self.rename_action)

        toolbar.addSeparator()

        # 展开全部
        self.expand_action = QAction("展开全部", self)
        self.expand_action.triggered.connect(lambda: self.tree_widget.expandAll())
        toolbar.addAction(self.expand_action)

        # 折叠全部
        self.collapse_action = QAction("折叠全部", self)
        self.collapse_action.triggered.connect(lambda: self.tree_widget.collapseAll())
        toolbar.addAction(self.collapse_action)

        toolbar.addSeparator()

        # 编辑备忘录
        self.memo_action = QAction("备忘录", self)
        self.memo_action.setShortcut("Ctrl+M")
        self.memo_action.triggered.connect(self.on_edit_memo)
        toolbar.addAction(self.memo_action)

        toolbar.addSeparator()

        # 颜色快捷键（隐藏动作）
        self.color_none_action = QAction("无色", self)
        self.color_none_action.setShortcut("Ctrl+0")
        self.color_none_action.triggered.connect(lambda: self.set_selected_color(""))
        self.addAction(self.color_none_action)

        self.color_red_action = QAction("红色", self)
        self.color_red_action.setShortcut("Ctrl+1")
        self.color_red_action.triggered.connect(lambda: self.set_selected_color("red"))
        self.addAction(self.color_red_action)

        self.color_yellow_action = QAction("黄色", self)
        self.color_yellow_action.setShortcut("Ctrl+2")
        self.color_yellow_action.triggered.connect(lambda: self.set_selected_color("yellow"))
        self.addAction(self.color_yellow_action)

        self.color_green_action = QAction("绿色", self)
        self.color_green_action.setShortcut("Ctrl+3")
        self.color_green_action.triggered.connect(lambda: self.set_selected_color("green"))
        self.addAction(self.color_green_action)

        self.color_blue_action = QAction("蓝色", self)
        self.color_blue_action.setShortcut("Ctrl+4")
        self.color_blue_action.triggered.connect(lambda: self.set_selected_color("blue"))
        self.addAction(self.color_blue_action)

    def setup_connections(self):
        """设置信号连接"""
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.tree_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree_widget.customContextMenuRequested.connect(self.on_context_menu)
        self.tree_widget.itemChanged.connect(self.on_item_changed)

    def on_new_project(self):
        """新建项目"""
        # 检查是否有未保存的修改
        if self.tree_model.nodes and not self.ask_save_changes():
            return

        # 选择创建方式
        options = ["从根图号开始（如：05S01101）", "从组件开始（如：05S01101-00）"]
        choice, ok = QInputDialog.getItem(
            self, "新建项目", "选择创建方式:", options, 0, False
        )

        if not ok:
            return

        if choice == options[0]:
            # 从根图号开始（不带横杠）
            root_number, ok = QInputDialog.getText(
                self, "新建项目", "请输入根图号（不带横杠，如：05S01101）:"
            )
        else:
            # 从组件开始（带横杠）
            root_number, ok = QInputDialog.getText(
                self, "新建项目", "请输入组件图号（带横杠，如：05S01101-00）:"
            )

        if ok and root_number:
            # 创建项目
            self.tree_model.create_project(root_number)
            self.refresh_tree()
            self.update_statistics()
            self.statusBar().showMessage(f"已创建项目: {root_number}")

    def on_open_project(self):
        """打开项目"""
        # 检查是否有未保存的修改
        if self.tree_model.nodes and not self.ask_save_changes():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "打开项目", "",
            "JSON文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            if self.tree_model.load(file_path):
                self.refresh_tree()
                self.update_statistics()
                self.statusBar().showMessage(f"已打开项目: {self.tree_model.project_name}")
            else:
                QMessageBox.warning(self, "错误", "无法打开项目文件")

    def on_save_project(self):
        """保存项目"""
        if not self.tree_model.file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存项目", f"{self.tree_model.project_name or 'project'}.json",
                "JSON文件 (*.json)"
            )
            if not file_path:
                return
        else:
            file_path = self.tree_model.file_path

        if self.tree_model.save(file_path):
            self.is_modified = False  # 保存成功，重置修改标志
            self.statusBar().showMessage(f"项目已保存: {file_path}")
        else:
            QMessageBox.warning(self, "错误", "保存失败")

    def on_add_component(self):
        """添加子组件"""
        parent_item = self.tree_widget.currentItem()
        if not parent_item:
            QMessageBox.warning(self, "警告", "请先选择一个父节点")
            return

        parent_number = parent_item.data(0, Qt.ItemDataRole.UserRole)
        parent_node = self.tree_model.get_node(parent_number)

        if not parent_node or not parent_node.can_have_children():
            QMessageBox.warning(self, "警告", "该节点不能添加子组件")
            return

        existing = self.tree_model.get_all_numbers()

        # 主机层（如 -00）：只手动输入字母组件（ZBC/KTC 等）
        if is_host_level(parent_number, parent_node.parent, self.tree_model.root_number):
            prefix = parse_drawing_number(self.tree_model.root_number)["prefix"]
            new_number, ok = QInputDialog.getText(
                self, "添加组件",
                f"{parent_number} 为主机层，请输入字母组件图号"
                f"（如 {prefix}-ZBC、{prefix}-KTC）:\n父级: {parent_number}",
                text=""
            )
            if not ok or not new_number.strip():
                return
            new_number = new_number.strip()
            error = self._validate_manual_component(new_number)
            if error:
                QMessageBox.warning(self, "错误", error)
                return
        else:
            # 选择添加方式：自动生成（默认）或手动输入（支持字母图号，如 ZBC）
            options = ["自动生成图号", "手动输入图号"]
            choice, ok = QInputDialog.getItem(
                self, "添加组件", "选择添加方式:", options, 0, False
            )
            if not ok:
                return

            if choice == options[0]:
                # 自动生成：
                # - 字母组件（如 LS001-ZBC）下 → 根前缀 + 两位数字全局编号（LS001-01、02...）
                # - 数字组件（如 LS001-10）下 → 追加法（LS001-1001、1002...）
                # - 根图号下 → LS001-00 开始
                success, new_number, _ = generate_number(parent_number, "component", existing)
                if not success:
                    QMessageBox.warning(self, "错误", new_number)
                    return
            else:
                # 手动输入：支持字母图号，默认给出自动计算的建议值
                _, default_number, _ = generate_number(parent_number, "component", existing)
                new_number, ok = QInputDialog.getText(
                    self, "添加组件",
                    f"请输入子组件图号（可含字母）:\n父级: {parent_number}",
                    text=default_number or ""
                )
                if not ok or not new_number.strip():
                    return
                new_number = new_number.strip()

                error = self._validate_manual_component(new_number)
                if error:
                    QMessageBox.warning(self, "错误", error)
                    return

        # 添加组件
        if self.tree_model.add_component(parent_number, new_number):
            self.is_modified = True  # 标记有修改
            self.refresh_tree()
            self.update_statistics()
            self.statusBar().showMessage(f"已添加组件: {new_number}")

            # 保持在父节点位置
            self.select_node_by_number(parent_number)
        else:
            QMessageBox.warning(self, "错误", "添加组件失败")

    def on_add_part(self):
        """添加子零件"""
        parent_item = self.tree_widget.currentItem()
        if not parent_item:
            QMessageBox.warning(self, "警告", "请先选择一个父节点")
            return

        parent_number = parent_item.data(0, Qt.ItemDataRole.UserRole)
        parent_node = self.tree_model.get_node(parent_number)

        if not parent_node or not parent_node.can_have_children():
            QMessageBox.warning(self, "警告", "该节点不能添加子零件")
            return

        # 主机层（如 -00）：不创建零件
        if is_host_level(parent_number, parent_node.parent, self.tree_model.root_number):
            QMessageBox.warning(
                self, "警告",
                f"{parent_number} 为主机层，不创建零件，"
                "零件请添加到其下的字母组件（如 -ZBC）中"
            )
            return

        # 获取所有已有图号
        existing = self.tree_model.get_all_numbers()

        # 字母组件下创建零件：使用宿主（字母组件的父级）的共享零件序列
        host_number = None
        if is_alpha_component(parent_number) and parent_node and parent_node.parent:
            host_number = parent_node.parent

        # 选择添加方式：自动生成（默认）或手动输入
        options = ["自动生成图号", "手动输入图号"]
        choice, ok = QInputDialog.getItem(
            self, "添加零件", "选择添加方式:", options, 0, False
        )
        if not ok:
            return

        if choice == options[0]:
            # 自动生成：父级图号 + "-序号"（分叉法）；字母组件用宿主序列
            success, new_number, _ = generate_number(
                parent_number, "part", existing, host_number=host_number
            )
            if not success:
                QMessageBox.warning(self, "错误", new_number)
                return
        else:
            # 手动输入：零件图号必须以 -数字 结尾，默认给出自动计算的建议值
            _, default_number, _ = generate_number(
                parent_number, "part", existing, host_number=host_number
            )
            new_number, ok = QInputDialog.getText(
                self, "添加零件",
                f"请输入子零件图号（以 -数字 结尾）:\n父级: {parent_number}",
                text=default_number or ""
            )
            if not ok or not new_number.strip():
                return
            new_number = new_number.strip()

            error = self._validate_manual_part(
                new_number, parent_number, host_number=host_number
            )
            if error:
                QMessageBox.warning(self, "错误", error)
                return

        # 添加零件
        if self.tree_model.add_part(parent_number, new_number):
            self.is_modified = True  # 标记有修改
            self.refresh_tree()
            self.update_statistics()
            self.statusBar().showMessage(f"已添加零件: {new_number}")

            # 保持在父节点位置
            self.select_node_by_number(parent_number)
        else:
            QMessageBox.warning(self, "错误", "添加零件失败")

    def _validate_manual_component(self, new_number: str) -> Optional[str]:
        """校验手动输入的组件图号，返回错误信息或 None"""
        if new_number in self.tree_model.nodes:
            return "图号已存在"
        if is_part(new_number):
            return "该图号以 -数字 结尾，属于零件格式，不能作为组件"
        try:
            parse_drawing_number(new_number)
        except ValueError as e:
            return str(e)
        root_number = self.tree_model.root_number
        if root_number:
            # 根前缀：项目从根图号开始（如 LS001）或从组件开始（如 LS001-00）都取其前缀
            prefix = parse_drawing_number(root_number)["prefix"]
            if not (new_number == root_number or new_number.startswith(prefix + "-")):
                return f"组件图号应以根前缀 {prefix} 开头"
        return None

    def _validate_manual_part(
        self, new_number: str, parent_number: str, host_number: Optional[str] = None
    ) -> Optional[str]:
        """校验手动输入的零件图号，返回错误信息或 None"""
        if new_number in self.tree_model.nodes:
            return "图号已存在"
        if not is_part(new_number):
            return "零件图号必须以 -数字 结尾（如 05S01101-10-1）"
        try:
            parse_drawing_number(new_number)
        except ValueError as e:
            return str(e)
        prefix = host_number or parent_number
        if not new_number.startswith(prefix + "-"):
            return f"零件图号应以{prefix}- 开头"
        return None

    def on_delete_node(self):
        """删除节点"""
        parent_item = self.tree_widget.currentItem()
        if not parent_item:
            return

        node_number = parent_item.data(0, Qt.ItemDataRole.UserRole)
        node = self.tree_model.get_node(node_number)

        if not node or node.is_root():
            QMessageBox.warning(self, "警告", "不能删除根节点")
            return

        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除节点 {node_number} 及其所有子节点吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.tree_model.remove_node(node_number):
                self.is_modified = True  # 标记有修改
                self.refresh_tree()
                self.update_statistics()
                self.statusBar().showMessage(f"已删除节点: {node_number}")

    def on_rename_node(self):
        """重命名节点"""
        parent_item = self.tree_widget.currentItem()
        if not parent_item:
            return

        old_number = parent_item.data(0, Qt.ItemDataRole.UserRole)
        node = self.tree_model.get_node(old_number)

        if not node or node.is_root():
            QMessageBox.warning(self, "警告", "不能重命名根节点")
            return

        new_number, ok = QInputDialog.getText(
            self, "重命名", "请输入新的图号:",
            text=old_number
        )

        if not ok or not new_number.strip():
            return
        new_number = new_number.strip()
        if new_number == old_number:
            return

        # 细化校验与提示
        error = self._validate_rename(new_number, node)
        if error:
            QMessageBox.warning(self, "错误", error)
            return

        if self.tree_model.rename_node(old_number, new_number):
            self.is_modified = True  # 标记有修改
            self.refresh_tree()
            self.update_statistics()
            self.select_node(new_number)
            self.statusBar().showMessage(f"已重命名: {old_number} -> {new_number}")
        else:
            QMessageBox.warning(self, "错误", "重命名失败，请检查图号格式或是否已存在")

    def _validate_rename(self, new_number: str, node) -> Optional[str]:
        """校验重命名的新图号，返回错误信息或 None"""
        if new_number in self.tree_model.nodes:
            return f"图号已存在：{new_number}"
        try:
            parse_drawing_number(new_number)
        except ValueError as e:
            return str(e)
        if node.is_component() and is_part(new_number):
            return "组件图号不能以 -数字 结尾（该格式为零件）"
        if node.is_part() and not is_part(new_number):
            return "零件图号必须以 -数字 结尾（如 05S01101-10-1）"
        root_number = self.tree_model.root_number
        if root_number:
            prefix = parse_drawing_number(root_number)["prefix"]
            if not new_number.startswith(prefix + "-"):
                return f"图号应以根前缀 {prefix}- 开头"
        return None

    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """点击节点"""
        pass

    def on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """双击节点"""
        if column == 0:  # 双击图号列，重命名
            self.on_rename_node()

    def on_item_changed(self, item: QTreeWidgetItem, column: int):
        """节点内容改变（编辑名称或备注）"""
        node_number = item.data(0, Qt.ItemDataRole.UserRole)
        if not node_number:
            return

        if column == 1:  # 名称列
            new_name = item.text(1)
            self.tree_model.update_node_name(node_number, new_name)
            self.is_modified = True
            self.statusBar().showMessage(f"已更新名称: {node_number}")
        elif column == 2:  # 备注列
            new_memo = item.text(2)
            self.tree_model.update_node_memo(node_number, new_memo)
            self.is_modified = True
            self.statusBar().showMessage(f"已更新备注: {node_number}")

    def on_edit_memo(self):
        """编辑备忘录"""
        item = self.tree_widget.currentItem()
        if not item:
            QMessageBox.warning(self, "警告", "请先选择一个节点")
            return

        node_number = item.data(0, Qt.ItemDataRole.UserRole)
        node = self.tree_model.get_node(node_number)
        if not node:
            return

        # 创建备忘录编辑对话框
        dialog = MemoDialog(self, node_number, node.memo)
        if dialog.exec():
            new_memo = dialog.get_memo()
            if self.tree_model.update_node_memo(node_number, new_memo):
                self.is_modified = True
                self.refresh_tree()
                self.select_node(node_number)
                self.statusBar().showMessage(f"已更新备忘录: {node_number}")

    def on_context_menu(self, position):
        """右键菜单"""
        item = self.tree_widget.itemAt(position)
        if not item:
            return

        node_number = item.data(0, Qt.ItemDataRole.UserRole)
        node = self.tree_model.get_node(node_number)

        menu = QMenu(self)

        if node and node.can_have_children():
            add_component_action = menu.addAction("添加组件")
            add_component_action.triggered.connect(self.on_add_component)

            add_part_action = menu.addAction("添加零件")
            add_part_action.triggered.connect(self.on_add_part)

            menu.addSeparator()

        if node and not node.is_root():
            delete_action = menu.addAction("删除")
            delete_action.triggered.connect(self.on_delete_node)

            rename_action = menu.addAction("重命名")
            rename_action.triggered.connect(self.on_rename_node)

            menu.addSeparator()

        # 备忘录和颜色标记（所有节点都可以）
        if node:
            memo_action = menu.addAction("编辑备忘录")
            memo_action.triggered.connect(self.on_edit_memo)

            # 颜色子菜单
            color_menu = menu.addMenu("设置颜色")
            color_names = [("无色", ""), ("红色", "red"), ("黄色", "yellow"), ("绿色", "green"), ("蓝色", "blue")]
            for color_name, color_value in color_names:
                action = color_menu.addAction(color_name)
                action.triggered.connect(lambda checked, c=color_value: self.set_node_color(node_number, c))

        menu.exec(self.tree_widget.viewport().mapToGlobal(position))

    def set_node_color(self, node_number: str, color: str):
        """设置节点颜色"""
        if self.tree_model.update_node_status_color(node_number, color):
            self.is_modified = True
            self.refresh_tree()
            self.select_node(node_number)
            color_display = {"": "无", "red": "红色", "yellow": "黄色", "green": "绿色", "blue": "蓝色"}
            self.statusBar().showMessage(f"已设置颜色: {color_display.get(color, color)}")

    def set_selected_color(self, color: str):
        """为当前选中节点设置颜色"""
        item = self.tree_widget.currentItem()
        if not item:
            return
        node_number = item.data(0, Qt.ItemDataRole.UserRole)
        if node_number:
            self.set_node_color(node_number, color)

    def refresh_tree(self):
        """刷新树形视图"""
        # 记录当前展开状态
        expanded_items = set()
        self._save_expanded_state(self.tree_widget.invisibleRootItem(), expanded_items)

        self.tree_widget.clear()

        if not self.tree_model.root_number:
            return

        # 递归添加节点
        self._add_node_to_tree(self.tree_model.root_number, None)

        # 恢复展开状态或默认展开前两层
        if expanded_items:
            self._restore_expanded_state(self.tree_widget.invisibleRootItem(), expanded_items)
        else:
            self.tree_widget.expandToDepth(1)

    def _save_expanded_state(self, item, expanded_set):
        """保存展开状态"""
        for i in range(item.childCount()):
            child = item.child(i)
            if child.isExpanded():
                node_num = child.data(0, Qt.ItemDataRole.UserRole)
                if node_num:
                    expanded_set.add(node_num)
                self._save_expanded_state(child, expanded_set)

    def _restore_expanded_state(self, item, expanded_set):
        """恢复展开状态"""
        for i in range(item.childCount()):
            child = item.child(i)
            node_num = child.data(0, Qt.ItemDataRole.UserRole)
            if node_num and node_num in expanded_set:
                child.setExpanded(True)
            self._restore_expanded_state(child, expanded_set)

    def _add_node_to_tree(self, node_number: str, parent_item: Optional[QTreeWidgetItem]):
        """递归添加节点到树"""
        node = self.tree_model.get_node(node_number)
        if not node:
            return

        # 创建树节点项
        item = QTreeWidgetItem()

        # 根据节点类型设置颜色（更柔和的颜色）
        if node.is_root():
            bg_color = QColor(230, 240, 255)       # 柔和蓝色背景
        elif node.is_component():
            bg_color = QColor(230, 250, 230)       # 柔和绿色背景
        else:
            bg_color = QColor(255, 248, 230)       # 柔和黄色背景

        item.setText(0, node_number)
        item.setText(1, node.name)
        item.setText(2, node.memo)
        item.setText(3, "")  # 状态列

        # 设置item的flags：只允许编辑名称列（第1列）和备注列（第2列）
        flags = item.flags()
        # 第0列（图号）不可编辑
        # 第1列（名称）可编辑
        # 第2列（备注）可编辑
        # 第3列（状态）不可编辑
        item.setFlags(flags | Qt.ItemFlag.ItemIsEditable)

        # 设置数据
        item.setData(0, Qt.ItemDataRole.UserRole, node_number)

        # 设置文字颜色（深色，确保选中时也能看清）
        item.setForeground(0, QColor(30, 30, 30))
        item.setForeground(1, QColor(50, 50, 50))
        item.setForeground(2, QColor(80, 80, 80))  # 备注用浅灰色

        # 设置背景颜色
        item.setBackground(0, bg_color)
        item.setBackground(1, bg_color)
        item.setBackground(2, bg_color)
        item.setBackground(3, bg_color)

        # 设置状态列的圆形图标
        if node.status_color:
            color_map = {
                "red": QColor(255, 0, 0),
                "yellow": QColor(255, 255, 0),
                "green": QColor(0, 180, 0),
                "blue": QColor(0, 0, 255)
            }
            color = color_map.get(node.status_color)
            if color:
                # 创建圆形图标
                pixmap = QPixmap(20, 20)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(2, 2, 16, 16)
                painter.end()
                item.setIcon(3, QIcon(pixmap))

        # 设置字体
        font = item.font(0)
        font.setBold(node.is_root())
        item.setFont(0, font)

        # 添加到树
        if parent_item is None:
            self.tree_widget.addTopLevelItem(item)
        else:
            parent_item.addChild(item)

        # 递归添加子节点
        for child_number in node.children:
            self._add_node_to_tree(child_number, item)

    def select_node(self, node_number: str):
        """选中指定节点（通过图号）"""
        self.select_node_by_number(node_number)

    def select_node_by_number(self, node_number: str):
        """通过图号选中节点"""
        # 遍历所有顶层项目
        for i in range(self.tree_widget.topLevelItemCount()):
            item = self.tree_widget.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == node_number:
                self.tree_widget.setCurrentItem(item)
                self.tree_widget.scrollToItem(item)
                return
            # 递归查找子节点
            found = self._find_item_by_number(item, node_number)
            if found:
                self.tree_widget.setCurrentItem(found)
                self.tree_widget.scrollToItem(found)
                return

    def _find_item_by_number(self, item: QTreeWidgetItem, node_number: str) -> Optional[QTreeWidgetItem]:
        """递归查找节点"""
        for i in range(item.childCount()):
            child = item.child(i)
            if child.data(0, Qt.ItemDataRole.UserRole) == node_number:
                return child
            found = self._find_item_by_number(child, node_number)
            if found:
                return found
        return None

    def update_statistics(self):
        """更新统计信息"""
        stats = self.tree_model.get_statistics()
        self.stats_label.setText(
            f"节点数: {stats['total']} | "
            f"组件: {stats['components']} | "
            f"零件: {stats['parts']}"
        )

    def ask_save_changes(self) -> bool:
        """询问是否保存修改"""
        reply = QMessageBox.question(
            self, "保存修改",
            "当前项目有未保存的修改，是否保存？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.on_save_project()
            return True
        elif reply == QMessageBox.StandardButton.No:
            return True
        else:
            return False

    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.is_modified:
            if not self.ask_save_changes():
                event.ignore()
                return
        event.accept()


class MemoDialog(QDialog):
    """备忘录编辑对话框"""

    def __init__(self, parent=None, node_number: str = "", current_memo: str = ""):
        super().__init__(parent)
        self.node_number = node_number
        self.setWindowTitle(f"备忘录 - {node_number}")
        self.setMinimumSize(400, 300)

        # 创建布局
        layout = QVBoxLayout(self)

        # 提示标签
        label = QLabel("请输入备忘内容：")
        layout.addWidget(label)

        # 文本编辑框
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(current_memo)
        self.text_edit.setPlaceholderText("输入设计需求、待办事项等...")
        layout.addWidget(self.text_edit)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_memo(self) -> str:
        """获取备忘录内容"""
        return self.text_edit.toPlainText().strip()
