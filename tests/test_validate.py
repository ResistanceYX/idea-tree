import tempfile
import unittest
from pathlib import Path

from scripts.validate import validate_repository


def node_text(node_id: str, title: str = "测试节点", number: str = "0001") -> str:
    return f"""编号: "{number}"
id: {node_id}
标题: {title}
档案类型: 预审
一句话: 用于验证检查器的最小合法节点
复活状态: 死透
创新类型: [渐进式]
领域: 测试
子领域: 测试
死法:
  - 类型: 伪需求
    证据: 创始人自我分析
    分析: 这是用于测试的明确内部推演，不冒充公开证据
    置信度: 中
可拆零件:
  - 测试零件
死因保质期: 2028-01-01
起草AI: 测试AI
审核人: 测试审核人
审核日期: 2026-01-01
"""


class ValidatorTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "nodes").mkdir()
        (root / "evidence").mkdir()
        (root / "README.md").write_text("# 测试仓库\n", encoding="utf-8")
        return root

    def test_valid_minimal_node_passes(self) -> None:
        root = self.make_repo()
        (root / "nodes" / "0001-test-node.yaml").write_text(node_text("test-node"), encoding="utf-8")
        (root / "README.md").write_text("[测试节点](nodes/0001-test-node.yaml)\n", encoding="utf-8")

        result = validate_repository(root)

        self.assertEqual([], result["errors"])
        self.assertEqual(1, result["nodes"])

    def test_deliberately_broken_node_is_rejected(self) -> None:
        root = self.make_repo()
        broken = """编号: "0001"
id: broken-node
档案类型: 未定义
一句话: 故意缺少标题并包含多项错误的测试节点
复活状态: 复活候选
创新类型: [渐进式]
领域: 测试
子领域: 测试
死法:
  - 类型: 伪需求
    证据: 公开案例
    推理: 故意只提供一个链接却标为高置信度
    证据链接:
      - https://example.com/evidence
    置信度: 高
可拆零件:
  - 测试零件
死因保质期: 2028-01-01
起草AI: 测试AI
审核人: 测试审核人
审核日期: 2026-01-01
"""
        (root / "nodes" / "0001-wrong-name.yaml").write_text(broken, encoding="utf-8")

        result = validate_repository(root)
        messages = "\n".join(result["errors"])

        self.assertIn("标题", messages)
        self.assertIn("档案类型", messages)
        self.assertIn("商业及社会价值评估", messages)
        self.assertIn("id 与文件名不一致", messages)
        self.assertIn("高置信度至少需要两个不同证据链接", messages)

    def test_optional_conclusion_boundary_must_be_a_nonempty_string(self) -> None:
        root = self.make_repo()
        file = root / "nodes" / "0001-test-node.yaml"
        file.write_text(node_text("test-node") + "结论边界: 仅限定当前完整路线。\n", encoding="utf-8")
        self.assertEqual([], validate_repository(root)["errors"])

        for value in ('""', "  ", "[缩围路线]", "123"):
            with self.subTest(value=value):
                file.write_text(node_text("test-node") + f"结论边界: {value}\n", encoding="utf-8")
                result = validate_repository(root)
                self.assertIn("结论边界如填写则必须是非空字符串", "\n".join(result["errors"]))

    def test_derived_id_requires_existing_parent(self) -> None:
        root = self.make_repo()
        parent = root / "nodes" / "0001-parent.yaml"
        parent.write_text(node_text("parent", "母题"), encoding="utf-8")
        (root / "nodes" / "0002-parent_child.yaml").write_text(
            node_text("parent_child", "直接派生子题", "0002"), encoding="utf-8"
        )

        valid = validate_repository(root)
        self.assertEqual([], valid["errors"])

        parent.unlink()
        invalid = validate_repository(root)
        self.assertIn("缺少对应母题节点", "\n".join(invalid["errors"]))

    def test_filename_requires_exactly_four_numeric_prefix_characters(self) -> None:
        for filename in ("test-node.yaml", "ab01-test-node.yaml", "123-test-node.yaml", "00012-test-node.yaml"):
            with self.subTest(filename=filename):
                root = self.make_repo()
                (root / "nodes" / filename).write_text(node_text("test-node"), encoding="utf-8")

                result = validate_repository(root)

                self.assertIn("文件名必须为 `<四位数字>-<id>.yaml`", "\n".join(result["errors"]))

    def test_number_is_required_quoted_and_consistent_with_filename(self) -> None:
        root = self.make_repo()
        file = root / "nodes" / "0001-test-node.yaml"
        file.write_text(node_text("test-node").replace('编号: "0001"\n', ""), encoding="utf-8")
        missing = validate_repository(root)
        self.assertIn("缺少必选字段 `编号`", "\n".join(missing["errors"]))

        file.write_text(node_text("test-node").replace('编号: "0001"', "编号: 0001"), encoding="utf-8")
        unquoted = validate_repository(root)
        self.assertIn("编号必须是带引号的四位数字字符串", "\n".join(unquoted["errors"]))

        file.write_text(node_text("test-node", number="0002"), encoding="utf-8")
        mismatched = validate_repository(root)
        self.assertIn("编号与文件名前四位不一致", "\n".join(mismatched["errors"]))

    def test_duplicate_and_reserved_numbers_are_rejected(self) -> None:
        root = self.make_repo()
        (root / "nodes" / "0001-alpha.yaml").write_text(node_text("alpha", "甲"), encoding="utf-8")
        (root / "nodes" / "0001-beta.yaml").write_text(node_text("beta", "乙"), encoding="utf-8")
        duplicate = validate_repository(root)
        self.assertIn("编号 `0001` 重复", "\n".join(duplicate["errors"]))

        reserved_root = self.make_repo()
        (reserved_root / "nodes" / "0000-test-node.yaml").write_text(
            node_text("test-node", number="0000"), encoding="utf-8"
        )
        reserved = validate_repository(reserved_root)
        self.assertIn("0000 永久保留", "\n".join(reserved["errors"]))

    def test_related_nodes_use_numbered_file_stems_and_require_return_links(self) -> None:
        root = self.make_repo()
        alpha = root / "nodes" / "0001-alpha.yaml"
        beta = root / "nodes" / "0002-beta.yaml"
        alpha.write_text(
            node_text("alpha", "甲") + "相关节点:\n  - 节点: 0002-beta\n    关系: 测试关系\n",
            encoding="utf-8",
        )
        beta.write_text(
            node_text("beta", "乙", "0002") + "相关节点:\n  - 节点: 0001-alpha\n    关系: 测试关系\n",
            encoding="utf-8",
        )
        self.assertEqual([], validate_repository(root)["errors"])

        beta.write_text(node_text("beta", "乙", "0002"), encoding="utf-8")
        missing_return = validate_repository(root)
        self.assertIn("缺少回程声明", "\n".join(missing_return["errors"]))

        alpha.write_text(
            node_text("alpha", "甲") + "相关节点:\n  - 节点: beta\n    关系: 测试关系\n",
            encoding="utf-8",
        )
        beta.write_text(
            node_text("beta", "乙", "0002") + "相关节点:\n  - 节点: 0001-alpha\n    关系: 测试关系\n",
            encoding="utf-8",
        )
        old_reference = validate_repository(root)
        self.assertIn("未使用带编号文件名主体", "\n".join(old_reference["errors"]))


if __name__ == "__main__":
    unittest.main()
