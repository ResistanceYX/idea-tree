import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from scripts.generate_review import generate_review, main, render_review, review_is_current


def node_text(
    node_id: str, title: str, expiry: str, reviewed: str = "2026-01-01", number: str = "0001"
) -> str:
    return f"""编号: "{number}"
id: {node_id}
标题: {title}
档案类型: 预审
一句话: 用于验证复核清单的测试节点
复活状态: 死透
创新类型: [渐进式]
领域: 测试领域
子领域: 测试子领域
死法:
  - 类型: 伪需求
    证据: 创始人自我分析
    分析: 仅用于测试复核清单，不代表真实创业结论
    置信度: 中
可拆零件:
  - 测试零件
死因保质期: {expiry}
起草AI: 测试AI
审核人: 测试审核人
审核日期: {reviewed}
"""


class ReviewGeneratorTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "nodes").mkdir()
        (root / "review_records.yaml").write_text("records: {}\n", encoding="utf-8")
        return root

    def test_new_node_is_pending_and_rows_follow_expiry_order(self) -> None:
        root = self.make_repo()
        (root / "nodes" / "0002-later.yaml").write_text(
            node_text("later", "较晚节点", "2028-01-01", number="0002"), encoding="utf-8"
        )
        (root / "nodes" / "0001-earlier.yaml").write_text(
            node_text("earlier", "较早节点", "2027-01-01"), encoding="utf-8"
        )
        (root / "review_records.yaml").write_text(
            """records:
  later:
    复核状态: 已复核
    复核结论: 维持原判
    复核后日期: 2026-02-01
    备注: 已完成测试复核
""",
            encoding="utf-8",
        )

        content = generate_review(root)

        self.assertIn("[较早节点](nodes/0001-earlier.yaml)", content)
        self.assertIn("[较晚节点](nodes/0002-later.yaml)", content)
        self.assertIn("| 编号 | 节点 | 审核日期 |", content)
        self.assertLess(content.index("较早节点"), content.index("较晚节点"))
        self.assertIn("| 待复核 | — | — | — |", content)
        self.assertIn("| 已复核 | 维持原判 | 2026-02-01 | 已完成测试复核 |", content)
        self.assertIn("待复核1个，已复核1个，暂缓0个", content)
        self.assertTrue(review_is_current(root))

    def test_check_detects_new_node_without_overwriting_human_record(self) -> None:
        root = self.make_repo()
        (root / "nodes" / "0001-stable.yaml").write_text(
            node_text("stable", "稳定节点", "2028-01-01"), encoding="utf-8"
        )
        (root / "review_records.yaml").write_text(
            """records:
  stable:
    复核状态: 暂缓
    备注: 等待公开来源更新后复核
""",
            encoding="utf-8",
        )
        first = generate_review(root)
        second = generate_review(root)
        self.assertEqual(first, second)
        self.assertIn("等待公开来源更新后复核", second)

        (root / "nodes" / "0002-new-node.yaml").write_text(
            node_text("new-node", "新增节点", "2027-06-01", number="0002"), encoding="utf-8"
        )
        self.assertFalse(review_is_current(root))
        output = io.StringIO()
        with patch.object(sys, "argv", ["generate_review.py", "--root", str(root), "--check"]):
            with contextlib.redirect_stdout(output):
                exit_code = main()
        self.assertEqual(1, exit_code)
        self.assertIn("不同步", output.getvalue())

        updated = generate_review(root)
        self.assertIn("新增节点", updated)
        self.assertIn("等待公开来源更新后复核", updated)

    def test_invalid_or_orphan_human_records_are_rejected(self) -> None:
        root = self.make_repo()
        (root / "nodes" / "0001-test-node.yaml").write_text(
            node_text("test-node", "测试节点", "2028-01-01"), encoding="utf-8"
        )
        (root / "review_records.yaml").write_text(
            """records:
  removed-node:
    复核状态: 暂缓
    备注: 等待下次检查时确认节点去向
""",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "不存在的节点"):
            render_review(root)

        (root / "review_records.yaml").write_text(
            """records:
  test-node:
    复核状态: 已复核
""",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "复核结论和复核后日期"):
            render_review(root)

        (root / "review_records.yaml").write_text(
            """records:
  test-node:
    复核状态: 暂缓
""",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "原因和下次检查条件"):
            render_review(root)

    def test_optional_history_is_validated_and_latest_entry_matches_current_state(self) -> None:
        root = self.make_repo()
        (root / "nodes" / "0001-test-node.yaml").write_text(
            node_text("test-node", "测试节点", "2028-01-01"), encoding="utf-8"
        )
        record = {
            "复核状态": "已复核",
            "复核结论": "维持原判",
            "复核后日期": "2026-02-01",
            "履历": [
                {
                    "日期": "2026-01-01",
                    "档案类型": "预审",
                    "复活状态": "死透",
                    "说明": "首次真实复核。",
                },
                {
                    "日期": "2026-02-01",
                    "档案类型": "预审",
                    "复活状态": "死透",
                    "说明": "第二次真实复核。",
                },
            ],
        }
        (root / "review_records.yaml").write_text(
            yaml.safe_dump({"records": {"test-node": record}}, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        content = render_review(root)
        self.assertIn("| 已复核 | 维持原判 | 2026-02-01 | — |", content)

        invalid_cases = [
            ("履历必须是数组", {"履历": {}}),
            ("履历第1条必须是映射", {"履历": ["不是映射"]}),
            ("存在未定义字段：额外", {"履历": [{**record["履历"][-1], "额外": "不允许"}]}),
            ("缺少字段", {"履历": [{key: value for key, value in record["履历"][-1].items() if key != "说明"}]}),
            ("日期必须是有效的 YYYY-MM-DD", {"履历": [{**record["履历"][-1], "日期": "2026-02-30"}]}),
            ("档案类型必须是预审或验尸", {"履历": [{**record["履历"][-1], "档案类型": "未知"}]}),
            ("复活状态不合法", {"履历": [{**record["履历"][-1], "复活状态": "未知"}]}),
            ("说明必须是非空字符串", {"履历": [{**record["履历"][-1], "说明": "  "}]}),
            ("履历不得重复", {"履历": [record["履历"][-1], record["履历"][-1]]}),
            ("最新履历日期必须与复核后日期一致", {"履历": [record["履历"][0]]}),
            ("最新履历中的档案类型与复活状态必须与节点当前状态一致", {"履历": [{**record["履历"][-1], "复活状态": "已复活"}]}),
        ]
        for message, override in invalid_cases:
            with self.subTest(message=message):
                invalid = {**record, **override}
                (root / "review_records.yaml").write_text(
                    yaml.safe_dump({"records": {"test-node": invalid}}, allow_unicode=True, sort_keys=False),
                    encoding="utf-8",
                )
                with self.assertRaisesRegex(ValueError, message):
                    render_review(root)

    def test_conflicting_conclusions_are_rejected(self) -> None:
        root = self.make_repo()
        (root / "nodes" / "0001-test-node.yaml").write_text(
            node_text("test-node", "测试节点", "2028-01-01"), encoding="utf-8"
        )
        (root / "review_records.yaml").write_text(
            """records:
  test-node:
    复核状态: 已复核
    复核结论: 维持原判、调整置信度
    复核后日期: 2026-02-01
""",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "不得与其他调整结论并列"):
            render_review(root)


if __name__ == "__main__":
    unittest.main()
