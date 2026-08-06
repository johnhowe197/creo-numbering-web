"""
Creo模型树自动取号器 - 测试Harness
提供自动化测试、验证和持续集成支持
"""

import json
import os
import sys
import unittest
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import (
    parse_drawing_number,
    is_component,
    is_part,
    validate_parent,
    generate_number,
    get_number_info,
    extract_components,
    extract_parts
)


@dataclass
class TestCase:
    """测试用例数据结构"""
    name: str
    description: str
    input_parent: str
    input_type: str  # 'component' or 'part'
    existing_numbers: List[str]
    expected_result: str
    expected_success: bool
    category: str = "functional"


@dataclass
class TestResult:
    """测试结果数据结构"""
    test_case: TestCase
    actual_result: str
    actual_success: bool
    passed: bool
    execution_time: float
    error_message: str = ""


class TestHarness:
    """测试Harness主类"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.path.dirname(os.path.abspath(__file__))
        self.test_cases: List[TestCase] = []
        self.results: List[TestResult] = []
        self.report_dir = os.path.join(self.project_root, "test_reports")
        os.makedirs(self.report_dir, exist_ok=True)

    def load_test_cases(self, filepath: str = None):
        """加载测试用例"""
        if filepath is None:
            filepath = os.path.join(self.project_root, "test_cases.json")

        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.test_cases = [TestCase(**tc) for tc in data.get('test_cases', [])]
        else:
            # 使用默认测试用例
            self.test_cases = self._get_default_test_cases()
            self.save_test_cases(filepath)

    def save_test_cases(self, filepath: str = None):
        """保存测试用例"""
        if filepath is None:
            filepath = os.path.join(self.project_root, "test_cases.json")

        data = {
            'test_cases': [asdict(tc) for tc in self.test_cases],
            'metadata': {
                'created': datetime.now().isoformat(),
                'version': '1.0.0'
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_default_test_cases(self) -> List[TestCase]:
        """获取默认测试用例"""
        return [
            # 组件生成测试
            TestCase(
                name="component_basic",
                description="基础组件生成 - 从01开始",
                input_parent="03S01201-100101",
                input_type="component",
                existing_numbers=[],
                expected_result="03S01201-10010101",
                expected_success=True,
                category="component"
            ),
            TestCase(
                name="component_increment",
                description="组件递增生成",
                input_parent="03S01201-100101",
                input_type="component",
                existing_numbers=["03S01201-10010101", "03S01201-10010102"],
                expected_result="03S01201-10010103",
                expected_success=True,
                category="component"
            ),
            TestCase(
                name="component_overflow",
                description="组件溢出检测",
                input_parent="03S01201-100101",
                input_type="component",
                existing_numbers=[f"03S01201-100101{i:02d}" for i in range(1, 100)],
                expected_result="Component level full (exceeded 99 sub-components)",
                expected_success=False,
                category="component"
            ),
            # 零件生成测试
            TestCase(
                name="part_basic",
                description="基础零件生成 - 从1开始",
                input_parent="03S01201-100101",
                input_type="part",
                existing_numbers=[],
                expected_result="03S01201-100101-1",
                expected_success=True,
                category="part"
            ),
            TestCase(
                name="part_increment",
                description="零件递增生成",
                input_parent="03S01201-100101",
                input_type="part",
                existing_numbers=["03S01201-100101-1", "03S01201-100101-2"],
                expected_result="03S01201-100101-3",
                expected_success=True,
                category="part"
            ),
            # 混合场景测试
            TestCase(
                name="mixed_scenario",
                description="组件和零件混合生成",
                input_parent="03S01201-100101",
                input_type="component",
                existing_numbers=[
                    "03S01201-10010101", "03S01201-10010102",
                    "03S01201-100101-1", "03S01201-100101-2"
                ],
                expected_result="03S01201-10010103",
                expected_success=True,
                category="mixed"
            ),
            # 错误处理测试
            TestCase(
                name="invalid_parent_format",
                description="无效父级格式",
                input_parent="03S01201-",
                input_type="component",
                existing_numbers=[],
                expected_result="无效的图号格式: 03S01201-",
                expected_success=False,
                category="error"
            ),
            TestCase(
                name="part_as_parent",
                description="零件作为父级",
                input_parent="03S01201-100101-1",
                input_type="component",
                existing_numbers=[],
                expected_result="Part cannot be a parent number",
                expected_success=False,
                category="error"
            ),
        ]

    def run_single_test(self, test_case: TestCase) -> TestResult:
        """运行单个测试用例"""
        start_time = datetime.now()

        try:
            success, result, _ = generate_number(
                test_case.input_parent,
                test_case.input_type,
                test_case.existing_numbers
            )

            # 如果预期失败，只检查是否失败
            if not test_case.expected_success:
                passed = not success
            else:
                passed = (success == test_case.expected_success and
                         result == test_case.expected_result)

            execution_time = (datetime.now() - start_time).total_seconds()

            return TestResult(
                test_case=test_case,
                actual_result=result,
                actual_success=success,
                passed=passed,
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_case=test_case,
                actual_result="",
                actual_success=False,
                passed=False,
                execution_time=execution_time,
                error_message=str(e)
            )

    def run_all_tests(self) -> List[TestResult]:
        """运行所有测试用例"""
        self.results = []
        for test_case in self.test_cases:
            result = self.run_single_test(test_case)
            self.results.append(result)
            status = "PASS" if result.passed else "FAIL"
            print(f"[{status}] {test_case.name}: {test_case.description}")

        return self.results

    def run_category_tests(self, category: str) -> List[TestResult]:
        """运行指定类别的测试"""
        category_results = []
        for test_case in self.test_cases:
            if test_case.category == category:
                result = self.run_single_test(test_case)
                category_results.append(result)
                status = "PASS" if result.passed else "FAIL"
                print(f"[{status}] {test_case.name}: {test_case.description}")

        return category_results

    def generate_report(self) -> str:
        """生成测试报告"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0

        report = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{pass_rate:.1f}%",
                "timestamp": datetime.now().isoformat()
            },
            "details": [
                {
                    "name": r.test_case.name,
                    "description": r.test_case.description,
                    "category": r.test_case.category,
                    "passed": r.passed,
                    "expected": r.test_case.expected_result,
                    "actual": r.actual_result,
                    "execution_time": f"{r.execution_time:.4f}s",
                    "error": r.error_message if r.error_message else None
                }
                for r in self.results
            ]
        }

        # 保存JSON报告
        report_file = os.path.join(
            self.report_dir,
            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 生成文本报告
        text_report = self._format_text_report(report)
        text_file = os.path.join(
            self.report_dir,
            f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(text_report)

        return text_report

    def _format_text_report(self, report: dict) -> str:
        """格式化文本报告"""
        lines = [
            "=" * 60,
            "Creo模型树自动取号器 - 测试报告",
            "=" * 60,
            "",
            f"生成时间: {report['summary']['timestamp']}",
            f"测试总数: {report['summary']['total']}",
            f"通过: {report['summary']['passed']}",
            f"失败: {report['summary']['failed']}",
            f"通过率: {report['summary']['pass_rate']}",
            "",
            "-" * 60,
            "详细结果:",
            "-" * 60,
        ]

        for detail in report['details']:
            status = "PASS" if detail['passed'] else "FAIL"
            lines.append(f"\n[{status}] {detail['name']}")
            lines.append(f"  描述: {detail['description']}")
            lines.append(f"  类别: {detail['category']}")
            lines.append(f"  期望: {detail['expected'] or '(无)'}")
            lines.append(f"  实际: {detail['actual'] or '(无)'}")
            lines.append(f"  耗时: {detail['execution_time']}")
            if detail['error']:
                lines.append(f"  错误: {detail['error']}")

        lines.extend([
            "",
            "=" * 60,
            "测试完成",
            "=" * 60
        ])

        return "\n".join(lines)


class RegressionSuite:
    """回归测试套件"""

    def __init__(self, harness: TestHarness):
        self.harness = harness

    def test_parser_edge_cases(self) -> List[TestResult]:
        """测试解析器边界情况"""
        edge_cases = [
            TestCase(
                name="parser_min_length",
                description="最短图号解析",
                input_parent="A-1",
                input_type="component",
                existing_numbers=[],
                expected_result="",
                expected_success=False,
                category="parser"
            ),
            TestCase(
                name="parser_special_chars",
                description="特殊字符图号",
                input_parent="03S01201-10_01",
                input_type="component",
                existing_numbers=[],
                expected_result="",
                expected_success=False,
                category="parser"
            ),
        ]

        results = []
        for tc in edge_cases:
            result = self.harness.run_single_test(tc)
            results.append(result)
        return results

    def test_concurrent_generation(self) -> bool:
        """测试并发生成（模拟）"""
        parent = "03S01201-100101"
        existing = []

        # 模拟多次连续生成
        for i in range(5):
            success, result, _ = generate_number(parent, "component", existing)
            if success:
                existing.append(result)
            else:
                return False

        return len(existing) == 5

    def test_data_persistence(self) -> bool:
        """测试数据持久化"""
        test_file = os.path.join(self.harness.project_root, "test_persistence.json")

        try:
            # 写入测试数据
            data = {"test": True, "numbers": ["03S01201-10010101"]}
            with open(test_file, 'w') as f:
                json.dump(data, f)

            # 读取验证
            with open(test_file, 'r') as f:
                loaded = json.load(f)

            return loaded.get("test") == True and len(loaded.get("numbers", [])) == 1

        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self, harness: TestHarness):
        self.harness = harness

    def benchmark_generation(self, iterations: int = 1000) -> Dict[str, float]:
        """基准测试生成性能"""
        import time

        parent = "03S01201-100101"
        existing = ["03S01201-10010101"]

        # 组件生成基准
        start = time.time()
        for _ in range(iterations):
            generate_number(parent, "component", existing)
        component_time = (time.time() - start) / iterations * 1000

        # 零件生成基准
        existing_parts = ["03S01201-100101-1"]
        start = time.time()
        for _ in range(iterations):
            generate_number(parent, "part", existing_parts)
        part_time = (time.time() - start) / iterations * 1000

        return {
            "iterations": iterations,
            "component_avg_ms": f"{component_time:.4f}",
            "part_avg_ms": f"{part_time:.4f}",
            "total_ms": f"{(component_time + part_time) * iterations:.2f}"
        }


def run_harness():
    """运行测试Harness"""
    print("=" * 60)
    print("Creo模型树自动取号器 - 测试Harness")
    print("=" * 60)

    # 初始化
    harness = TestHarness()
    harness.load_test_cases()

    # 运行基础测试
    print("\n[1/4] 运行基础测试用例...")
    harness.run_all_tests()

    # 运行回归测试
    print("\n[2/4] 运行回归测试...")
    regression = RegressionSuite(harness)
    regression.test_parser_edge_cases()
    concurrent_ok = regression.test_concurrent_generation()
    persistence_ok = regression.test_data_persistence()

    # 运行性能基准
    print("\n[3/4] 运行性能基准测试...")
    benchmark = PerformanceBenchmark(harness)
    perf_results = benchmark.benchmark_generation()

    # 生成报告
    print("\n[4/4] 生成测试报告...")
    report = harness.generate_report()

    # 输出摘要
    print("\n" + "=" * 60)
    print("测试摘要")
    print("=" * 60)
    print(f"并发生成测试: {'PASS' if concurrent_ok else 'FAIL'}")
    print(f"数据持久化测试: {'PASS' if persistence_ok else 'FAIL'}")
    print(f"\n性能基准:")
    print(f"  组件生成平均耗时: {perf_results['component_avg_ms']}ms")
    print(f"  零件生成平均耗时: {perf_results['part_avg_ms']}ms")
    print("\n" + report)


if __name__ == "__main__":
    run_harness()
