"""
图号解析器 - 解析Creo模型树图号结构
"""

import re
from typing import Optional, Tuple


def parse_drawing_number(dwg_no: str) -> dict:
    """
    解析图号结构

    Args:
        dwg_no: 图号字符串，如 "03S01201-100101" 或 "05S01101"

    Returns:
        dict: {
            'prefix': str,      # 固定前缀，如 "03S01201"
            'level_code': str,  # 层级码，如 "100101" 或 ""（根图号无层级码）
            'is_part': bool,    # 是否为零件
            'is_root': bool,    # 是否为根图号（无层级码）
            'full_number': str  # 完整图号
        }
    """
    # 检查是否包含横杠
    if '-' not in dwg_no:
        # 无横杠，视为根图号
        return {
            'prefix': dwg_no,
            'level_code': '',
            'is_part': False,
            'is_root': True,
            'full_number': dwg_no
        }

    # 匹配格式: 前缀-层级码
    match = re.match(r'^([A-Za-z0-9]+)-(.+)$', dwg_no)
    if not match:
        raise ValueError(f"无效的图号格式: {dwg_no}")

    prefix = match.group(1)
    level_code = match.group(2)

    # 判断是否为零件
    # 零件特征：末尾为 -数字
    is_part = bool(re.search(r'-\d+$', level_code))

    return {
        'prefix': prefix,
        'level_code': level_code,
        'is_part': is_part,
        'is_root': False,
        'full_number': dwg_no
    }


def is_component(dwg_no: str) -> bool:
    """
    判断图号是否为组件（纯数字层级码）

    Args:
        dwg_no: 图号字符串

    Returns:
        bool: 是否为组件
    """
    parsed = parse_drawing_number(dwg_no)
    # 零件不是组件；根图号（无层级码）也不算组件（由 node_type='root' 区分）
    if parsed['is_part'] or parsed['level_code'] == '':
        return False
    # 组件层级码可以是纯数字（如 100101），也可以是字母（如 ZBC、KTC）
    return True


def is_alpha_component(dwg_no: str) -> bool:
    """
    判断图号是否为含字母的组件（层级码中包含字母，如 ZBC、KTC）

    这类组件没有自然的数字递增顺序，其下新建组件时使用「根前缀 + 两位数字」的全局编号。

    Args:
        dwg_no: 图号字符串

    Returns:
        bool: 是否为含字母的组件
    """
    parsed = parse_drawing_number(dwg_no)
    if parsed['is_part'] or parsed['level_code'] == '':
        return False
    return any(c.isalpha() for c in parsed['level_code'])


def is_host_level(parent_number: str, parent_parent: Optional[str], root_number: str) -> bool:
    """
    判断是否为「主机层」：根的直接子级、层级码为两位纯数字（如 -00）

    主机层只放字母组件（手动输入），不创建零件。

    Args:
        parent_number: 父级图号（候选主机层节点）
        parent_parent: 父级图号的父级（树模型中的 parent 引用）
        root_number: 项目根图号

    Returns:
        bool: 是否为主机层
    """
    if not parent_parent or parent_parent != root_number:
        return False
    parsed = parse_drawing_number(parent_number)
    if parsed['is_root'] or parsed['is_part']:
        return False
    level_code = parsed['level_code']
    return len(level_code) == 2 and level_code.isdigit()


def is_part(dwg_no: str) -> bool:
    """
    判断图号是否为零件（末尾为 -数字）

    Args:
        dwg_no: 图号字符串

    Returns:
        bool: 是否为零件
    """
    parsed = parse_drawing_number(dwg_no)
    return parsed['is_part']


def get_parent_number(dwg_no: str) -> Optional[str]:
    """
    获取父级图号

    对于零件: 去掉末尾的 -数字
    对于组件: 返回None（组件本身就是父级）

    Args:
        dwg_no: 图号字符串

    Returns:
        str or None: 父级图号
    """
    if is_part(dwg_no):
        # 零件的父级是去掉末尾 -数字
        match = re.match(r'^(.*)-\d+$', dwg_no)
        if match:
            return match.group(1)
    return None


def extract_components(dwg_no: str, all_numbers: list) -> list:
    """
    提取指定图号下的直接子组件（不包括后代）

    Args:
        dwg_no: 父级图号
        all_numbers: 所有图号列表

    Returns:
        list: 直接子组件图号列表
    """
    components = []
    parsed_parent = parse_drawing_number(dwg_no)
    is_root_no_dash = parsed_parent['is_root']

    for num in all_numbers:
        if num.startswith(dwg_no) and num != dwg_no:
            suffix = num[len(dwg_no):]

            if is_root_no_dash:
                # 根图号无横杠，子组件格式为 "-00", "-01"...
                # 直接子组件：后缀为 "-XX"（2位数字）
                if re.match(r'^-\d{2}$', suffix):
                    components.append(num)
            else:
                # 有层级码的父号，直接子组件为2位数字后缀
                # 例如：05S01101-11 的直接子组件是 05S01101-1101（后缀01）
                # 但 05S01101-110101 不是直接子组件（后缀0101是4位）
                if re.match(r'^\d{2}$', suffix):
                    components.append(num)
    return components


def extract_parts(dwg_no: str, all_numbers: list) -> list:
    """
    提取指定图号下的所有子零件

    Args:
        dwg_no: 父级图号
        all_numbers: 所有图号列表

    Returns:
        list: 子零件图号列表
    """
    parts = []
    for num in all_numbers:
        if num.startswith(f"{dwg_no}-"):
            # 检查是否为零件（-数字结尾）
            suffix = num[len(dwg_no):]
            if re.match(r'^-\d+$', suffix):
                parts.append(num)
    return parts


def extract_top_level_numbers(prefix: str, all_numbers: list) -> list:
    """
    提取根前缀下的所有两位数字图号（形如 prefix-00、prefix-01 ... prefix-99）

    用于字母组件（如 LS001-ZBC）或根图号下新建组件时的全局编号计算。
    只匹配恰好两位数字的图号，深层追加图号（如 prefix-1001）不会被误算。

    Args:
        prefix: 根前缀，如 "LS001"
        all_numbers: 所有图号列表

    Returns:
        list: 两位数字图号列表
    """
    result = []
    for num in all_numbers:
        if num.startswith(prefix + '-') and num != prefix:
            suffix = num[len(prefix) + 1:]
            if re.match(r'^\d{2}$', suffix):
                result.append(num)
    return result


def validate_parent(dwg_no: str) -> Tuple[bool, str]:
    """
    验证父级图号有效性

    Args:
        dwg_no: 父级图号

    Returns:
        Tuple[bool, str]: (是否有效, 错误信息)
    """
    try:
        parsed = parse_drawing_number(dwg_no)
    except ValueError as e:
        return False, str(e)

    # 零件不能作为父级
    if parsed['is_part']:
        return False, "零件不能作为父级图号"

    # 根图号（无横杠）可以作为父级
    if parsed['is_root']:
        return True, ""

    # 有横杠的图号，只要不是零件就可以作为父级
    # 支持格式：05S01101-00, 05S01101-ZBC 等
    return True, ""
