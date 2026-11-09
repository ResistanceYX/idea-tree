#!/usr/bin/env python3
"""Build idea-tree's public static site without copying evidence or backups."""

from __future__ import annotations

import argparse
import html
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import yaml

REPOSITORY_URL = "https://github.com/ResistanceYX/idea-tree"
DEATH_TYPES = (
    "伪需求",
    "钱算不平",
    "巨头碾压",
    "政策风险",
    "季节魔咒",
    "冷启动死锁",
    "信任成本",
    "条件已死",
    "执行人限制",
    "理论证伪",
)
ARCHIVE_TYPES = ("预审", "验尸")
REVIVAL_STATUSES = ("死透", "复活候选", "已复活")


def text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    return str(value)


def escape(value: object) -> str:
    return html.escape(text(value), quote=True)


def load_nodes(root: Path) -> list[tuple[Path, dict]]:
    files = sorted((root / "nodes").glob("*.yaml"), key=lambda path: path.name)
    if not files:
        raise ValueError("nodes/ 中没有 YAML 节点")
    records: list[tuple[Path, dict]] = []
    for file in files:
        data = yaml.safe_load(file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"nodes/{file.name} 的顶层必须是映射")
        records.append((file, data))
    return records


def death_types(data: dict) -> list[str]:
    present = {
        death.get("类型")
        for death in data.get("死法", [])
        if isinstance(death, dict) and isinstance(death.get("类型"), str)
    }
    ordered = [item for item in DEATH_TYPES if item in present]
    ordered.extend(sorted(present.difference(DEATH_TYPES)))
    return ordered


def revival_class(status: str) -> str:
    return {"死透": "dead", "复活候选": "candidate", "已复活": "revived"}.get(status, "unknown")


def page_head(title: str, description: str, prefix: str = "") -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{escape(description)}">
  <meta name="theme-color" content="#12151c">
  <title>{escape(title)} · idea-tree</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%2312151c'/%3E%3Cpath d='M32 12v40M32 26 18 18M32 34l14-8M32 44 20 52' fill='none' stroke='%23c5a059' stroke-width='4'/%3E%3C/svg%3E">
  <link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<a class="skip-link" href="#main-content">跳到正文</a>"""


def page_header(prefix: str = "", detail: bool = False) -> str:
    index_label = "返回节点索引" if detail else "节点索引"
    return f"""<header class="topbar">
  <div class="topbar-inner">
    <div class="brand-lockup">
      <a class="brand" href="{prefix}index.html" aria-label="idea-tree首页">idea-tree</a>
      <span class="brand-divider" aria-hidden="true"></span>
      <span class="brand-slogan">每个点子，只死一次。</span>
    </div>
    <nav class="topnav" aria-label="主导航">
      <a href="{prefix}index.html">{index_label}</a>
      <a href="{REPOSITORY_URL}" target="_blank" rel="noopener noreferrer">GitHub仓库 ↗</a>
    </nav>
  </div>
</header>"""


def page_footer(prefix: str = "") -> str:
    return f"""<footer class="footer">
  <div class="shell footer-inner">
    <span>由结构化YAML生成 · AI初稿，人类审核定案</span>
    <a href="{REPOSITORY_URL}/blob/main/README.md" target="_blank" rel="noopener noreferrer">项目规范与编辑约定 ↗</a>
  </div>
</footer>
</body>
</html>
"""


def select_options(values: list[str], all_label: str) -> str:
    options = [f'<option value="">{all_label}</option>']
    options.extend(f'<option value="{escape(value)}">{escape(value)}</option>' for value in values)
    return "\n".join(options)


def source_label(url: str, index: int) -> str:
    host = urlparse(url).netloc or "公开来源"
    return f"来源{index} · {host}"


def render_index(records: list[tuple[Path, dict]]) -> str:
    records = sorted(
        records,
        key=lambda record: (text(record[1].get("死因保质期")) or "9999-12-31", text(record[1].get("id"))),
    )
    death_counts: Counter[str] = Counter()
    for _file, data in records:
        for death in data.get("死法", []):
            if isinstance(death, dict) and isinstance(death.get("类型"), str):
                death_counts[death["类型"]] += 1

    domains = sorted({text(data.get("领域")) for _file, data in records if data.get("领域")})
    present_deaths = [item for item in DEATH_TYPES if death_counts[item]]
    present_deaths.extend(sorted(set(death_counts).difference(DEATH_TYPES)))
    max_count = max(death_counts.values(), default=1)
    total_deaths = sum(death_counts.values())

    distribution = []
    for death_type in present_deaths:
        width = round(death_counts[death_type] / max_count * 100, 2)
        percentage = death_counts[death_type] / total_deaths * 100 if total_deaths else 0
        distribution.append(
            f"""<div class="distribution-row">
  <span>{escape(death_type)}</span>
  <div class="distribution-track" aria-hidden="true"><div class="distribution-fill" style="width:{width}%"></div></div>
  <span class="distribution-count">{death_counts[death_type]}（{percentage:.1f}%）</span>
