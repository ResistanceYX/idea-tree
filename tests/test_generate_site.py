import json
import re
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from scripts.generate_site import (
    NUMBERED_MARKER,
    build_site,
    join_soft,
    load_nodes,
    parse_acknowledgements,
    parse_prose,
    reasoning_preview,
    render_acknowledgements,
    render_detail,
    render_index,
    render_prose,
)


class LocalLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.links.append(value)


def node_text(
    node_id: str,
    title: str,
    death_type: str = "伪需求",
    status: str = "死透",
    archive: str = "预审",
) -> str:
    return f"""id: {node_id}
标题: {title}
一句话: 用于验证公开静态站的测试节点
档案类型: {archive}
复活状态: {status}
重启预算: 低
创新类型: [渐进式]
领域: 测试领域
子领域: 测试子领域
死法:
  - 类型: {death_type}
    证据: 创始人自我分析
    分析: 仅用于测试静态站生成，不代表真实创业结论
    置信度: 中
可拆零件:
  - 测试零件
死因保质期: 2028-01-01
起草AI: 测试AI
审核人: 测试审核人
审核日期: 2026-01-01
"""


class SiteGeneratorTests(unittest.TestCase):
    def make_repo(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        (root / "nodes").mkdir()
        assets = root / "site" / "assets"
        assets.mkdir(parents=True)
        (assets / "style.css").write_text("body { color: black; }\n", encoding="utf-8")
        (assets / "site.js").write_text("(() => {})();\n", encoding="utf-8")
        (root / "README.md").write_text(
            """# 测试仓库

## 特别鸣谢

**测试助手**：用于验证鸣谢页生成
- 模型：测试模型
- 休眠时间：未知
- 作品：如下表

| 编号 | 工作 | 链接 |
|---|---|---|
| 1 | 初稿、复检 | [nodes/alpha.yaml](nodes/alpha.yaml) |
| 2 | 私人附件 | [evidence/private.xlsx](evidence/private.xlsx) |
| 3 | 储备区条目 | [non-startup-tech/reserve.yaml](non-startup-tech/reserve.yaml) |
""",
            encoding="utf-8",
        )
        return root

    def add_node(self, root: Path, node_id: str, title: str, **kwargs: str) -> Path:
        file = root / "nodes" / f"{node_id}.yaml"
        file.write_text(node_text(node_id, title, **kwargs), encoding="utf-8")
        return file

    def build(self, root: Path) -> Path:
        output = root / "public"
        build_site(root, output)
        return output

    def test_index_contains_statistics_filters_and_noscript_records(self) -> None:
        root = self.make_repo()
        self.add_node(root, "alpha", "甲节点", death_type="政策风险", status="复活候选")
        self.add_node(root, "beta", "乙节点", archive="验尸")

        content = render_index(load_nodes(root))

        self.assertIn('<span class="brand-slogan">每个点子，只死一次。</span>', content)
        self.assertIn('<h1 class="archive-title">死法档案</h1>', content)
        self.assertNotIn('<h1>每个点子', content)
        self.assertEqual(content.count('1（50.0%）'), 2)
        self.assertIn('<span>正式节点</span>', content)
        self.assertIn('<span>死法条目</span>', content)
        self.assertIn('<span>预审</span>', content)
        self.assertIn('<span>验尸</span>', content)
        self.assertIn('<span>死透<strong>1</strong></span>', content)
        self.assertIn('<span>复活候选<strong>1</strong></span>', content)
        self.assertIn('<span>已复活<strong>0</strong></span>', content)
        self.assertIn('id="domain-filter"', content)
        self.assertIn('name="death-filter" value="政策风险"', content)
        self.assertIn('id="status-filter"', content)
        self.assertIn('id="archive-filter"', content)
        self.assertIn('data-domain="测试领域"', content)
        self.assertIn('data-deaths="政策风险"', content)
        self.assertIn('data-status="复活候选"', content)
        self.assertIn('data-archive="验尸"', content)
        self.assertIn('class="status-tag revival-tag candidate">复活候选</span>', content)
        self.assertIn('<summary>快速查看：一句话、推理与零件</summary>', content)
        self.assertIn('第一条推理／分析', content)
        self.assertIn('仅用于测试静态站生成', content)
        self.assertIn('可拆零件', content)
        self.assertIn('了解预审', content)
        self.assertIn('<h2 id="filters-title" tabindex="-1">检索档案</h2>', content)
        self.assertIn('<h2 id="catalog-title" tabindex="-1">节点索引</h2>', content)
        self.assertIn('死法类型（多选，满足任一）', content)
        self.assertIn('id="filter-results-link"', content)
        self.assertIn('查看 2 个结果 ↑', content)
        self.assertIn('class="status-guide"', content)
        self.assertIn('当前完整路线按现有证据判为不可行或不再成立', content)
        self.assertIn('href="acknowledgements.html"', content)
        self.assertIn('href="nodes/alpha.html"', content)
        self.assertIn('/blob/main/nodes/alpha.yaml', content)

    def test_quick_view_uses_excerpt_and_at_most_three_parts(self) -> None:
        root = self.make_repo()
        alpha = self.add_node(root, "alpha", "甲节点")
        data = yaml.safe_load(alpha.read_text(encoding="utf-8"))
        data["死法"][0]["分析"] = "第一个完整论点。第二个完整论点不应进入快速查看。"
        data["可拆零件"] = ["零件一", "零件二", "零件三", "零件四", "零件五"]

        content = render_index([(alpha, data)])
        preview = content.split('<details class="record-preview">', 1)[1].split('</details>', 1)[0]

        self.assertIn("第一个完整论点。", preview)
        self.assertNotIn("第二个完整论点", preview)
        self.assertEqual(preview.count("<li>"), 3)
        self.assertIn("零件三", preview)
        self.assertNotIn("零件四", preview)
        self.assertIn("共 5 个零件，完整清单见完整档案。", preview)
        self.assertNotIn("…", preview)
        self.assertIn("第二个完整论点", content, "全文检索数据不应被预览截断破坏")
        self.assertIn("零件五", content)

    def test_reasoning_preview_preserves_short_text_and_shortens_long_sentence(self) -> None:
        self.assertEqual(reasoning_preview("短内容，没有句末标点"), "短内容，没有句末标点")
        self.assertEqual(reasoning_preview("第一句。第二句。"), "第一句。")

        preview = reasoning_preview("甲" * 180 + "，" + "乙" * 80 + "。")

        self.assertLessEqual(len(preview), 240)
        self.assertGreaterEqual(len(preview), 180)
        self.assertTrue(preview.endswith("…"))
        self.assertNotIn("乙", preview)

        numbered = "一，" + "甲" * 90 + "；\n  二，" + "乙" * 90 + "；\n  三，" + "丙" * 60 + "。"
        numbered_preview = reasoning_preview(numbered)
        self.assertNotIn("\n", numbered_preview)
        self.assertFalse(numbered_preview.endswith("三…"), numbered_preview)
        self.assertTrue(numbered_preview.endswith("乙…"), numbered_preview)

    def test_detail_preserves_evidence_reasoning_parts_and_related_links(self) -> None:
        root = self.make_repo()
        alpha = self.add_node(root, "alpha", "甲节点")
        self.add_node(root, "beta", "乙节点")
        data = yaml.safe_load(alpha.read_text(encoding="utf-8"))
        data["相关节点"] = [{"节点": "beta", "关系": "同源母题", "说明": "测试关系"}]
        data["需求证据"] = {"类型": "访谈记录", "附件": "evidence/private.xlsx"}

        content = render_detail(
            alpha,
            data,
            {"alpha": alpha, "beta": root / "nodes" / "beta.yaml"},
            {"alpha": "甲节点", "beta": "乙节点"},
        )

        for expected in ("死法1 · 伪需求", "置信度：中", "创始人自我分析", "仅用于测试静态站生成", "测试零件", "审核日期", "死因保质期"):
            self.assertIn(expected, content)
        self.assertIn('<details class="death" id="death-1" open>', content)
        self.assertIn('id="death-actions" hidden', content)
        self.assertIn('各死法默认收起，可逐条展开；通过死法锚点打开时会自动展开目标。', content)
        self.assertIn('src="../assets/site.js"', content)
        self.assertIn('href="beta.html">乙节点</a>', content)
        self.assertNotIn('href="beta.html">beta</a>', content)
        self.assertIn('href="../index.html"', content)
        self.assertIn('/blob/main/nodes/alpha.yaml', content)
        self.assertIn('记录类型：访谈记录', content)
        self.assertIn('附件不通过静态站发布', content)
        self.assertNotIn('private.xlsx', content)

    def test_parse_prose_joins_soft_lines_without_fusing_words(self) -> None:
        self.assertEqual(join_soft("multi", "  Agent"), "multi Agent")
        self.assertEqual(join_soft("1.", "6倍"), "1.6倍")
        self.assertEqual(join_soft("OpenRouter", "于2026年"), "OpenRouter于2026年")
        self.assertEqual(
            parse_prose("这是一句因为源文件宽度而拆开的中文，\n下一行仍然属于同一句。"),
            [("paragraph", "这是一句因为源文件宽度而拆开的中文，下一行仍然属于同一句。")],
        )
        self.assertEqual(reasoning_preview("multi\n  Agent完成第一句。第二句。"), "multi Agent完成第一句。")

    def test_parse_prose_renders_numbered_arguments_without_duplicate_markers(self) -> None:
        source = "一，第一论点尚未结束，\n    这里仍是第一论点；\n二，第二论点。"

        blocks = parse_prose(source)
        content = render_prose(source)

        self.assertEqual(blocks, [("ordered_list", ["第一论点尚未结束，这里仍是第一论点；", "第二论点。"])])
        self.assertIn('<ol class="argument-list">', content)
        self.assertEqual(content.count("<li>"), 2)
        self.assertNotIn("一，", content)
        self.assertNotIn("二，", content)

    def test_parse_prose_separates_conclusion_and_note(self) -> None:
        source = (
            "一，第一论点。\n"
            "二，第二论点。\n"
            "三层生态位各有占位者，独立平台难以进入。\n"
            "边界说明：该结论只在特定条件下成立，\n"
            "（条件仍在下一行）。"
        )

        self.assertEqual(
            parse_prose(source),
            [
                ("ordered_list", ["第一论点。", "第二论点。"]),
                ("paragraph", "三层生态位各有占位者，独立平台难以进入。"),
                ("note", "边界说明：该结论只在特定条件下成立，（条件仍在下一行）。"),
            ],
        )

    def test_parse_prose_does_not_treat_decimals_or_paper_ids_as_lists(self) -> None:
        paragraphs = parse_prose("1.6倍增长不是列表。\n2502.08788号论文也不是列表。")
        numbered = parse_prose("1. 第一项。\n2、第二项。")

        self.assertEqual(paragraphs, [("paragraph", "1.6倍增长不是列表。2502.08788号论文也不是列表。")])
        self.assertEqual(numbered, [("ordered_list", ["第一项。", "第二项。"])])

    def test_parse_prose_preserves_blank_paragraphs_and_escapes_html(self) -> None:
        blocks = parse_prose("第一段。\n\n第二段。")
        content = render_prose("一，<script>alert(1)</script>与<strong>纯文本</strong>。")

        self.assertEqual(blocks, [("paragraph", "第一段。"), ("paragraph", "第二段。")])
        self.assertNotIn("<script>alert(1)</script>", content)
        self.assertNotIn("<strong>纯文本</strong>", content)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", content)
        self.assertIn("&lt;strong&gt;纯文本&lt;/strong&gt;", content)

    def test_detail_renders_reasoning_as_semantic_blocks(self) -> None:
        root = self.make_repo()
        alpha = self.add_node(root, "alpha", "甲节点")
        data = yaml.safe_load(alpha.read_text(encoding="utf-8"))
        data["死法"][0]["分析"] = "一，第一项。\n二，第二项。\n结论：两项完整保留。\n边界说明：仅用于测试。"

        content = render_detail(alpha, data, {"alpha": alpha})

        self.assertIn('<div class="rich-text">', content)
        self.assertIn('<ol class="argument-list">', content)
        self.assertIn('class="argument-note"', content)
        self.assertIn('<p class="argument-note">结论：两项完整保留。</p>', content)
        rich_text = content.split('<div class="rich-text">', 1)[1].split('</div>', 1)[0]
        self.assertEqual(rich_text.count("<li>"), 2)

    def test_real_reasoning_fields_preserve_all_text(self) -> None:
        root = Path(__file__).resolve().parents[1]
        records = load_nodes(root)
        self.assertTrue(records)

        for file, data in records:
            for index, death in enumerate(data.get("死法", []), start=1):
                source = death.get("推理") or death.get("分析") or ""
                blocks = parse_prose(source)
                source_lines = []
                for line in str(source).splitlines():
                    marker = NUMBERED_MARKER.match(line)
                    source_lines.append(marker.group("body") if marker else line)
                expected = re.sub(r"\s+", "", "".join(source_lines))
                actual_parts = []
                for kind, payload in blocks:
                    if kind == "ordered_list":
                        self.assertTrue(payload)
                        self.assertFalse(any(not item for item in payload))
                        actual_parts.extend(payload)
                    else:
                        self.assertTrue(payload)
                        actual_parts.append(payload)
                actual = re.sub(r"\s+", "", "".join(actual_parts))
                self.assertEqual(actual, expected, f"{file.name} 死法{index} 的论证文字发生变化")

    def test_acknowledgements_are_parsed_and_private_rows_are_omitted(self) -> None:
        root = self.make_repo()

        people = parse_acknowledgements(root)
        content = render_acknowledgements(people)

        self.assertEqual(len(people), 1)
        self.assertEqual(people[0]["name"], "测试助手")
        self.assertEqual(len(people[0]["works"]), 1)
        self.assertIn('href="#assistant-1"', content)
        self.assertIn("测试模型", content)
        self.assertNotIn("evidence/", content)
        self.assertNotIn("non-startup-tech/", content)
        (root / "README.md").unlink()
        self.assertEqual(parse_acknowledgements(root), [])

    def test_no_script_detail_leaves_first_two_deaths_open(self) -> None:
        root = self.make_repo()
        alpha = self.add_node(root, "alpha", "甲节点")
        data = yaml.safe_load(alpha.read_text(encoding="utf-8"))
        data["死法"] = [dict(data["死法"][0]) for _index in range(3)]

        content = render_detail(alpha, data, {"alpha": alpha})

        self.assertIn('<details class="death" id="death-1" open>', content)
        self.assertIn('<details class="death" id="death-2" open>', content)
        self.assertIn('<details class="death" id="death-3">', content)

    def test_build_outputs_all_public_files_and_excludes_private_material(self) -> None:
        root = self.make_repo()
        self.add_node(root, "alpha", "甲节点")
        (root / "evidence").mkdir()
        (root / "evidence" / "private.xlsx").write_bytes(b"not public")
        (root / "non-startup-tech").mkdir()
        (root / "non-startup-tech" / "reserve.yaml").write_text("id: reserve\n", encoding="utf-8")
        (root / "BACKUP.md").write_text("backup metadata\n", encoding="utf-8")

        output = self.build(root)

        self.assertTrue((output / "index.html").is_file())
        self.assertTrue((output / "acknowledgements.html").is_file())
        self.assertTrue((output / "nodes" / "alpha.html").is_file())
        self.assertTrue((output / "assets" / "style.css").is_file())
        self.assertTrue((output / "assets" / "site.js").is_file())
        self.assertTrue((output / "data" / "nodes.json").is_file())
        self.assertTrue((output / ".nojekyll").is_file())
        self.assertFalse((output / "evidence").exists())
        self.assertFalse((output / "non-startup-tech").exists())
        self.assertFalse((output / "BACKUP.md").exists())
        acknowledgements = (output / "acknowledgements.html").read_text(encoding="utf-8")
        self.assertIn("测试助手", acknowledgements)
        self.assertIn("初稿、复检", acknowledgements)
        self.assertIn("/blob/main/nodes/alpha.yaml", acknowledgements)
        self.assertNotIn("私人附件", acknowledgements)
        self.assertNotIn("储备区条目", acknowledgements)
        self.assertNotIn("private.xlsx", acknowledgements)
        self.assertNotIn("reserve.yaml", acknowledgements)
        payload = json.loads((output / "data" / "nodes.json").read_text(encoding="utf-8"))
        self.assertEqual(len(payload), 1)
        self.assertEqual(
            set(payload[0]),
            {"id", "标题", "档案类型", "复活状态", "领域", "子领域", "死法类型", "审核日期", "死因保质期", "相关节点", "页面"},
        )
        self.assertNotIn("证据", payload[0])
        self.assertNotIn("需求证据", payload[0])

    def test_new_node_is_included_on_next_build(self) -> None:
        root = self.make_repo()
        self.add_node(root, "alpha", "甲节点")
        output = self.build(root)
        self.assertEqual(len(json.loads((output / "data" / "nodes.json").read_text(encoding="utf-8"))), 1)

        self.add_node(root, "beta", "乙节点", status="已复活")
        build_site(root, output)

        self.assertTrue((output / "nodes" / "beta.html").is_file())
        index = (output / "index.html").read_text(encoding="utf-8")
        self.assertIn("乙节点", index)
        self.assertIn("显示 2 / 2 个节点", index)
        self.assertEqual(len(json.loads((output / "data" / "nodes.json").read_text(encoding="utf-8"))), 2)

    def test_repeated_build_is_deterministic_and_relative_links_resolve(self) -> None:
        root = self.make_repo()
        alpha = self.add_node(root, "alpha", "甲节点")
        self.add_node(root, "beta", "乙节点")
        data = yaml.safe_load(alpha.read_text(encoding="utf-8"))
        data["相关节点"] = [{"节点": "beta", "关系": "同源母题"}]
        alpha.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
        output = self.build(root)
        first = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}

        build_site(root, output)
        second = {path.relative_to(output): path.read_bytes() for path in output.rglob("*") if path.is_file()}

        self.assertEqual(first, second)
        for html_file in output.rglob("*.html"):
            parser = LocalLinkParser()
            parser.feed(html_file.read_text(encoding="utf-8"))
            for link in parser.links:
                split = urlsplit(link)
                if split.scheme or link.startswith(("#", "//")):
                    continue
                target = (html_file.parent / split.path).resolve()
                self.assertTrue(target.is_file(), f"{html_file}: 无效本地链接 {link}")

    def test_html_content_is_escaped(self) -> None:
        root = self.make_repo()
        file = self.add_node(root, "alpha", "甲节点")
        data = yaml.safe_load(file.read_text(encoding="utf-8"))
        data["标题"] = '<script>alert("x")</script>'

        content = render_index([(file, data)])

        self.assertNotIn('<script>alert("x")</script>', content)
        self.assertIn('&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;', content)

    def test_output_directory_cannot_erase_repository_or_parent(self) -> None:
        root = self.make_repo()
        self.add_node(root, "alpha", "甲节点")

        with self.assertRaises(ValueError):
            build_site(root, root)
        with self.assertRaises(ValueError):
            build_site(root, root.parent)


if __name__ == "__main__":
    unittest.main()
