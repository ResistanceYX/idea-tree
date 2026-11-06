import tempfile
import unittest
from pathlib import Path

from scripts.validate import validate_repository


def node_text(node_id: str, title: str = "测试节点") -> str:
    return f"""id: {node_id}
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
        (root / "nodes" / "test-node.yaml").write_text(node_text("test-node"), encoding="utf-8")
        (root / "README.md").write_text("[测试节点](nodes/test-node.yaml)\n", encoding="utf-8")

        result = validate_repository(root)

        self.assertEqual([], result["errors"])
        self.assertEqual(1, result["nodes"])

    def test_deliberately_broken_node_is_rejected(self) -> None:
        root = self.make_repo()
        broken = """id: broken-node
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
        (root / "nodes" / "wrong-name.yaml").write_text(broken, encoding="utf-8")

        result = validate_repository(root)
        messages = "\n".join(result["errors"])

        self.assertIn("标题", messages)
        self.assertIn("档案类型", messages)
        self.assertIn("商业及社会价值评估", messages)
        self.assertIn("id 与文件名不一致", messages)
        self.assertIn("高置信度至少需要两个不同证据链接", messages)

    def test_derived_id_requires_existing_parent(self) -> None:
        root = self.make_repo()
        (root / "nodes" / "parent.yaml").write_text(node_text("parent", "母题"), encoding="utf-8")
        (root / "nodes" / "parent_child.yaml").write_text(
            node_text("parent_child", "直接派生子题"), encoding="utf-8"
        )

        valid = validate_repository(root)
        self.assertEqual([], valid["errors"])

        (root / "nodes" / "parent.yaml").unlink()
        invalid = validate_repository(root)
        self.assertIn("缺少对应母题节点", "\n".join(invalid["errors"]))


if __name__ == "__main__":
    unittest.main()
