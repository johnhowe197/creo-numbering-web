"""
编号核心逻辑

复用桌面版 creo编号器/core 的解析与生成规则，保证 Web 版与桌面版行为一致。
服务器部署时需要把 creo编号器/core 一并带上。
"""

import sys
from pathlib import Path


def _resolve_core_dir() -> Path:
    """定位编号核心目录：
    1. 打包后（frozen）：解压目录下的 core
    2. 开发模式：Web 版目录内的 core（自包含，不依赖桌面版）
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "core"
    return Path(__file__).resolve().parent.parent / "core"


_CORE_DIR = _resolve_core_dir()
if str(_CORE_DIR) not in sys.path:
    sys.path.insert(0, str(_CORE_DIR))

from core import (  # noqa: E402
    parse_drawing_number,
    is_component,
    is_part,
    is_alpha_component,
    validate_parent,
    generate_number,
    get_next_component_number,
    get_next_part_number,
    get_next_top_component_number,
)


def get_prefix(number: str) -> str:
    """获取图号的根前缀"""
    return parse_drawing_number(number)["prefix"]


def next_component(parent_number: str, all_numbers: list) -> tuple[bool, str, str]:
    """生成下一个组件号（含字母组件下的全局编号规则）"""
    return generate_number(parent_number, "component", all_numbers)


def next_part(parent_number: str, all_numbers: list) -> tuple[bool, str, str]:
    """生成下一个零件号"""
    return generate_number(parent_number, "part", all_numbers)


def next_component_for_alpha(prefix: str, all_numbers: list) -> tuple[bool, str, str]:
    """
    生成字母组件下的下一个全局数字组件号（根前缀 + 两位数字，从 01 起）
    """
    return get_next_top_component_number(prefix, all_numbers)


def next_part_for_host(host_number: str, all_numbers: list) -> tuple[bool, str, str]:
    """
    生成字母组件下零件的宿主序列号（如 -00-1），所有字母组件共享
    """
    return get_next_part_number(host_number, all_numbers)


def validate_node_number(number: str) -> str:
    """
    校验手动输入的图号格式，返回错误信息；合法返回空串。
    """
    try:
        parse_drawing_number(number)
    except ValueError as e:
        return str(e)
    return ""


def is_host_level(parent_number: str, parent_parent: str | None, root_number: str) -> bool:
    """
    判断父级是否为「主机层」：根的直接子级、层级码为两位纯数字（如 -00）

    主机层只放字母组件（手动输入），不创建零件。
    仅「根图号（无横杠）开始」的项目存在主机层。
    """
    if "-" in root_number:
        return False
    if not parent_parent or parent_parent != root_number:
        return False
    parsed = parse_drawing_number(parent_number)
    if parsed["is_root"] or parsed["is_part"]:
        return False
    level_code = parsed["level_code"]
    return len(level_code) == 2 and level_code.isdigit()


def part_host_number(parent_number: str, parent_parent: str | None) -> str:
    """
    获取字母组件下零件的「宿主图号」

    字母组件（如 -ZBC）下创建的零件使用其父级图号的零件序列（如 -00-1），
    所有字母组件共享该序列。
    """
    if parent_parent:
        return parent_parent
    # 兜底：没有父级信息时退回字母组件自身
    return parent_number


__all__ = [
    "parse_drawing_number",
    "is_component",
    "is_part",
    "is_alpha_component",
    "validate_parent",
    "generate_number",
    "get_prefix",
    "next_component",
    "next_part",
    "next_component_for_alpha",
    "next_part_for_host",
    "validate_node_number",
    "is_host_level",
    "part_host_number",
]