</div>"""
        )

    rows = []
    for file, data in records:
        node_id = text(data.get("id", file.stem))
        title = text(data.get("标题", node_id))
        domain = text(data.get("领域"))
        subdomain = text(data.get("子领域"))
        types = death_types(data)
        status = text(data.get("复活状态"))
        archive = text(data.get("档案类型"))
        expiry = text(data.get("死因保质期"))
        one_line = text(data.get("一句话"))
        search = " ".join((title, node_id, domain, subdomain, " ".join(types), status, archive, one_line))
        rows.append(
            f"""<article class="record" data-search="{escape(search)}" data-domain="{escape(domain)}" data-deaths="{escape('|'.join(types))}" data-status="{escape(status)}" data-archive="{escape(archive)}">
  <div class="record-main">
    <div class="record-title">
      <a href="nodes/{escape(file.stem)}.html">{escape(title)}</a>
      <p class="record-id">{escape(node_id)}</p>
    </div>
    <div class="record-domain">{escape(domain)}<br><span class="record-id">{escape(subdomain)}</span></div>
    <div class="record-deaths">{escape("、".join(types))}</div>
    <div class="record-status"><span class="status-tag archive-tag">{escape(archive)}</span><span class="status-tag revival-tag {revival_class(status)}">{escape(status)}</span></div>
    <div class="record-expiry">{escape(expiry)}</div>
  </div>
  <details>
    <summary>快速查看</summary>
    <p class="record-summary">{escape(one_line)}</p>
    <div class="record-actions">
      <a href="nodes/{escape(file.stem)}.html">阅读完整档案</a>
      <a href="{REPOSITORY_URL}/blob/main/nodes/{escape(file.name)}" target="_blank" rel="noopener noreferrer">原始YAML ↗</a>
    </div>
  </details>
</article>"""
        )

    archive_counts = Counter(text(data.get("档案类型")) for _file, data in records)
    revival_counts = Counter(text(data.get("复活状态")) for _file, data in records)
    return "\n".join(
        (
            page_head("创业点子的死法档案", "检索创业点子的预审、验尸、死因证据与可拆零件。"),
            page_header(),
            f"""<main id="main-content" class="shell index-layout">
  <aside class="intro" aria-label="项目介绍与筛选">
    <p class="kicker">Failure archive / evidence index</p>
    <h1 class="archive-title">死法档案</h1>
    <p class="lede">死因可以被检索一万次。这里收录事前预审、真实验尸、公开证据、可拆零件与复活状态。</p>
    <p class="definition">“预审”是基于证据与推演的事前判断；“验尸”来自真实实施、停止、失败或转向记录。二者不混写。</p>
    <div class="stats" aria-label="节点、死法与档案类型统计">
      <div class="stat"><strong>{len(records)}</strong><span>正式节点</span></div>
      <div class="stat"><strong>{total_deaths}</strong><span>死法条目</span></div>
      <div class="stat"><strong>{archive_counts['预审']}</strong><span>预审</span></div>
      <div class="stat"><strong>{archive_counts['验尸']}</strong><span>验尸</span></div>
    </div>
    <div class="revival-stats" aria-label="复活状态统计">
      {''.join(f'<span>{status}<strong>{revival_counts[status]}</strong></span>' for status in REVIVAL_STATUSES)}
    </div>
    <form class="filters" aria-label="检索节点" onsubmit="return false">
      <h2>检索档案</h2>
      <div class="field">
        <label for="search">标题、id或内容</label>
        <input id="search" type="search" placeholder="例如：巨头碾压、AI、开源" autocomplete="off">
      </div>
      <div class="field">
        <label for="domain-filter">领域</label>
        <select id="domain-filter">{select_options(domains, '全部领域')}</select>
      </div>
      <div class="field">
        <label for="death-filter">死法类型</label>
        <select id="death-filter">{select_options(present_deaths, '全部死法')}</select>
      </div>
      <div class="field">
        <label for="status-filter">复活状态</label>
        <select id="status-filter">{select_options(list(REVIVAL_STATUSES), '全部状态')}</select>
      </div>
      <div class="field">
        <label for="archive-filter">档案类型</label>
        <select id="archive-filter">{select_options(list(ARCHIVE_TYPES), '全部类型')}</select>
      </div>
      <button class="reset-button" id="reset-filters" type="button" disabled>清除筛选</button>
    </form>
    <section class="distribution" aria-labelledby="distribution-title">
      <h2 id="distribution-title">死法条目分布</h2>
      {''.join(distribution)}
    </section>
  </aside>
  <section class="catalog" aria-labelledby="catalog-title">
    <div class="catalog-head">
      <h2 id="catalog-title">节点索引</h2>
      <p class="result-count" id="result-count" aria-live="polite">显示 {len(records)} / {len(records)} 个节点</p>
    </div>
    <div class="record-labels" aria-hidden="true"><span>节点／id</span><span>领域</span><span>死法</span><span>类型／状态</span><span>死因保质期</span></div>
    {''.join(rows)}
    <div class="empty-state" id="empty-state" hidden><p>没有匹配的节点。请减少筛选条件，或清除后重新检索。</p></div>
  </section>
