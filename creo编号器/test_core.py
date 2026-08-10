"""
核心功能测试脚本
"""

from core import (
    parse_drawing_number,
    is_component,
    is_part,
    is_alpha_component,
    is_host_level,
    validate_parent,
    generate_number,
    get_number_info,
    get_next_top_component_number
)


def test_parser():
    """测试图号解析器"""
    print("=== Testing Parser ===")

    test_cases = [
        ("03S01201-10", True, False),      # 组件
        ("03S01201-100101", True, False),   # 组件
        ("03S01201-100101-1", False, True), # 零件
        ("03S01201-10010101", True, False), # 组件
    ]

    for dwg_no, expect_component, expect_part in test_cases:
        parsed = parse_drawing_number(dwg_no)
        assert is_component(dwg_no) == expect_component, f"Component check failed for {dwg_no}"
        assert is_part(dwg_no) == expect_part, f"Part check failed for {dwg_no}"
        print(f"OK {dwg_no}")

    print()


def test_generator():
    """测试图号生成器"""
    print("=== Testing Generator ===")

    # Test 1: Generate component
    parent = "03S01201-100101"
    existing = ["03S01201-10010101", "03S01201-10010102"]
    success, result, _ = generate_number(parent, "component", existing)
    assert success, "Component generation failed"
    assert result == "03S01201-10010103", f"Expected 03S01201-10010103, got {result}"
    print(f"OK Component generation: {result}")

    # Test 2: Generate part
    existing_parts = ["03S01201-100101-1", "03S01201-100101-2"]
    success, result, _ = generate_number(parent, "part", existing_parts)
    assert success, "Part generation failed"
    assert result == "03S01201-100101-3", f"Expected 03S01201-100101-3, got {result}"
    print(f"OK Part generation: {result}")

    # Test 3: Empty parent (should start from 01)
    success, result, _ = generate_number(parent, "component", [])
    assert success, "Empty parent generation failed"
    assert result == "03S01201-10010101", f"Expected 03S01201-10010101, got {result}"
    print(f"OK Empty parent generation: {result}")

    # Test 4: Overflow check
    existing_full = [f"03S01201-100101{i:02d}" for i in range(1, 100)]
    success, result, _ = generate_number(parent, "component", existing_full)
    assert not success, "Should fail on overflow"
    print(f"OK Overflow check: {result}")

    print()


def test_validation():
    """测试父级验证"""
    print("=== Testing Validation ===")

    # Valid parent
    valid, _ = validate_parent("03S01201-100101")
    assert valid, "Valid parent should pass"
    print("OK Valid parent: 03S01201-100101")

    # Invalid: part as parent
    valid, error = validate_parent("03S01201-100101-1")
    assert not valid, "Part as parent should fail"
    print(f"OK Part as parent rejected: {error}")

    # Invalid: invalid format
    valid, error = validate_parent("03S01201-")
    assert not valid, "Invalid format should fail"
    print(f"OK Invalid format rejected: {error}")

    print()


def test_number_info():
    """测试图号信息获取"""
    print("=== Testing Number Info ===")

    all_numbers = [
        "03S01201-100101",
        "03S01201-10010101",
        "03S01201-10010102",
        "03S01201-100101-1",
        "03S01201-100101-2",
    ]

    info = get_number_info("03S01201-100101", all_numbers)
    assert info['components_count'] == 2, f"Expected 2 components, got {info['components_count']}"
    assert info['parts_count'] == 2, f"Expected 2 parts, got {info['parts_count']}"
    print(f"OK Components: {info['components_count']}")
    print(f"OK Parts: {info['parts_count']}")

    print()


def test_alpha_component():
    """测试字母图号（如 ZBC、KTC）"""
    print("=== Testing Alpha Component ===")

    # 字母组件识别
    assert is_component("05S01101-ZBC"), "字母组件应识别为组件"
    assert not is_part("05S01101-ZBC"), "字母组件不是零件"
    assert is_alpha_component("05S01101-ZBC"), "ZBC 应为字母组件"
    assert not is_alpha_component("05S01101-10"), "纯数字组件不是字母组件"
    assert not is_alpha_component("05S01101-100101-1"), "零件不是字母组件"
    print("OK 字母组件识别: 05S01101-ZBC")

    # 字母组件可作为父级
    valid, error = validate_parent("05S01101-ZBC")
    assert valid, f"字母组件应可作为父级: {error}"
    print("OK 字母组件父级验证")

    # 字母组件下新建组件：根前缀 + 两位数字全局编号
    success, result, _ = generate_number(
        "05S01101-ZBC", "component",
        ["05S01101-00", "05S01101-01", "05S01101-02"]
    )
    assert success, "字母组件下组件生成失败"
    assert result == "05S01101-03", f"Expected 05S01101-03, got {result}"
    print(f"OK 字母组件下全局编号: {result}")

    # 全局编号不受深层追加图号（如 -1001）影响
    success, result, _ = generate_number(
        "05S01101-ZBC", "component",
        ["05S01101-00", "05S01101-10", "05S01101-1001", "05S01101-100101"]
    )
    assert result == "05S01101-11", f"Expected 05S01101-11, got {result}"
    print(f"OK 全局编号忽略深层图号: {result}")

    # 全局编号为空时从 01 开始（字母组件下的数字组件从 01 起）
    success, result, _ = get_next_top_component_number("LS001", [])
    assert result == "LS001-01", f"Expected LS001-01, got {result}"
    print(f"OK 全局编号起始: {result}")

    # 字母组件下新建零件：分叉法
    success, result, _ = generate_number("05S01101-ZBC", "part", [])
    assert result == "05S01101-ZBC-1", f"Expected 05S01101-ZBC-1, got {result}"
    print(f"OK 字母组件下零件编号: {result}")

    # 字母组件下新建零件：传入宿主（字母组件的父级）时使用宿主共享序列
    success, result, _ = generate_number(
        "05S01101-ZBC", "part", ["05S01101-00-1"], host_number="05S01101-00"
    )
    assert result == "05S01101-00-2", f"Expected 05S01101-00-2, got {result}"
    print(f"OK 字母组件零件宿主序列: {result}")

    # 数字组件（追加法）行为不变
    success, result, _ = generate_number("05S01101-10", "component", ["05S01101-1001"])
    assert result == "05S01101-1002", f"Expected 05S01101-1002, got {result}"
    print(f"OK 数字组件追加法: {result}")

    # 主机层判定：根的直接子级两位数字（如 -00）是主机层
    assert is_host_level("05S01101-00", "05S01101", "05S01101"), "-00 应为主机层"
    assert not is_host_level("05S01101-10", "05S01101-ZBC", "05S01101"), "-10 不是主机层"
    assert not is_host_level("05S01101-ZBC", "05S01101-00", "05S01101"), "字母组件不是主机层"
    assert not is_host_level("05S01101-00", None, "05S01101"), "无父级引用不是主机层"
    print("OK 主机层判定")

    print()


if __name__ == "__main__":
    test_parser()
    test_generator()
    test_validation()
    test_number_info()
    test_alpha_component()
    print("All tests passed!")
