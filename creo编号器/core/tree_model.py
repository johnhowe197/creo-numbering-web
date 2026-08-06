"""
树形数据模型 - 管理Creo模型树的层级结构
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

from .parser import is_part


@dataclass
class TreeNode:
    """树节点数据结构"""
    number: str                    # 图号
    node_type: str                 # 类型: root, component, part
    name: str = ""                 # 名称
    parent: Optional[str] = None   # 父级图号
    children: List[str] = field(default_factory=list)  # 子节点图号列表
    memo: str = ""                 # 备忘录
    status_color: str = ""         # 状态颜色: "red"/"yellow"/"green"/"blue"/""
    created: str = field(default_factory=lambda: datetime.now().isoformat())

    def is_root(self) -> bool:
        return self.node_type == "root"

    def is_component(self) -> bool:
        return self.node_type == "component"

    def is_part(self) -> bool:
        return self.node_type == "part"

    def can_have_children(self) -> bool:
        """是否可以有子节点（只有组件和根可以）"""
        return self.node_type in ("root", "component")


class TreeModel:
    """树形数据模型"""

    def __init__(self):
        self.nodes: Dict[str, TreeNode] = {}
        self.root_number: Optional[str] = None
        self.project_name: Optional[str] = None
        self.file_path: Optional[str] = None

    def create_project(self, root_number: str, project_name: str = None):
        """创建新项目"""
        self.root_number = root_number
        self.project_name = project_name or root_number
        self.nodes.clear()

        # 判断根节点类型
        # 如果包含横杠，视为组件；否则视为根图号
        if '-' in root_number:
            node_type = "component"
        else:
            node_type = "root"

        # 创建根节点
        root = TreeNode(
            number=root_number,
            node_type=node_type,
            parent=None,
            children=[]
        )
        self.nodes[root_number] = root

    def get_node(self, number: str) -> Optional[TreeNode]:
        """获取节点"""
        return self.nodes.get(number)

    def get_root(self) -> Optional[TreeNode]:
        """获取根节点"""
        return self.nodes.get(self.root_number) if self.root_number else None

    def get_children(self, parent_number: str) -> List[TreeNode]:
        """获取子节点列表"""
        parent = self.get_node(parent_number)
        if not parent:
            return []
        return [self.nodes[child_num] for child_num in parent.children if child_num in self.nodes]

    def get_all_components(self, parent_number: str) -> List[TreeNode]:
        """获取所有子组件"""
        return [child for child in self.get_children(parent_number) if child.is_component()]

    def get_all_parts(self, parent_number: str) -> List[TreeNode]:
        """获取所有子零件"""
        return [child for child in self.get_children(parent_number) if child.is_part()]

    def add_component(self, parent_number: str, component_number: str) -> bool:
        """添加子组件"""
        parent = self.get_node(parent_number)
        if not parent or not parent.can_have_children():
            return False

        # 零件格式（以 -数字 结尾）不能作为组件，避免与零件混淆
        if is_part(component_number):
            return False

        # 检查图号是否已存在
        if component_number in self.nodes:
            return False

        # 创建新节点
        new_node = TreeNode(
            number=component_number,
            node_type="component",
            parent=parent_number,
            children=[]
        )

        # 更新父节点
        parent.children.append(component_number)
        self.nodes[component_number] = new_node

        return True

    def add_part(self, parent_number: str, part_number: str) -> bool:
        """添加子零件"""
        parent = self.get_node(parent_number)
        if not parent or not parent.can_have_children():
            return False

        # 零件图号必须以 -数字 结尾（如 05S01101-10-1）
        if not is_part(part_number):
            return False

        # 检查图号是否已存在
        if part_number in self.nodes:
            return False

        # 创建新节点
        new_node = TreeNode(
            number=part_number,
            node_type="part",
            parent=parent_number,
            children=[]
        )

        # 更新父节点
        parent.children.append(part_number)
        self.nodes[part_number] = new_node

        return True

    def remove_node(self, number: str) -> bool:
        """删除节点（包括所有子节点）"""
        node = self.get_node(number)
        if not node or node.is_root():
            return False

        # 递归删除子节点
        for child_num in node.children[:]:
            self.remove_node(child_num)

        # 从父节点中移除
        if node.parent and node.parent in self.nodes:
            parent = self.nodes[node.parent]
            if number in parent.children:
                parent.children.remove(number)

        # 删除节点
        del self.nodes[number]
        return True

    def move_node(self, node_number: str, new_parent_number: str) -> bool:
        """移动节点到新的父级"""
        node = self.get_node(node_number)
        new_parent = self.get_node(new_parent_number)

        if not node or not new_parent:
            return False

        if node.is_root():
            return False

        if not new_parent.can_have_children():
            return False

        # 不能移动到自己的子节点下
        if self._is_descendant(new_parent_number, node_number):
            return False

        # 从原父节点移除
        if node.parent and node.parent in self.nodes:
            old_parent = self.nodes[node.parent]
            if node_number in old_parent.children:
                old_parent.children.remove(node_number)

        # 添加到新父节点
        new_parent.children.append(node_number)
        node.parent = new_parent_number

        return True

    def _is_descendant(self, child_number: str, parent_number: str) -> bool:
        """检查是否是后代节点"""
        child = self.get_node(child_number)
        if not child:
            return False

        current = child
        while current and current.parent:
            if current.parent == parent_number:
                return True
            current = self.get_node(current.parent)

        return False

    def rename_node(self, old_number: str, new_number: str) -> bool:
        """重命名节点"""
        node = self.get_node(old_number)
        if not node or old_number == self.root_number:
            return False

        # 检查新图号是否已存在
        if new_number in self.nodes:
            return False

        # 类型一致性校验：组件不能改成零件格式，零件不能改成组件格式
        if node.is_component() and is_part(new_number):
            return False
        if node.is_part() and not is_part(new_number):
            return False

        # 更新父节点的children列表
        if node.parent and node.parent in self.nodes:
            parent = self.nodes[node.parent]
            idx = parent.children.index(old_number)
            parent.children[idx] = new_number

        # 更新所有子节点的parent引用
        for child_num in node.children:
            child = self.get_node(child_num)
            if child:
                child.parent = new_number

        # 重新映射节点
        node.number = new_number
        self.nodes[new_number] = node
        del self.nodes[old_number]

        return True

    def update_node_name(self, number: str, name: str) -> bool:
        """更新节点名称"""
        node = self.get_node(number)
        if not node:
            return False

        node.name = name
        return True

    def update_node_memo(self, number: str, memo: str) -> bool:
        """更新节点备忘录"""
        node = self.get_node(number)
        if not node:
            return False

        node.memo = memo
        return True

    def update_node_status_color(self, number: str, color: str) -> bool:
        """更新节点状态颜色"""
        node = self.get_node(number)
        if not node:
            return False

        # 验证颜色值
        valid_colors = ["", "red", "yellow", "green", "blue"]
        if color not in valid_colors:
            return False

        node.status_color = color
        return True

    def get_node_info(self, number: str) -> Dict[str, Any]:
        """获取节点详细信息"""
        node = self.get_node(number)
        if not node:
            return {}

        children = self.get_children(number)
        components = self.get_all_components(number)
        parts = self.get_all_parts(number)

        return {
            "number": node.number,
            "name": node.name,
            "type": node.node_type,
            "type_display": {"root": "根节点", "component": "组件", "part": "零件"}.get(node.node_type, "未知"),
            "parent": node.parent,
            "children_count": len(children),
            "components_count": len(components),
            "parts_count": len(parts),
            "memo": node.memo,
            "status_color": node.status_color,
            "created": node.created,
            "can_have_children": node.can_have_children()
        }

    def get_all_numbers(self) -> List[str]:
        """获取所有图号列表"""
        return list(self.nodes.keys())

    def get_statistics(self) -> Dict[str, int]:
        """获取统计信息"""
        components = sum(1 for n in self.nodes.values() if n.is_component())
        parts = sum(1 for n in self.nodes.values() if n.is_part())
        return {
            "total": len(self.nodes),
            "components": components,
            "parts": parts,
            "root": 1 if self.root_number else 0
        }

    def save(self, file_path: str = None) -> bool:
        """保存到文件"""
        if file_path:
            self.file_path = file_path

        if not self.file_path:
            return False

        data = {
            "project": {
                "name": self.project_name,
                "root": self.root_number,
                "saved_at": datetime.now().isoformat()
            },
            "nodes": {
                num: asdict(node) for num, node in self.nodes.items()
            }
        }

        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    def load(self, file_path: str) -> bool:
        """从文件加载"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.project_name = data.get("project", {}).get("name")
            self.root_number = data.get("project", {}).get("root")
            self.file_path = file_path

            self.nodes.clear()
            for num, node_data in data.get("nodes", {}).items():
                self.nodes[num] = TreeNode(**node_data)

            return True
        except Exception as e:
            print(f"加载失败: {e}")
            return False
