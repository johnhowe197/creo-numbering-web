# 测试Harness使用指南

## 概述

测试Harness为Creo模型树自动取号器提供完整的自动化测试框架，包括：

- 功能测试用例管理
- 回归测试套件
- 性能基准测试
- 自动化报告生成

## 快速开始

### 运行所有测试

```bash
python harness.py
```

### 运行指定类别测试

```python
from harness import TestHarness

harness = TestHarness()
harness.load_test_cases()

# 运行组件相关测试
harness.run_category_tests("component")

# 运行零件相关测试
harness.run_category_tests("part")
```

## 测试用例

测试用例存储在 `test_cases.json` 文件中，格式如下：

```json
{
  "test_cases": [
    {
      "name": "component_basic",
      "description": "基础组件生成 - 从01开始",
      "input_parent": "03S01201-100101",
      "input_type": "component",
      "existing_numbers": [],
      "expected_result": "03S01201-10010101",
      "expected_success": true,
      "category": "component"
    }
  ]
}
```

### 测试类别

| 类别 | 说明 |
|------|------|
| `component` | 组件生成测试 |
| `part` | 零件生成测试 |
| `mixed` | 混合场景测试 |
| `error` | 错误处理测试 |
| `parser` | 解析器边界测试 |

## 回归测试

RegressionSuite提供额外的回归测试：

```python
from harness import RegressionSuite, TestHarness

harness = TestHarness()
regression = RegressionSuite(harness)

# 测试解析器边界情况
regression.test_parser_edge_cases()

# 测试并发生成
regression.test_concurrent_generation()

# 测试数据持久化
regression.test_data_persistence()
```

## 性能基准

PerformanceBenchmark用于测量生成性能：

```python
from harness import PerformanceBenchmark, TestHarness

harness = TestHarness()
benchmark = PerformanceBenchmark(harness)

# 运行1000次迭代基准测试
results = benchmark.benchmark_generation(iterations=1000)
print(results)
# 输出: {'iterations': 1000, 'component_avg_ms': '0.0040', ...}
```

## 测试报告

测试完成后自动生成两种格式的报告：

### JSON报告
包含详细的测试结果数据，便于程序解析。

### 文本报告
人类可读的格式化报告，包含：
- 测试摘要（总数、通过、失败、通过率）
- 详细结果（每个测试用例的期望值、实际值、耗时）

报告保存在 `test_reports/` 目录。

## 自定义测试用例

### 添加新测试用例

1. 直接编辑 `test_cases.json`
2. 或在代码中添加：

```python
from harness import TestHarness, TestCase

harness = TestHarness()
harness.load_test_cases()

# 添加新测试用例
new_test = TestCase(
    name="my_custom_test",
    description="自定义测试描述",
    input_parent="03S01201-100101",
    input_type="component",
    existing_numbers=[],
    expected_result="03S01201-10010101",
    expected_success=True,
    category="custom"
)

harness.test_cases.append(new_test)
harness.run_single_test(new_test)
```

## 集成到CI/CD

### GitHub Actions示例

```yaml
name: Run Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python harness.py
      - name: Upload test reports
        uses: actions/upload-artifact@v2
        with:
          name: test-reports
          path: test_reports/
```

### 命令行运行

```bash
# 运行所有测试并检查退出码
python harness.py
if [ $? -eq 0 ]; then
  echo "All tests passed"
else
  echo "Some tests failed"
  exit 1
fi
```

## 测试覆盖率

当前测试覆盖：

- ✅ 组件生成（追加法）
- ✅ 零件生成（分叉法）
- ✅ 混合场景
- ✅ 错误处理
- ✅ 溢出检测
- ✅ 并发生成
- ✅ 数据持久化
- ✅ 性能基准

## 故障排除

### 测试失败

查看 `test_reports/` 目录中的详细报告，定位失败原因。

### 性能问题

如果性能基准测试显示异常，检查：
- 系统负载
- Python版本
- 依赖库版本

### 报告生成失败

确保 `test_reports/` 目录存在且有写入权限。
