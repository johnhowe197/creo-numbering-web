"""
图号生成器 - 根据父级图号生成下一个可用图号
"""

import re
from typing import List, Tuple, Optional

from .parser import (
    parse_drawing_number,
    is_component,
    is_part,
    is_alpha_component,
    extract_components,
    extract_parts,
    extract_top_level_numbers,
    validate_parent
)


def get_next_component_number(parent_no: str, all_numbers: List[str]) -> Tuple[bool, str, str]:
    """
    生成下一个子组件图号（追加法）

    规则:
    - 如果父级无层级码（根图号）：父级图号 + "-00", "-01", "-02"...
    - 如果父级有层级码：父级图号 + 两位数字（01~99）

    Args:
        parent_no: 父级图号
        all_numbers: 所有已有图号列表

    Returns:
        Tuple[bool, str, str]: (是否成功, 新图号或错误信息, 新层级码)
    """
    # 验证父级
    valid, error = validate_parent(parent_no)
    if not valid:
        return False, error, ""

    # 解析父级图号
    parsed = parse_drawing_number(parent_no)
    is_root_no_dash = parsed['is_root']  # 无横杠的根图号

    # 提取现有子组件
    components = extract_components(parent_no, all_numbers)

    # 找出所有后缀数字
    suffix_numbers = []
    for comp in components:
        suffix = comp[len(parent_no):]
        # 对于无横杠根图号，后缀格式为 "-00", "-01"...
        if is_root_no_dash:
            # 去掉开头的横杠
            if suffix.startswith('-'):
                num_part = suffix[1:]
                if num_part.isdigit():
                    suffix_numbers.append(int(num_part))
        else:
            # 对于有层级码的父号，后缀为纯数字
            if suffix.isdigit():
                suffix_numbers.append(int(suffix))

    # 确定新数字
    if suffix_numbers:
        max_num = max(suffix_numbers)
        new_num = max_num + 1
    else:
        new_num = 0 if is_root_no_dash else 1  # 根图号从00开始，其他从01开始

    # 检查是否溢出
    if new_num > 99:
        return False, "组件层级已满（超过99个子组件）", ""

    # 生成新图号
    if is_root_no_dash:
        # 根图号无层级码，生成 "-00", "-01"...
        new_suffix = f"-{new_num:02d}"
        new_number = f"{parent_no}{new_suffix}"
    else:
        # 有层级码的父号，追加两位数字
        new_suffix = f"{new_num:02d}"
        new_number = f"{parent_no}{new_suffix}"

    return True, new_number, new_suffix


def get_next_part_number(parent_no: str, all_numbers: List[str]) -> Tuple[bool, str, str]:
    """
    生成下一个子零件图号（分叉法）

    规则: 父级图号 + `-` + 顺序数字（1, 2, 3...）

    Args:
        parent_no: 父级图号
        all_numbers: 所有已有图号列表

    Returns:
        Tuple[bool, str, str]: (是否成功, 新图号或错误信息, 新层级码)
    """
    # 验证父级
    valid, error = validate_parent(parent_no)
    if not valid:
        return False, error, ""

    # 提取现有子零件
    parts = extract_parts(parent_no, all_numbers)

    # 找出所有后缀数字
    suffix_numbers = []
    for part in parts:
        # 提取末尾数字
        match = re.search(r'-(\d+)$', part)
        if match:
            suffix_numbers.append(int(match.group(1)))

    # 确定新数字
    if suffix_numbers:
        max_num = max(suffix_numbers)
        new_num = max_num + 1
    else:
        new_num = 1

    # 生成新图号
    new_suffix = f"-{new_num}"
    new_number = f"{parent_no}{new_suffix}"

    return True, new_number, new_suffix


def get_next_top_component_number(prefix: str, all_numbers: List[str]) -> Tuple[bool, str, str]:
    """
    生成下一个「根前缀 + 两位数字」的全局组件图号（用于字母组件下的子组件）

    规则:
    - 扫描所有 prefix-XX（恰好两位数字）的图号，取最大值 + 1
    - 不存在时从 01 开始（字母组件下的数字组件从 01 起；根图号子组件仍从 00 起）
    - 深层追加图号（如 prefix-1001）不参与计算，避免序号冲突

    Args:
        prefix: 根前缀，如 "LS001"
        all_numbers: 所有已有图号列表

    Returns:
        Tuple[bool, str, str]: (是否成功, 新图号或错误信息, 新层级码)
    """
    top_numbers = extract_top_level_numbers(prefix, all_numbers)

    suffix_numbers = []
    for num in top_numbers:
        suffix = num[len(prefix) + 1:]
        if suffix.isdigit():
            suffix_numbers.append(int(suffix))

    if suffix_numbers:
        new_num = max(suffix_numbers) + 1
    else:
        new_num = 1  # 无任何两位数字图号时，从 01 开始

    if new_num > 99:
        return False, "组件层级已满（超过99个子组件）", ""

    new_suffix = f"-{new_num:02d}"
    new_number = f"{prefix}{new_suffix}"
    return True, new_number, new_suffix


def generate_number(parent_no: str, number_type: str, all_numbers: List[str]) -> Tuple[bool, str, str]:
    """
    统一入口：生成新图号

    Args:
        parent_no: 父级图号
        number_type: 类型 ('component' 或 'part')
        all_numbers: 所有已有图号列表

    Returns:
        Tuple[bool, str, str]: (是否成功, 新图号或错误信息, 新层级码)
    """
    if number_type == 'component':
        # 先验证父级（内部会捕获格式错误），避免非法图号抛异常
        valid, error = validate_parent(parent_no)
        if not valid:
            return False, error, ""
        # 含字母的组件（如 LS001-ZBC）没有数字递增顺序，其子组件使用
        # 「根前缀 + 两位数字」的全局编号；其余父级保持追加法
        if is_alpha_component(parent_no):
            prefix = parse_drawing_number(parent_no)['prefix']
            return get_next_top_component_number(prefix, all_numbers)
        return get_next_component_number(parent_no, all_numbers)
    elif number_type == 'part':
        return get_next_part_number(parent_no, all_numbers)
    else:
        return False, f"无效的图号类型: {number_type}", ""


def get_number_info(dwg_no: str, all_numbers: List[str]) -> dict:
    """
    获取图号详细信息

    Args:
        dwg_no: 图号
        all_numbers: 所有已有图号列表

    Returns:
        dict: 图号详细信息
    """
    parsed = parse_drawing_number(dwg_no)

    # 获取子组件和子零件
    children = [n for n in all_numbers if n.startswith(dwg_no) and n != dwg_no]
    components = extract_components(dwg_no, all_numbers)
    parts = extract_parts(dwg_no, all_numbers)

    return {
        'number': dwg_no,
        'prefix': parsed['prefix'],
        'level_code': parsed['level_code'],
        'is_part': parsed['is_part'],
        'is_component': is_component(dwg_no),
        'children_count': len(children),
        'components_count': len(components),
        'parts_count': len(parts),
        'components': components,
        'parts': parts
    }