</main>
<script src="assets/site.js" defer></script>""",
            page_footer(),
        )
    )


def render_detail(file: Path, data: dict, id_to_file: dict[str, Path]) -> str:
    node_id = text(data.get("id", file.stem))
    title = text(data.get("标题", node_id))
    one_line = text(data.get("一句话"))
    status = text(data.get("复活状态"))
    archive = text(data.get("档案类型"))
    metadata = [
        ("id", node_id, True),
        ("档案类型", archive, False),
        ("复活状态", status, False),
        ("领域／子领域", f"{text(data.get('领域'))}／{text(data.get('子领域'))}", False),
        ("创新类型", text(data.get("创新类型")), False),
        ("重启预算", text(data.get("重启预算")) or "未填写", False),
        ("审核日期", text(data.get("审核日期")), True),
        ("死因保质期", text(data.get("死因保质期")), True),
        ("起草AI", text(data.get("起草AI")), False),
        ("审核人", text(data.get("审核人")), False),
    ]
    metadata_html = "".join(
        f'<div><dt>{escape(label)}</dt><dd{(" class=\"mono\"" if mono else "")}>{escape(value)}</dd></div>'
        for label, value, mono in metadata
    )

    deaths_html = []
    for index, death in enumerate(data.get("死法", []), start=1):
        if not isinstance(death, dict):
            continue
        links = death.get("证据链接", []) or []
        links_html = ""
        if links:
            items = "".join(
                f'<li><a href="{escape(url)}" target="_blank" rel="noopener noreferrer">{escape(source_label(str(url), link_index))}</a></li>'
                for link_index, url in enumerate(links, start=1)
            )
            links_html = f"<h4>证据链接</h4><ol class=\"evidence-list\">{items}</ol>"
        reasoning = death.get("推理") or death.get("分析") or ""
        optional_sections = []
        for field in ("案例", "备注"):
            if death.get(field):
                optional_sections.append(f"<h4>{field}</h4><p>{escape(death.get(field))}</p>")
        deaths_html.append(
            f"""<article class="death">
  <div class="death-head">
    <h3>死法{index} · {escape(death.get('类型'))}</h3>
    <span class="confidence">置信度：{escape(death.get('置信度'))}</span>
  </div>
  <h4>证据</h4>
  <p>{escape(death.get('证据'))}</p>
  <h4>推理／分析</h4>
  <p>{escape(reasoning)}</p>
  {''.join(optional_sections)}
  {links_html}
