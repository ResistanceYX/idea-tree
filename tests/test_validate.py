import tempfile
import unittest
from pathlib import Path

import yaml

from scripts.validate import evidence_source_key, validate_repository


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


def public_death(links: list[str], confidence: str = "中") -> dict:
    return {
        "类型": "伪需求",
        "证据": "公开案例",
        "推理": "用于测试来源归并与复用检查的公开证据条目",
        "证据链接": links,
        "置信度": confidence,
    }


def internal_death() -> dict:
    return {
        "类型": "执行人限制",
        "证据": "内部推演",
        "推理": "用于组成足够死法数量的明确内部推演",
        "置信度": "中",
    }


class ValidatorTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "nodes").mkdir()
        (root / "evidence").mkdir()
        (root / "README.md").write_text("# 测试仓库\n", encoding="utf-8")
        return root

    def write_node(
        self,
        root: Path,
        stem: str,
        deaths: list[dict],
        relations: list[dict] | None = None,
    ) -> Path:
        number, node_id = stem.split("-", 1)
        data = yaml.safe_load(node_text(node_id, number=number))
        data["死法"] = deaths
        if relations is not None:
            data["相关节点"] = relations
        file = root / "nodes" / f"{stem}.yaml"
        file.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return file

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
        self.assertIn("高置信度至少需要两个不同证据来源", messages)

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
        parent.write_text(
            node_text("parent", "母题")
            + "相关节点:\n  - 节点: 0002-parent_child\n    关系: 直接派生\n",
            encoding="utf-8",
        )
        child = root / "nodes" / "0002-parent_child.yaml"
        child_text = (
            node_text("parent_child", "直接派生子题", "0002")
            + "相关节点:\n  - 节点: 0001-parent\n    关系: 直接母题\n"
        )
        child.write_text(child_text, encoding="utf-8")

        valid = validate_repository(root)
        self.assertEqual([], valid["errors"])

        child.write_text(node_text("parent_child", "直接派生子题", "0002"), encoding="utf-8")
        missing_declaration = validate_repository(root)
        self.assertIn("必须且只能声明一个直接母题", "\n".join(missing_declaration["errors"]))

        child.write_text(child_text, encoding="utf-8")
        parent.unlink()
        invalid = validate_repository(root)
        self.assertIn("缺少对应母题节点", "\n".join(invalid["errors"]))

    def test_derived_ids_roll_to_only_two_parent_prefixes(self) -> None:
        root = self.make_repo()
        chain = [
            ("0001", "root", None, "0002-root_child"),
            ("0002", "root_child", "0001-root", "0003-root_child_grandchild"),
            ("0003", "root_child_grandchild", "0002-root_child", "0004-child_grandchild_greatgrandchild"),
            ("0004", "child_grandchild_greatgrandchild", "0003-root_child_grandchild", None),
        ]
        files = {}
        for number, node_id, parent, child in chain:
            text = node_text(node_id, node_id, number)
            relations = []
            if parent:
                relations.append(f"  - 节点: {parent}\n    关系: 直接母题\n")
            if child:
                relations.append(f"  - 节点: {child}\n    关系: 直接派生\n")
            if relations:
                text += "相关节点:\n" + "".join(relations)
            file = root / "nodes" / f"{number}-{node_id}.yaml"
            file.write_text(text, encoding="utf-8")
            files[number] = file

        self.assertEqual([], validate_repository(root)["errors"])

        old_id = "root_child_grandchild_greatgrandchild"
        old_stem = f"0004-{old_id}"
        files["0003"].write_text(
            files["0003"].read_text(encoding="utf-8").replace(
                "0004-child_grandchild_greatgrandchild", old_stem
            ),
            encoding="utf-8",
        )
        files["0004"].unlink()
        (root / "nodes" / f"{old_stem}.yaml").write_text(
            node_text(old_id, old_id, "0004")
            + "相关节点:\n  - 节点: 0003-root_child_grandchild\n    关系: 直接母题\n",
            encoding="utf-8",
        )

        result = validate_repository(root)
        self.assertIn(
            "两级滚动母题前缀，应为：`child_grandchild_greatgrandchild`",
            "\n".join(result["errors"]),
        )

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


    def test_evidence_source_keys_merge_only_deterministic_variants(self) -> None:
        equivalent_groups = [
            [
                "HTTP://Example.COM:80/evidence/?utm_source=newsletter#section",
                "https://example.com/evidence",
            ],
            [
                "https://github.com/OpenAI/Repo/blob/main/docs/A.md?plain=1#L1",
                "https://raw.githubusercontent.com/openai/repo/main/docs/A.md",
            ],
            [
                "https://arxiv.org/abs/2408.14007v1",
                "https://www.arxiv.org/html/2408.14007v3",
            ],
            [
                "http://dx.doi.org/10.1000/ABC",
                "https://doi.org/10.1000/abc/",
            ],
            [
                "https://www.bilibili.com/video/BV1HSWx6MEbG/?spm_id_from=333.788&vd_source=abc",
                "https://b23.tv/BV1HSWx6MEbG",
            ],
            [
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=1s",
                "https://youtu.be/dQw4w9WgXcQ",
            ],
        ]
        for group in equivalent_groups:
            with self.subTest(group=group):
                self.assertEqual(1, len({evidence_source_key(url) for url in group}))

        distinct_pairs = [
            ("https://example.com/evidence-a", "https://example.com/evidence-b"),
            (
                "https://github.com/openai/repo/blob/main/docs/A.md",
                "https://github.com/openai/repo/blob/main/docs/B.md",
            ),
            ("https://arxiv.org/abs/2408.14007v1", "https://arxiv.org/abs/2408.14008v1"),
            (
                "https://www.bilibili.com/video/BV1HSWx6MEbG/?p=1",
                "https://www.bilibili.com/video/BV1HSWx6MEbG/?p=2",
            ),
            ("https://b23.tv/unresolved-token", "https://www.bilibili.com/video/BV1HSWx6MEbG/"),
        ]
        for left, right in distinct_pairs:
            with self.subTest(left=left, right=right):
                self.assertNotEqual(evidence_source_key(left), evidence_source_key(right))

    def test_high_confidence_cannot_count_same_work_variants_twice(self) -> None:
        root = self.make_repo()
        variants = [
            "https://arxiv.org/abs/2408.14007v1",
            "https://arxiv.org/html/2408.14007v3",
        ]
        file = self.write_node(
            root,
            "0001-test-node",
            [public_death(variants, "高"), internal_death(), internal_death(), internal_death()],
        )

        result = validate_repository(root)

        self.assertIn("高置信度至少需要两个不同证据来源", "\n".join(result["errors"]))
        self.assertIn("同源变体链接", "\n".join(result["warnings"]))
        self.assertNotIn("超过 n-2", "\n".join(result["errors"]))
        self.assertEqual(2, result["unique_links"])
        self.assertEqual(1, result["unique_sources"])

        data = yaml.safe_load(file.read_text(encoding="utf-8"))
        data["死法"][0]["证据链接"][1] = "https://example.org/independent-evidence"
        file.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        independent = validate_repository(root)
        self.assertEqual([], independent["errors"])
        self.assertEqual([], independent["warnings"])
        self.assertEqual(2, independent["unique_sources"])

    def test_n_minus_two_counts_same_source_across_url_variants(self) -> None:
        root = self.make_repo()
        variants = [
            "https://github.com/OpenAI/Repo/blob/main/docs/A.md",
            "https://raw.githubusercontent.com/openai/repo/main/docs/A.md",
            "https://github.com/openai/repo/raw/main/docs/A.md#evidence",
        ]
        self.write_node(
            root,
            "0001-test-node",
            [*(public_death([url]) for url in variants), internal_death()],
        )

        result = validate_repository(root)

        self.assertIn("同源证据 `github-file:openai/repo/main/docs/A.md` 复用 3 次，超过 n-2=2", "\n".join(result["errors"]))
        self.assertEqual(3, result["unique_links"])
        self.assertEqual(1, result["unique_sources"])

    def test_related_cluster_concentration_warns_without_global_quota(self) -> None:
        root = self.make_repo()
        links = [f"https://example.com/source-{index}" for index in range(4)]
        deaths = [public_death([url]) for url in links]
        self.write_node(
            root,
            "0001-alpha",
            deaths,
            [{"节点": "0002-beta", "关系": "测试关联"}],
        )
        self.write_node(
            root,
            "0002-beta",
            deaths,
            [{"节点": "0001-alpha", "关系": "测试关联"}],
        )

        related = validate_repository(root)

        self.assertEqual([], related["errors"])
        self.assertIn("相关节点共享 4 个同源来源", "\n".join(related["warnings"]))
        self.assertIn("不得仅为消除警告替换链接", "\n".join(related["warnings"]))

        for stem in ("0001-alpha", "0002-beta"):
            file = root / "nodes" / f"{stem}.yaml"
            data = yaml.safe_load(file.read_text(encoding="utf-8"))
            del data["相关节点"]
            file.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        unrelated = validate_repository(root)
        self.assertEqual([], unrelated["errors"])
        self.assertEqual([], unrelated["warnings"])

    def test_one_source_repeated_along_four_node_relation_chain_warns(self) -> None:
        root = self.make_repo()
        shared = "https://example.com/shared-baseline"
        stems = ["0001-alpha", "0002-beta", "0003-gamma", "0004-delta"]
        for index, stem in enumerate(stems):
            relations = []
            if index:
                relations.append({"节点": stems[index - 1], "关系": "测试关联"})
            if index + 1 < len(stems):
                relations.append({"节点": stems[index + 1], "关系": "测试关联"})
            self.write_node(
                root,
                stem,
                [
                    public_death([shared, f"https://example.org/unique-{index}"]),
                    internal_death(),
                    internal_death(),
                ],
                relations,
            )

        result = validate_repository(root)

        self.assertEqual([], result["errors"])
        self.assertIn("沿显式相关节点链覆盖 4 个节点", "\n".join(result["warnings"]))
        self.assertIn(shared, "\n".join(result["warnings"]))
        self.assertNotIn("相关节点共享 4 个同源来源", "\n".join(result["warnings"]))

    def test_derived_child_needs_a_source_new_to_its_ancestor_chain(self) -> None:
        root = self.make_repo()
        self.write_node(
            root,
            "0001-parent",
            [public_death(["https://arxiv.org/abs/2408.14007v1"]), internal_death(), internal_death()],
            [{"节点": "0002-parent_child", "关系": "直接派生"}],
        )
        child = self.write_node(
            root,
            "0002-parent_child",
            [public_death(["https://arxiv.org/html/2408.14007v3"]), internal_death(), internal_death()],
            [{"节点": "0001-parent", "关系": "直接母题"}],
        )

        inherited_only = validate_repository(root)

        self.assertEqual([], inherited_only["errors"])
        self.assertIn("直接派生子题没有超出全部祖先链的新增同源来源", "\n".join(inherited_only["warnings"]))

        data = yaml.safe_load(child.read_text(encoding="utf-8"))
        data["死法"] = [
            data["死法"][0],
            public_death(["https://example.org/child-mechanism"]),
            internal_death(),
        ]
        child.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        with_new_source = validate_repository(root)
        self.assertEqual([], with_new_source["errors"])
        self.assertNotIn("新增同源来源", "\n".join(with_new_source["warnings"]))


if __name__ == "__main__":
    unittest.main()
