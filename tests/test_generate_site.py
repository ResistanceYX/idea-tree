import json
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import yaml

from scripts.generate_site import build_site, load_nodes, render_detail, render_index


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
        self.assertIn('id="death-filter"', content)
        self.assertIn('id="status-filter"', content)
        self.assertIn('id="archive-filter"', content)
        self.assertIn('data-domain="测试领域"', content)
        self.assertIn('data-deaths="政策风险"', content)
        self.assertIn('data-status="复活候选"', content)
        self.assertIn('data-archive="验尸"', content)
        self.assertIn('class="status-tag revival-tag candidate">复活候选</span>', content)
        self.assertIn('<summary>快速查看</summary>', content)
        self.assertIn('href="nodes/alpha.html"', content)
        self.assertIn('/blob/main/nodes/alpha.yaml', content)

    def test_detail_preserves_evidence_reasoning_parts_and_related_links(self) -> None:
        root = self.make_repo()
        alpha = self.add_node(root, "alpha", "甲节点")
        self.add_node(root, "beta", "乙节点")
        data = yaml.safe_load(alpha.read_text(encoding="utf-8"))
        data["相关节点"] = [{"节点": "beta", "关系": "同源母题", "说明": "测试关系"}]
        data["需求证据"] = {"类型": "访谈记录", "附件": "evidence/private.xlsx"}

        content = render_detail(alpha, data, {"alpha": alpha, "beta": root / "nodes" / "beta.yaml"})

        for expected in ("死法1 · 伪需求", "置信度：中", "创始人自我分析", "仅用于测试静态站生成", "测试零件", "审核日期", "死因保质期"):
            self.assertIn(expected, content)
        self.assertIn('href="beta.html"', content)
        self.assertIn('href="../index.html"', content)
        self.assertIn('/blob/main/nodes/alpha.yaml', content)
        self.assertIn('记录类型：访谈记录', content)
        self.assertIn('附件不通过静态站发布', content)
        self.assertNotIn('private.xlsx', content)

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
        self.assertTrue((output / "nodes" / "alpha.html").is_file())
        self.assertTrue((output / "assets" / "style.css").is_file())
        self.assertTrue((output / "assets" / "site.js").is_file())
        self.assertTrue((output / "data" / "nodes.json").is_file())
        self.assertTrue((output / ".nojekyll").is_file())
        self.assertFalse((output / "evidence").exists())
        self.assertFalse((output / "non-startup-tech").exists())
        self.assertFalse((output / "BACKUP.md").exists())
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