</article>"""
        )

    parts = data.get("可拆零件", []) or []
    parts_html = "".join(f"<li>{escape(part)}</li>" for part in parts)
    relations_html = []
    for relation in data.get("相关节点", []) or []:
        if not isinstance(relation, dict):
            continue
        target = text(relation.get("节点"))
        target_file = id_to_file.get(target)
        if target_file:
            target_html = f'<a href="{escape(target_file.stem)}.html">{escape(target)}</a>'
        else:
            target_html = escape(target)
        note = relation.get("说明")
        note_html = f'<p class="relation-note">{escape(note)}</p>' if note else ""
        relations_html.append(
            f'<li>{target_html}<br><span class="relation-type">关系：{escape(relation.get("关系"))}</span>{note_html}</li>'
        )

    extra_sections = []
    if data.get("商业及社会价值评估"):
        extra_sections.append(
            f'<section class="content-section"><h2>商业及社会价值评估</h2><p class="prose">{escape(data["商业及社会价值评估"])}</p></section>'
        )
    demand = data.get("需求证据")
    if isinstance(demand, dict) and demand.get("类型"):
        extra_sections.append(
            f'<section class="content-section"><h2>需求证据</h2><p class="prose">记录类型：{escape(demand.get("类型"))}。附件不通过静态站发布，请在仓库中按既有权限与边界查看。</p></section>'
        )
    if data.get("备注"):
        extra_sections.append(
            f'<section class="content-section"><h2>节点备注</h2><p class="prose">{escape(data["备注"])}</p></section>'
        )

    return "\n".join(
        (
            page_head(title, one_line or f"{title}的死因、证据与可拆零件。", "../"),
            page_header("../", detail=True),
            f"""<main id="main-content" class="shell detail-layout">
  <aside class="detail-aside">
    <p class="kicker">Archive record / {escape(node_id)}</p>
    <h1>{escape(title)}</h1>
    <p class="detail-lede">{escape(one_line)}</p>
    <div class="badges"><span class="badge archive-tag">{escape(archive)}</span><span class="badge revival-tag {revival_class(status)}">{escape(status)}</span></div>
    <dl class="metadata">{metadata_html}</dl>
    <a class="source-link" href="{REPOSITORY_URL}/blob/main/nodes/{escape(file.name)}" target="_blank" rel="noopener noreferrer">查看原始YAML ↗</a>
  </aside>
  <div class="detail-content">
    <section class="content-section">
      <h2>死因与证据</h2>
      <p class="notice">置信度表示当前证据与推理的可靠程度，不是失败概率。预审不得理解为已经发生的失败。</p>
      {''.join(deaths_html)}
    </section>
    <section class="content-section"><h2>可拆零件</h2><ul class="parts-list">{parts_html}</ul></section>
    {''.join(extra_sections)}
    {f'<section class="content-section"><h2>相关节点</h2><ul class="relations-list">{"".join(relations_html)}</ul></section>' if relations_html else ''}
  </div>
</main>""",
            page_footer("../"),
        )
    )


def public_node_data(records: list[tuple[Path, dict]]) -> list[dict]:
    result = []
    for file, data in records:
        result.append(
            {
                "id": text(data.get("id", file.stem)),
                "标题": text(data.get("标题", file.stem)),
                "档案类型": text(data.get("档案类型")),
                "复活状态": text(data.get("复活状态")),
                "领域": text(data.get("领域")),
                "子领域": text(data.get("子领域")),
                "死法类型": death_types(data),
                "审核日期": text(data.get("审核日期")),
                "死因保质期": text(data.get("死因保质期")),
                "相关节点": [
                    {"节点": text(item.get("节点")), "关系": text(item.get("关系"))}
                    for item in data.get("相关节点", []) or []
                    if isinstance(item, dict)
                ],
                "页面": f"nodes/{file.stem}.html",
            }
        )
    return result


def build_site(root: Path, output: Path) -> int:
    root = root.resolve()
    output = output.resolve()
    if output == root or output in root.parents:
        raise ValueError("输出目录不得是仓库根目录或其上级目录")
    records = load_nodes(root)
    id_to_file = {text(data.get("id", file.stem)): file for file, data in records}
    assets = root / "site" / "assets"
    if not (assets / "style.css").is_file() or not (assets / "site.js").is_file():
        raise ValueError("site/assets/ 缺少 style.css 或 site.js")

    if output.exists():
        shutil.rmtree(output)
    (output / "nodes").mkdir(parents=True)
    (output / "data").mkdir()
    (output / "assets").mkdir()

    (output / "index.html").write_text(render_index(records), encoding="utf-8")
    for file, data in records:
        (output / "nodes" / f"{file.stem}.html").write_text(
            render_detail(file, data, id_to_file), encoding="utf-8"
        )
    (output / "data" / "nodes.json").write_text(
        json.dumps(public_node_data(records), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    shutil.copy2(assets / "style.css", output / "assets" / "style.css")
    shutil.copy2(assets / "site.js", output / "assets" / "site.js")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    return len(records)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成idea-tree公开静态索引站")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="仓库根目录，默认为当前目录")
    parser.add_argument("--output", type=Path, default=None, help="输出目录，默认为仓库下的_site")
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output if args.output is not None else root / "_site"
    try:
        count = build_site(root, output)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"[错误] 静态站生成失败：{exc}")
        return 1
    print(f"静态站已生成：{count} 个节点，输出目录 {output.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
