import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.generate_index import expected_index, generate_index, index_is_current, main


def node_text(
    node_id: str, title: str, death_type: str = "伪需求", status: str = "死透", number: str = "0001"
) -> str:
    return f"""编号: "{number}"
id: {node_id}
标题: {title}
档案类型: 预审
一句话: 用于验证自动索引的测试节点
复活状态: {status}
创新类型: [渐进式]
领域: 测试领域
子领域: 测试子领域
死法:
  - 类型: {death_type}
    证据: 创始人自我分析
    分析: 仅用于测试自动索引，不代表真实创业结论
    置信度: 中
可拆零件:
  - 测试零件
死因保质期: 2028-01-01
起草AI: 测试AI
审核人: 测试审核人
审核日期: 2026-01-01
"""


class IndexGeneratorTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "nodes").mkdir()
        return root

    def test_index_contains_node_fields_and_statistics(self) -> None:
        root = self.make_repo()
        (root / "nodes" / "0002-alpha.yaml").write_text(
            node_text("alpha", "甲节点", "政策风险", "复活候选", "0002"), encoding="utf-8"
        )
        (root / "nodes" / "0001-beta.yaml").write_text(
            node_text("beta", "乙节点", "伪需求", number="0001"), encoding="utf-8"
        )

        content = generate_index(root)

        self.assertIn("[甲节点](nodes/0002-alpha.yaml)", content)
        self.assertIn("[乙节点](nodes/0001-beta.yaml)", content)
        self.assertLess(content.index("乙节点"), content.index("甲节点"))
        self.assertIn("| 编号 | 标题 | id |", content)
        self.assertIn("`alpha`", content)
        self.assertIn("预审", content)
        self.assertIn("复活候选", content)
        self.assertIn("测试领域", content)
        self.assertIn("2028-01-01", content)
        self.assertIn("- 节点：2 个", content)
        self.assertIn("- 死法：2 条", content)
        self.assertIn("| 政策风险 | 1 | 1 |", content)
        self.assertIn("| 伪需求 | 1 | 1 |", content)
        self.assertIn("| 死透 | 1 |", content)
        self.assertIn("| 复活候选 | 1 |", content)
        self.assertIn("| 预审 | 2 |", content)

    def test_repeated_generation_is_deterministic(self) -> None:
        root = self.make_repo()
        (root / "nodes" / "0001-stable.yaml").write_text(
            node_text("stable", "稳定节点"), encoding="utf-8"
        )

        first = generate_index(root)
        second = generate_index(root)

        self.assertEqual(first, second)
        self.assertEqual(first, (root / "INDEX.md").read_text(encoding="utf-8"))
        self.assertNotIn("生成时间", first)
        self.assertTrue(index_is_current(root))

    def test_check_detects_stale_index_after_node_change(self) -> None:
        root = self.make_repo()
        node = root / "nodes" / "0001-changing.yaml"
        node.write_text(node_text("changing", "修改前"), encoding="utf-8")
        generate_index(root)
        self.assertTrue(index_is_current(root))

        node.write_text(node_text("changing", "修改后", "信任成本"), encoding="utf-8")

        self.assertFalse(index_is_current(root))
        self.assertIn("修改后", expected_index(root))
        self.assertIn("信任成本", expected_index(root))
        self.assertIn("修改前", (root / "INDEX.md").read_text(encoding="utf-8"))

        output = io.StringIO()
        with patch.object(sys, "argv", ["generate_index.py", "--root", str(root), "--check"]):
            with contextlib.redirect_stdout(output):
                exit_code = main()
        self.assertEqual(1, exit_code)
        self.assertIn("INDEX.md 与当前节点不同步", output.getvalue())


if __name__ == "__main__":
    unittest.main()
