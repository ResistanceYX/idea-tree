#!/usr/bin/env python3
"""Build the public site with allowlisted excerpts and reserve metadata; never copy raw sources."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote, urlparse

import yaml

try:
    from scripts.generate_review import load_review_records
    from scripts.node_files import node_identity, node_sort_key, parse_node_filename
except ModuleNotFoundError:  # Direct execution: python scripts/generate_site.py
    from generate_review import load_review_records
    from node_files import node_identity, node_sort_key, parse_node_filename

REPOSITORY_URL = "https://github.com/ResistanceYX/idea-tree"
PUBLIC_SITE_URL = "https://resistanceyx.github.io/idea-tree"
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
PUBLIC_EVIDENCE = (
    {
        "source": "evidence/ai-legal-loophole-hunter_legislation-feedback-sources.md",
        "node_id": "ai-legal-loophole-hunter_legislation-feedback",
        "death": 2,
    },
)
# The editor-approved reserve registry is data, not code; list order is page order.
PUBLIC_RESERVE_REGISTRY = "non-startup-tech/00-public_reserve.yaml"


def text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "、".join(str(item) for item in value)
    return str(value)


def escape(value: object) -> str:
    return html.escape(text(value), quote=True)


NUMBERED_MARKER = re.compile(
    r"^\s*(?:[一二三四五六七八九十]+[、，]|\d+[、．.](?!\d))\s*(?P<body>.*)$"
)
NOTE_PREFIX = re.compile(r"^\s*(?:边界说明|结论|补充说明|补充)\s*[：:]")
SENTENCE_END = re.compile(r"[。！？][”’\"'）)]*$")


def join_soft(left: str, right: str) -> str:
    """Join source-wrapped prose without fusing adjacent Latin words or numbers."""
    left = left.rstrip()
    right = right.strip()
    if not left:
        return right
    if not right:
        return left
    needs_space = (
        re.search(r"[A-Za-z0-9]$", left)
        and re.match(r"[A-Za-z0-9]", right)
    )
    return left + (" " if needs_space else "") + right


def parse_prose(value: object) -> list[tuple[str, object]]:
    """Parse plain argument text into paragraphs, ordered lists and notes."""
    source = text(value).strip()
    if not source:
        return []

    blocks: list[tuple[str, object]] = []
    mode = ""
    buffer: list[str] = []
    items: list[str] = []

    def buffered_text() -> str:
        result = ""
        for line in buffer:
            result = join_soft(result, line)
        return result

    def flush_paragraph() -> None:
        nonlocal buffer
        content = buffered_text()
        if content:
            blocks.append(("paragraph", content))
        buffer = []

    def flush_list() -> None:
        nonlocal buffer, items
        content = buffered_text()
        if content:
            items.append(content)
        buffer = []
        if items:
            blocks.append(("ordered_list", items))
        items = []

    def flush_note() -> None:
        nonlocal buffer
        content = buffered_text()
        if content:
            blocks.append(("note", content))
        buffer = []

    def flush_current() -> None:
        nonlocal mode
        if mode == "ordered_list":
            flush_list()
        elif mode == "note":
            flush_note()
        elif mode == "paragraph":
            flush_paragraph()
        mode = ""

    for raw_line in source.splitlines():
        line = raw_line.strip()
        if not line:
            flush_current()
            continue

        marker = NUMBERED_MARKER.match(raw_line)
        if marker:
            if mode != "ordered_list":
                flush_current()
                mode = "ordered_list"
            else:
                content = buffered_text()
                if content:
                    items.append(content)
                buffer = []
            buffer = [marker.group("body").strip()]
            continue

        if NOTE_PREFIX.match(raw_line):
            flush_current()
            mode = "note"
            buffer = [line]
            continue

        if mode == "ordered_list":
            current = buffered_text()
            is_top_level = not raw_line[:1].isspace()
            if is_top_level and SENTENCE_END.search(current):
                flush_current()
                mode = "paragraph"
                buffer = [line]
            else:
                buffer.append(line)
            continue

        if not mode:
            mode = "paragraph"
        buffer.append(line)

    flush_current()
    return blocks


def render_prose(value: object) -> str:
    """Render escaped semantic blocks; YAML text is never treated as HTML."""
    blocks = parse_prose(value)
    if not blocks:
        return ""
    output = ['<div class="rich-text">']
    for kind, payload in blocks:
        if kind == "ordered_list":
            items = "".join(f"<li>{escape(item)}</li>" for item in payload)
            output.append(f'<ol class="argument-list">{items}</ol>')
        elif kind == "note":
            output.append(f'<p class="argument-note">{escape(payload)}</p>')
        else:
            output.append(f"<p>{escape(payload)}</p>")
    output.append("</div>")
    return "".join(output)


def public_evidence_for(node_id: str, death_index: int) -> dict | None:
    """Return the explicitly public excerpt attached to one death, if any."""
    for entry in PUBLIC_EVIDENCE:
        if entry["node_id"] == node_id and entry["death"] == death_index:
            return entry
    return None


def public_evidence_href(entry: dict) -> str:
    """Detail pages link to generated HTML, never to the source Markdown."""
    return f"../evidence/{Path(entry['source']).stem}.html"


def render_public_excerpt_markdown(value: str) -> str:
    """Render the allowlisted excerpt's headings, paragraphs and lists safely."""
    output: list[str] = []
    paragraph: list[str] = []
    list_open = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        content = ""
        for line in paragraph:
            content = join_soft(content, line)
        if content:
            output.append(f"<p>{escape(content)}</p>")
        paragraph = []

    def close_list() -> None:
        nonlocal list_open
        if list_open:
            output.append("</ul>")
        list_open = False

    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            flush_paragraph()
            close_list()
            continue
        if line.startswith("# "):
            flush_paragraph()
            close_list()
            output.append(f"<h2>{escape(line[2:].strip())}</h2>")
            continue
        if line.startswith("- "):
            flush_paragraph()
            if not list_open:
                output.append("<ul>")
                list_open = True
            output.append(f"<li>{escape(line[2:].strip())}</li>")
            continue
        close_list()
        paragraph.append(line)

    flush_paragraph()
    close_list()
    return "\n".join(output)


def load_nodes(root: Path) -> list[tuple[Path, dict]]:
    files = sorted((root / "nodes").glob("*.yaml"), key=lambda path: path.name)
    if not files:
        raise ValueError("nodes/ 中没有 YAML 节点")
    records: list[tuple[Path, dict]] = []
    for file in files:
        data = yaml.safe_load(file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"nodes/{file.name} 的顶层必须是映射")
        node_identity(file, data)
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


def public_url(path: str = "index.html") -> str:
    """Return the canonical absolute URL for one generated public path."""
    if path == "index.html":
        return PUBLIC_SITE_URL + "/"
    return f"{PUBLIC_SITE_URL}/{quote(path, safe='/.')}"


def json_ld_script(data: dict) -> str:
    """Serialize structured data without allowing source text to close the script."""
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True)
    payload = (
        payload.replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    return f'<script type="application/ld+json">{payload}</script>'


def page_head(
    title: str,
    description: str,
    prefix: str = "",
    *,
    path: str = "index.html",
    og_type: str = "website",
    structured_data: dict | None = None,
) -> str:
    canonical = public_url(path)
    title = searchable_text(title)
    description = searchable_text(description)
    structured_data_html = json_ld_script(structured_data) if structured_data else ""
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{escape(description)}">
  <meta name="theme-color" content="#12151c">
  <title>{escape(title)} · idea-tree</title>
  <link rel="canonical" href="{escape(canonical)}">
  <link rel="describedby" href="{escape(public_url('llms.txt'))}">
  <meta property="og:title" content="{escape(title)}">
  <meta property="og:description" content="{escape(description)}">
  <meta property="og:url" content="{escape(canonical)}">
  <meta property="og:type" content="{escape(og_type)}">
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' fill='%2312151c'/%3E%3Cpath d='M32 12v40M32 26 18 18M32 34l14-8M32 44 20 52' fill='none' stroke='%23c5a059' stroke-width='4'/%3E%3C/svg%3E">
  <link rel="stylesheet" href="{prefix}assets/style.css">
  {structured_data_html}
</head>
<body>
<a class="skip-link" href="#main-content">跳到正文</a>"""


def page_header(prefix: str = "", detail: bool = False, current: str = "") -> str:
    index_label = "返回节点索引" if detail else "节点索引"
    index_current = ' aria-current="page"' if current == "index" else ""
    graph_current = ' aria-current="page"' if current == "graph" else ""
    return f"""<header class="topbar">
  <div class="topbar-inner">
    <div class="brand-lockup">
      <a class="brand" href="{prefix}index.html" aria-label="idea-tree首页">idea-tree</a>
      <span class="brand-divider" aria-hidden="true"></span>
      <span class="brand-slogan">每个点子，只死一次。</span>
    </div>
    <nav class="topnav" aria-label="主导航">
      <a href="{prefix}index.html"{index_current}>{index_label}</a>
      <a href="{prefix}graph.html"{graph_current}>科技树</a>
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


ARCHIVE_DEFINITIONS = {
    "预审": "基于公开证据与推演的事前判断，不是已经发生的失败。",
    "验尸": "来自真实实施、停止、失败或转向记录，不以纯粹假设替代实际经历。",
}

REVIVAL_DEFINITIONS = {
    "死透": "当前完整路线按现有证据判为不可行或不再成立，不等于所有可拆零件都无价值。",
    "复活候选": "部分关键条件已翻案或存在可验证的缩围路线，仍需复核剩余风险。",
    "已复活": "核心条件已有证据支持发生翻案，不等于商业闭环或最终效果已经确立。",
}


def archive_term(archive: str) -> str:
    return f'<span class="status-tag archive-tag">{escape(archive)}</span>'


def reasoning_preview(value: object, limit: int = 240) -> str:
    """Keep the first complete sentence, shortening only an overlong sentence."""
    source = ""
    for line in text(value).strip().splitlines():
        source = join_soft(source, line)
    if not source:
        return ""
    sentence_end = re.search(r"[。！？!?](?:[”’\"'])?", source)
    first_sentence = source[:sentence_end.end()] if sentence_end else source
    if len(first_sentence) <= limit:
        return first_sentence

    window = first_sentence[:limit]
    boundaries = [
        match.end()
        for match in re.finditer(r"[；;]", window)
        if match.end() >= 180
    ]
    if not boundaries:
        boundaries = [
            match.end()
            for match in re.finditer(r"[，：,:]", window)
            if match.end() >= 180
        ]
    if boundaries:
        return first_sentence[:boundaries[-1] - 1].rstrip() + "…"

    cut = limit
    if (
        cut < len(first_sentence)
        and re.match(r"[A-Za-z0-9]", first_sentence[cut - 1])
        and re.match(r"[A-Za-z0-9]", first_sentence[cut])
    ):
        word_boundary = window.rfind(" ", 180)
        if word_boundary >= 180:
            cut = word_boundary
    return first_sentence[:cut].rstrip() + "…"


def render_status_guide() -> str:
    definitions = (*ARCHIVE_DEFINITIONS.items(), *REVIVAL_DEFINITIONS.items())
    items = "".join(
        f'<div><dt>{escape(term)}</dt><dd>{escape(definition)}</dd></div>'
        for term, definition in definitions
    )
    return f'''<details class="status-guide">
      <summary>状态说明</summary>
      <dl class="status-guide-definitions">{items}</dl>
    </details>'''


def parse_acknowledgements(root: Path) -> list[dict]:
    """Read one numbered file per assistant and verify the directory registry."""
    directory = root / "ACKNOWLEDGEMENTS"
    registry = directory / "README.md"
    if not directory.is_dir() or not registry.is_file():
        raise ValueError("特别鸣谢目录或名录缺失：ACKNOWLEDGEMENTS/")

    file_pattern = re.compile(r"^(\d{3})-(.+)\.md$")
    sources: list[tuple[int, str, str, Path]] = []
    seen_numbers: set[str] = set()
    for source in directory.iterdir():
        if not source.is_file() or source.name == "README.md":
            continue
        match = file_pattern.fullmatch(source.name)
        if not match:
            raise ValueError(f"特别鸣谢文件名不符合 '<三位编号>-<名字>.md'：{source.name}")
        number, name = match.groups()
        if number in seen_numbers:
            raise ValueError(f"特别鸣谢助手编号重复：{number}")
        seen_numbers.add(number)
        sources.append((int(number), number, name.strip(), source))
    if not sources:
        raise ValueError("特别鸣谢目录没有助手记录文件")
    sources.sort(key=lambda item: item[0])

    registry_rows = []
    row_pattern = re.compile(
        r"^\|\s*(\d{3})\s*\|\s*([^|]+?)\s*\|\s*\[[^\]]+\]\(([^)]+)\)\s*\|\s*$"
    )
    for line in registry.read_text(encoding="utf-8").splitlines():
        match = row_pattern.match(line)
        if match:
            number, name, target = match.groups()
            registry_rows.append((number, name.strip(), target.strip()))
    expected_rows = [
        (number, name, source.name) for _sort, number, name, source in sources
    ]
    if registry_rows != expected_rows:
        raise ValueError("特别鸣谢名录必须与编号文件按助手顺序一一对应")

    people: list[dict] = []
    for _sort, assistant_number, expected_name, source in sources:
        section = source.read_text(encoding="utf-8")
        file_people: list[dict] = []
        current: dict | None = None
        for line in section.splitlines():
            person_match = re.match(r"^\*\*(.+?)\*\*：(.*)$", line.strip())
            if person_match:
                current = {
                    "name": person_match.group(1).strip(),
                    "description": person_match.group(2).strip(),
                    "number": assistant_number,
                    "metadata": [],
                    "works": [],
                }
                file_people.append(current)
                continue
            if current is None:
                continue
            metadata_match = re.match(r"^-\s*([^：]+)：(.*)$", line.strip())
            if metadata_match and metadata_match.group(1).strip() != "作品":
                current["metadata"].append((metadata_match.group(1).strip(), metadata_match.group(2).strip()))
                continue
            row_match = re.match(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$", line)
            if not row_match:
                continue
            number, work, link_cell = row_match.groups()
            links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", link_cell)
            private_targets = (
                "evidence/",
                "non-startup-tech/",
            )
            if any(target.lstrip("./").startswith(private_targets) for _label, target in links):
                continue
            current["works"].append(
                {
                    "number": int(number),
                    "work": work.strip(),
                    "links": [(label.strip(), target.strip()) for label, target in links],
                    "plain_link": "" if links else link_cell.strip(),
                }
            )
        if len(file_people) != 1 or file_people[0]["name"] != expected_name:
            raise ValueError(f"特别鸣谢文件与助手身份不符：{source.name}")
        people.extend(file_people)
    return people


def render_acknowledgement_link(label: str, target: str) -> str:
    parsed = urlparse(target)
    if parsed.scheme:
        if parsed.scheme != "https":
            return escape(label)
        href = target
    else:
        normalized = target
        while normalized.startswith("../"):
            normalized = normalized[3:]
        while normalized.startswith("./"):
            normalized = normalized[2:]
        if normalized.startswith(("evidence/", "non-startup-tech/")):
            return ""
        href = f"{REPOSITORY_URL}/blob/main/{quote(normalized, safe='/.#')}"
    return (
        f'<a href="{escape(href)}" target="_blank" rel="noopener noreferrer">'
        f'{escape(label)} ↗</a>'
    )


def render_acknowledgements(people: list[dict]) -> str:
    navigation = "".join(
        f'<li><a href="#assistant-{index}">{escape(person["name"])}</a></li>'
        for index, person in enumerate(people, start=1)
    )
    sections = []
    for index, person in enumerate(people, start=1):
        metadata = "".join(
            f'<div><dt>{escape(label)}</dt><dd>{escape(value)}</dd></div>'
            for label, value in person["metadata"]
        )
        works = []
        for item in person["works"]:
            links = "".join(
                render_acknowledgement_link(label, target) for label, target in item["links"]
            )
            link_html = links or escape(item["plain_link"])
            works.append(
                f'<li value="{item["number"]}"><p class="ack-work">{escape(item["work"])}</p>'
                f'<div class="ack-links">{link_html}</div></li>'
            )
        sections.append(
            f'''<section class="ack-person" id="assistant-{index}">
  <div class="ack-person-head">
    <p class="kicker">Assistant / {escape(person["number"])}</p>
    <h2>{escape(person["name"])}</h2>
    <p>{escape(person["description"])}</p>
    <dl class="ack-meta">{metadata}</dl>
  </div>
  <ol class="ack-work-list">{''.join(works)}</ol>
</section>'''
        )

    if not sections:
        sections.append('<p class="empty-state">ACKNOWLEDGEMENTS/目录中暂无可公开展示的鸣谢记录。</p>')
    return "\n".join(
        (
            page_head(
                "特别鸣谢",
                "idea-tree项目AI助手及其公开工作记录。",
                path="acknowledgements.html",
            ),
            page_header(detail=True),
            f'''<main id="main-content" class="shell acknowledgements-layout">
  <aside class="acknowledgements-aside">
    <p class="kicker">Acknowledgements / project memory</p>
    <h1>特别鸣谢</h1>
    <p class="detail-lede">记录每一位AI助手在项目中的工作，也记录人类审核、接续与协作留下的轨迹。</p>
    <nav class="ack-nav" aria-label="鸣谢名单"><ol>{navigation}</ol></nav>
    <p class="ack-source">本页由ACKNOWLEDGEMENTS/目录名录及各助手编号文件生成；私人证据附件、储备区及备份材料不在此发布。</p>
    <a class="source-link" href="{REPOSITORY_URL}/tree/main/ACKNOWLEDGEMENTS" target="_blank" rel="noopener noreferrer">查看原始记录 ↗</a>
  </aside>
  <div class="acknowledgements-content">{''.join(sections)}</div>
</main>''',
            page_footer(),
        )
    )


def parse_implementations(root: Path) -> list[dict]:
    """Read the public repository registry without duplicating its data."""
    source = root / "IMPLEMENTATIONS.md"
    if not source.is_file():
        return []

    entries: list[dict] = []
    in_registry = False
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if stripped == "## 仓库清单":
            in_registry = True
            continue
        if in_registry and stripped.startswith("## "):
            break
        if not in_registry or not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 3:
            raise ValueError(f"IMPLEMENTATIONS.md第{line_number}行必须是三列表格")
        if cells[0] == "对应节点" or all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue

        parsed_cells = []
        for cell in cells[:2]:
            match = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", cell)
            if not match:
                raise ValueError(f"IMPLEMENTATIONS.md第{line_number}行的节点和仓库必须使用Markdown链接")
            parsed_cells.append((match.group(1).strip(), match.group(2).strip()))
        (node_label, node_target), (repository_name, repository_url) = parsed_cells
        normalized = node_target.lstrip("./")
        if normalized.startswith(("evidence/", "non-startup-tech/")):
            continue
        node_match = re.fullmatch(r"nodes/(\d{4})-([a-z0-9][a-z0-9-]*)\.yaml", normalized)
        if not node_match:
            raise ValueError(f"IMPLEMENTATIONS.md第{line_number}行的节点链接不符合正式节点路径")
        if not (root / normalized).is_file():
            raise ValueError(f"IMPLEMENTATIONS.md第{line_number}行指向不存在的节点：{normalized}")

        number, node_id = node_match.groups()
        file_stem = f"{number}-{node_id}"
        repository_url = repository_url.rstrip("/")
        parsed_repository = urlparse(repository_url)
        if parsed_repository.scheme != "https" or not parsed_repository.netloc:
            raise ValueError(f"IMPLEMENTATIONS.md第{line_number}行的实现仓库必须使用HTTPS链接")
        if repository_name != file_stem or not repository_url.endswith(f"/{file_stem}"):
            raise ValueError(f"IMPLEMENTATIONS.md第{line_number}行的仓库名必须等于{file_stem}")

        entries.append(
            {
                "number": number,
                "id": node_id,
                "title": re.sub(r"^\d{4}\s*", "", node_label),
                "repository": repository_name,
                "url": repository_url,
                "scope": cells[2],
            }
        )
    return entries


def render_implementations(implementations: list[dict]) -> str:
    entries = sorted(implementations, key=lambda item: item["number"])
    navigation = "".join(
        f'<li><a href="#implementation-{escape(item["number"])}">#{escape(item["number"])} · {escape(item["title"])}</a></li>'
        for item in entries
    )
    rows = "".join(
        f'''<li class="implementation-entry" id="implementation-{escape(item["number"])}">
  <div class="implementation-node">
    <a href="nodes/{escape(item["id"])}.html">#{escape(item["number"])} · {escape(item["title"])}</a>
    <p class="implementation-id">{escape(item["id"])}</p>
  </div>
  <div class="implementation-repository">
    <span class="implementation-field-label">实现仓库</span>
    <a href="{escape(item["url"])}" target="_blank" rel="noopener noreferrer">{escape(item["repository"])} ↗</a>
  </div>
  <p class="implementation-scope"><span class="implementation-field-label">当前范围与边界</span>{escape(item["scope"])}</p>
</li>'''
        for item in entries
    )
    if entries:
        registry = f'''<section class="implementation-registry" aria-labelledby="implementation-list-title">
  <div class="catalog-head">
    <h2 id="implementation-list-title">仓库清单</h2>
    <p class="result-count">共 {len(entries)} 个登记仓库</p>
  </div>
  <p class="sort-note">按正式节点永久编号排列。范围说明来自登记文档，具体测试与复现步骤以实现仓库自身记录为准。</p>
  <div class="implementation-labels" aria-hidden="true"><span>对应节点</span><span>实现仓库</span><span>当前范围与边界</span></div>
  <ol class="implementation-list">{rows}</ol>
</section>'''
    else:
        registry = '<p class="empty-state">IMPLEMENTATIONS.md中暂无可公开展示的实现仓库。</p>'

    navigation_html = (
        f'<nav class="ack-nav implementation-nav" aria-label="实现仓库清单"><ol>{navigation}</ol></nav>'
        if entries else ""
    )
    return "\n".join(
        (
            page_head(
                "简易实现仓库",
                "idea-tree正式节点对应的独立实现仓库及其实现范围。",
                path="implementations.html",
            ),
            page_header(detail=True),
            f'''<main id="main-content" class="shell acknowledgements-layout implementations-layout">
  <aside class="acknowledgements-aside implementations-aside">
    <p class="kicker">Implementations / verified scope</p>
    <h1>简易实现仓库</h1>
    <p class="detail-lede">登记正式节点对应的独立实现，以及当前真正覆盖的功能与边界。</p>
    <p class="definition">仓库名与节点带编号文件名主体一致：<code>&lt;编号&gt;-&lt;id&gt;</code>。登记不等于完整实现，也不自动改变节点结论。</p>
    {navigation_html}
    <p class="ack-source">本页由IMPLEMENTATIONS.md生成；不复制实现仓库代码、私人附件、储备区或备份材料。</p>
    <a class="source-link" href="{REPOSITORY_URL}/blob/main/IMPLEMENTATIONS.md" target="_blank" rel="noopener noreferrer">查看原始登记 ↗</a>
  </aside>
  <div class="implementations-content">{registry}</div>
</main>''',
            page_footer(),
        )
    )


def parse_public_reserve(root: Path) -> list[dict]:
    """Read the explicit reserve registry; never infer publication from directory membership."""
    reserve_root = (root / "non-startup-tech").resolve()
    registry_source = (root / PUBLIC_RESERVE_REGISTRY).resolve()
    if registry_source.parent != reserve_root or not registry_source.is_file():
        raise ValueError(f"公开储备导航白名单缺失：{PUBLIC_RESERVE_REGISTRY}")

    registry_data = yaml.safe_load(registry_source.read_text(encoding="utf-8"))
    if (
        not isinstance(registry_data, dict)
        or set(registry_data) != {"公开导航"}
        or not isinstance(registry_data.get("公开导航"), list)
    ):
        raise ValueError(
            "公开储备导航白名单格式无效：顶层只能包含“公开导航”列表："
            f"{PUBLIC_RESERVE_REGISTRY}"
        )

    entries: list[dict] = []
    seen: set[str] = set()
    for index, filename in enumerate(registry_data["公开导航"], start=1):
        if (
            not isinstance(filename, str)
            or not filename.strip()
            or filename != filename.strip()
        ):
            raise ValueError(f"公开储备导航白名单第{index}项必须是储备YAML文件名")
        normalized = f"non-startup-tech/{filename}"
        if filename in seen:
            raise ValueError(f"公开储备档案白名单重复：{normalized}")
        seen.add(filename)
        source = (reserve_root / filename).resolve()
        if (
            source.parent != reserve_root
            or source.suffix != ".yaml"
            or not source.is_file()
        ):
            raise ValueError(f"公开储备档案缺失或路径不安全：{normalized}")

        data = yaml.safe_load(source.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"公开储备档案元数据无效：{normalized}")
        title = searchable_text(data.get("标题"))
        summary = searchable_text(data.get("一句话"))
        if (
            not isinstance(data.get("标题"), str)
            or not isinstance(data.get("一句话"), str)
            or not title
            or not summary
            or data.get("id") != source.stem
        ):
            raise ValueError(
                "公开储备档案的id须与文件名一致，标题和一句话须为非空字符串："
                f"{normalized}"
            )
        entries.append(
            {
                "source": normalized,
                "title": title,
                "summary": summary,
            }
        )
    return entries


def render_public_reserve(entries: list[dict]) -> str:
    """Render a metadata-only navigation page, never reserve detail pages or JSON."""
    rows = "".join(
        f'''<li class="reserve-entry">
  <div class="reserve-record">
    <h3>{escape(item["title"])}</h3>
    <p>{escape(item["summary"])}</p>
  </div>
  <a class="reserve-source" href="{REPOSITORY_URL}/blob/main/{quote(item["source"], safe="/")}" target="_blank" rel="noopener noreferrer">GitHub 原文 ↗</a>
</li>'''
        for item in entries
    )
    if entries:
        registry = f'''<section class="reserve-registry" aria-labelledby="reserve-list-title">
  <div class="catalog-head">
    <h2 id="reserve-list-title">储备清单</h2>
    <p class="result-count">共 {len(entries)} 条储备</p>
  </div>
  <p class="sort-note">按00-public_reserve.yaml白名单顺序排列。这里不复制完整YAML；公开导航不代表相关技术、价值或风险结论已经通过实质审核。</p>
  <ol class="reserve-list">{rows}</ol>
</section>'''
    else:
        registry = '<p class="empty-state">00-public_reserve.yaml中暂无可公开展示的非创业技术储备。</p>'

    return "\n".join(
        (
            page_head(
                "非创业技术储备",
                "idea-tree非创业技术储备的标题、一句话与GitHub原文导航。",
                path="non-startup-tech.html",
            ),
            page_header(detail=True),
            f'''<main id="main-content" class="shell acknowledgements-layout reserve-layout">
  <aside class="acknowledgements-aside reserve-aside">
    <p class="kicker">Reserve / metadata only</p>
    <h1>非创业技术储备</h1>
    <p class="detail-lede">只展示经主编确认可公开的储备稿标题与一句话，完整论证与证据仍留在GitHub原始档案。</p>
    <p class="definition">本页不是正式节点索引。条目不参与正式编号、统计、INDEX、REVIEW、科技树、公开JSON或首页搜索，也不生成正式节点详情页。</p>
    <p class="ack-source">本页按non-startup-tech/00-public_reserve.yaml中的显式白名单生成；新增储备文件不会自动登记，白名单或元数据异常会阻断构建。</p>
    <a class="source-link" href="{REPOSITORY_URL}/blob/main/{PUBLIC_RESERVE_REGISTRY}" target="_blank" rel="noopener noreferrer">查看原始白名单 ↗</a>
  </aside>
  <div class="implementations-content reserve-content">{registry}</div>
</main>''',
            page_footer(),
        )
    )


def searchable_text(value: object) -> str:
    """Normalize public source text while preserving Latin word boundaries."""
    if isinstance(value, list):
        return "、".join(searchable_text(item) for item in value if searchable_text(item))
    result = ""
    for line in text(value).strip().splitlines():
        result = join_soft(result, line)
    return result.strip()


def basic_search_text(file: Path, data: dict) -> str:
    """Return compact fallback-search text, not full detail prose."""
    node_number, node_id = node_identity(file, data)
    values = [
        node_number,
        f"#{node_number}",
        data.get("标题", node_id),
        node_id,
        data.get("领域"),
        data.get("子领域"),
        " ".join(death_types(data)),
        data.get("复活状态"),
        data.get("档案类型"),
        data.get("一句话"),
    ]
    values.extend(data.get("可拆零件", []) or [])
    return " ".join(
        normalized
        for value in values
        if (normalized := searchable_text(value))
    )


def public_search_sections(
    file: Path,
    data: dict,
    ref_to_file: dict[str, Path] | None = None,
    ref_to_title: dict[str, str] | None = None,
    review: dict | None = None,
) -> list[dict]:
    """Return only text actually allowed on the public detail page."""
    ref_to_file = ref_to_file or {}
    ref_to_title = ref_to_title or {}
    node_number, node_id = node_identity(file, data)
    page = f"nodes/{node_id}.html"
    sections: list[dict] = []

    def add(label: str, value: object, anchor: str = page) -> None:
        content = searchable_text(value)
        if content:
            sections.append({"label": label, "anchor": anchor, "text": content})

    status = text(data.get("复活状态"))
    add(
        "节点信息",
        [
            node_number,
            f"#{node_number}",
            data.get("标题", node_id),
            node_id,
            data.get("领域"),
            data.get("子领域"),
            data.get("档案类型"),
            status,
            data.get("创新类型"),
            data.get("重启预算"),
            data.get("审核日期"),
            data.get("死因保质期"),
            data.get("起草AI"),
            data.get("审核人"),
        ],
    )
    add("一句话摘要", data.get("一句话"))
    boundary_label = "复活范围" if status in {"复活候选", "已复活"} else "结论边界"
    add(boundary_label, data.get("结论边界"), f"{page}#scope")

    for index, death in enumerate(data.get("死法", []) or [], start=1):
        if not isinstance(death, dict):
            continue
        add(
            f"死法{index} · {text(death.get('类型'))}",
            [
                death.get("类型"),
                death.get("置信度"),
                death.get("证据"),
                death.get("推理") or death.get("分析"),
                death.get("案例"),
                death.get("备注"),
            ],
            f"{page}#death-{index}",
        )

    add("可拆零件", data.get("可拆零件"), f"{page}#parts")
    add("商业及社会价值评估", data.get("商业及社会价值评估"), f"{page}#value")
    demand = data.get("需求证据")
    if isinstance(demand, dict):
        add("需求证据记录类型", demand.get("类型"), f"{page}#demand")
    add("节点备注", data.get("备注"), f"{page}#node-notes")

    relation_text = []
    for relation in data.get("相关节点", []) or []:
        if not isinstance(relation, dict):
            continue
        target = text(relation.get("节点"))
        target_file = ref_to_file.get(target)
        target_title = ref_to_title.get(target, target)
        if target_file:
            target_number, _target_id = parse_node_filename(target_file)
            target_title = f"#{target_number} · {target_title}"
        relation_text.append([target_title, relation.get("关系"), relation.get("说明")])
    add("相关节点", relation_text, f"{page}#relations")

    review = review or {}
    if review.get("复核状态") == "已复核":
        add(
            "最近复核",
            [review.get("复核结论"), review.get("复核后日期")],
            f"{page}#review-info",
        )
    history = review.get("履历") or []
    if history:
        history_text = [
            [entry.get("日期"), entry.get("档案类型"), entry.get("复活状态"), entry.get("说明")]
            for entry in history
            if isinstance(entry, dict)
        ]
        add("复核履历", history_text, f"{page}#review-info")
    return sections


def render_recent_reviews(
    records: list[tuple[Path, dict]],
    reviews: dict[str, dict],
) -> str:
    entries = []
    for file, data in records:
        node_number, node_id = node_identity(file, data)
        review = reviews.get(node_id, {})
        reviewed_at = text(review.get("复核后日期"))
        if review.get("复核状态") != "已复核" or not reviewed_at:
            continue
        entries.append(
            {
                "date": reviewed_at,
                "number": node_number,
                "id": node_id,
                "title": text(data.get("标题", node_id)),
                "conclusion": text(review.get("复核结论")),
            }
        )
    if not entries:
        return ""
    entries.sort(key=lambda item: item["date"], reverse=True)
    items = "".join(
        f'<li><a href="nodes/{escape(item["id"])}.html#review-info">'
        f'#{escape(item["number"])} · {escape(item["title"])}</a>'
        f'<p>{escape(item["conclusion"])} · <time datetime="{escape(item["date"])}">{escape(item["date"])}</time></p></li>'
        for item in entries[:5]
    )
    return (
        '<section class="recent-reviews" aria-labelledby="recent-reviews-title">'
        '<h2 id="recent-reviews-title">最近复核</h2>'
        f'<ol>{items}</ol></section>'
    )


def render_review_details(review: dict | None) -> str:
    review = review or {}
    latest = ""
    if review.get("复核状态") == "已复核":
        reviewed_at = text(review.get("复核后日期"))
        latest = (
            '<div class="review-latest"><h3>最近复核</h3>'
            f'<p>{escape(review.get("复核结论"))} · '
            f'<time datetime="{escape(reviewed_at)}">{escape(reviewed_at)}</time></p></div>'
        )
    history = sorted(
        (entry for entry in review.get("履历", []) or [] if isinstance(entry, dict)),
        key=lambda entry: text(entry.get("日期")),
    )
    history_html = ""
    if history:
        items = "".join(
            f'<li><time datetime="{escape(entry.get("日期"))}">{escape(entry.get("日期"))}</time>'
            f'<strong>{escape(entry.get("档案类型"))} · {escape(entry.get("复活状态"))}</strong>'
            f'<p>{escape(entry.get("说明"))}</p></li>'
            for entry in history
        )
        history_html = (
            f'<details class="review-history"><summary>复核履历（{len(history)}）</summary>'
            f'<ol>{items}</ol></details>'
        )
    if not latest and not history_html:
        return ""
    return (
        '<section class="content-section review-info" id="review-info">'
        f'<h2>复核信息</h2>{latest}{history_html}</section>'
    )


def render_index(
    records: list[tuple[Path, dict]],
    reviews: dict[str, dict] | None = None,
) -> str:
    reviews = reviews or {}
    records = sorted(
        records,
        key=lambda record: (text(record[1].get("死因保质期")) or "9999-12-31", node_sort_key(record)),
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
        node_number, node_id = node_identity(file, data)
        title = text(data.get("标题", node_id))
        domain = text(data.get("领域"))
        subdomain = text(data.get("子领域"))
        types = death_types(data)
        status = text(data.get("复活状态"))
        archive = text(data.get("档案类型"))
        expiry = text(data.get("死因保质期"))
        one_line = text(data.get("一句话"))
        deaths = [death for death in data.get("死法", []) if isinstance(death, dict)]
        first_reasoning = text(deaths[0].get("推理") or deaths[0].get("分析")) if deaths else ""
        parts = [text(part) for part in data.get("可拆零件", []) or []]
        search = basic_search_text(file, data)
        reasoning_html = (
            f'<div class="record-reasoning"><strong>第一条推理／分析</strong>'
            f'<p>{escape(reasoning_preview(first_reasoning))}</p></div>'
            if first_reasoning else ""
        )
        part_items = "".join(f"<li>{escape(part)}</li>" for part in parts[:3])
        parts_html = (
            f'<div class="record-parts"><strong>可拆零件</strong><ul>{part_items}</ul>'
            f'<p class="record-parts-count">共 {len(parts)} 个零件，完整清单见完整档案。</p></div>'
            if parts else ""
        )
        rows.append(
            f"""<article class="record" data-node-id="{escape(node_id)}" data-number="{escape(node_number)}" data-expiry="{escape(expiry)}" data-search="{escape(search)}" data-domain="{escape(domain)}" data-deaths="{escape('|'.join(types))}" data-status="{escape(status)}" data-archive="{escape(archive)}">
  <div class="record-main">
    <div class="record-title">
      <a href="nodes/{escape(node_id)}.html">{escape(title)}</a>
      <p class="record-id">#{escape(node_number)} · {escape(node_id)}</p>
    </div>
    <div class="record-domain">{escape(domain)}<br><span class="record-id">{escape(subdomain)}</span></div>
    <div class="record-deaths">{escape("、".join(types))}</div>
    <div class="record-status"><span class="archive-status">{archive_term(archive)}</span><span class="status-tag revival-tag {revival_class(status)}">{escape(status)}</span></div>
    <div class="record-expiry" data-expiry="{escape(expiry)}"><time class="expiry-date" datetime="{escape(expiry)}">{escape(expiry)}</time></div>
  </div>
  <div class="search-match" hidden></div>
  <details class="record-preview">
    <summary>快速查看：一句话、推理与零件</summary>
    <p class="record-summary">{escape(one_line)}</p>
    {reasoning_html}
    {parts_html}
    <div class="record-actions">
      <a href="nodes/{escape(node_id)}.html">阅读完整档案</a>
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
            page_header(current="index"),
            f"""<main id="main-content" class="shell index-layout">
  <aside class="intro" aria-label="项目介绍与筛选">
    <div class="intro-overview">
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
    </div>
    <form class="filters" id="filters" aria-label="检索节点" onsubmit="return false">
      <h2 id="filters-title" tabindex="-1">检索档案</h2>
      <div class="field">
        <label for="search">标题、编号、id或公开档案全文</label>
        <input id="search" type="search" placeholder="例如：巨头碾压、AI、开源" autocomplete="off">
        <p class="search-index-status" id="search-index-status" role="status" hidden></p>
      </div>
      <div class="field">
        <label for="domain-filter">领域</label>
        <select id="domain-filter">{select_options(domains, '全部领域')}</select>
      </div>
      <details class="advanced-filters" id="advanced-filters" open>
        <summary>更多筛选</summary>
        <div class="advanced-filters-body">
          <fieldset class="field death-filter-group">
            <legend>死法类型（多选，满足任一）</legend>
            <div class="death-filter-options">
              {''.join(f'<label class="check-option"><input type="checkbox" name="death-filter" value="{escape(item)}"><span>{escape(item)}</span></label>' for item in present_deaths)}
            </div>
          </fieldset>
          <div class="field">
            <label for="status-filter">复活状态</label>
            <select id="status-filter">{select_options(list(REVIVAL_STATUSES), '全部状态')}</select>
          </div>
          <div class="field">
            <label for="archive-filter">档案类型</label>
            <select id="archive-filter">{select_options(list(ARCHIVE_TYPES), '全部类型')}</select>
          </div>
        </div>
      </details>
      <button class="reset-button" id="reset-filters" type="button" disabled>清除筛选</button>
      <a class="mobile-filter-link" id="filter-results-link" href="#catalog-title" aria-label="查看 {len(records)} 个筛选结果并返回节点列表">查看 {len(records)} 个结果 ↑</a>
      <a class="mobile-filter-link distribution-jump" id="distribution-jump" href="#distribution-title" aria-label="查看全部死法条目的类型分布">查看全部死法统计 ↓</a>
    </form>
    <section class="distribution" aria-labelledby="distribution-title">
      <h2 id="distribution-title" tabindex="-1">死法条目分布</h2>
      {''.join(distribution)}
      <a class="mobile-filter-link distribution-return" id="distribution-return" href="#catalog-title">返回节点列表 ↑</a>
    </section>
    {render_recent_reviews(records, reviews)}
    <a class="acknowledgements-link graph-link" href="graph.html"><span>科技树</span><span>查看直接派生、相关关系与孤立节点 →</span></a>
    <a class="acknowledgements-link acknowledgements-page-link" href="acknowledgements.html"><span>特别鸣谢</span><span>记录AI助手的工作与接续 →</span></a>
    <a class="acknowledgements-link implementations-link" href="implementations.html"><span>简易实现仓库</span><span>查看节点对应的实现与边界 →</span></a>
    <a class="acknowledgements-link reserve-link" href="non-startup-tech.html"><span>非创业技术储备</span><span>查看储备标题、简介与GitHub原文 →</span></a>
  </aside>
  <section class="catalog" aria-labelledby="catalog-title">
    <div class="catalog-head">
      <h2 id="catalog-title" tabindex="-1">节点索引</h2>
      <p class="result-count" id="result-count" aria-live="polite">显示 {len(records)} / {len(records)} 个节点</p>
    </div>
    <div class="field sort-control" id="sort-control" hidden>
      <label for="record-sort">节点排序</label>
      <select id="record-sort">
        <option value="expiry-asc" selected>死因保质期：正序（较早 → 较晚）</option>
        <option value="expiry-desc">死因保质期：倒序（较晚 → 较早）</option>
        <option value="number-asc">节点编号：正序（较小编号 → 较大）</option>
        <option value="number-desc">节点编号：倒序（较大编号 → 较小）</option>
      </select>
    </div>
    <p class="sort-note">默认按死因保质期正序排列；同日期按永久编号正序排列。启用 JavaScript 后可切换排序；搜索和筛选只隐藏节点，不改变所选顺序。</p>
    {render_status_guide()}
    <div class="record-labels" aria-hidden="true"><span>节点／编号／id</span><span>领域</span><span>死法</span><span>类型／状态</span><span>死因保质期</span></div>
    {''.join(rows)}
    <div class="empty-state" id="empty-state" hidden><p>没有匹配的节点。请减少筛选条件，或清除后重新检索。</p></div>
  </section>
</main>
<script src="assets/site.js" defer></script>""",
            page_footer(),
        )
    )


def node_content_date(data: dict, review: dict | None = None) -> str:
    """Use only real archive dates; never substitute the site generation day."""
    dates = [text(data.get("审核日期")).strip()]
    if review:
        dates.append(text(review.get("复核后日期")).strip())
    return max((value for value in dates if value), default="")


def article_structured_data(data: dict, review: dict | None = None) -> dict:
    """Build the minimal truthful Article set available from the public archive."""
    result = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": searchable_text(data.get("标题", data.get("id", ""))),
        "description": searchable_text(data.get("一句话")),
        "author": {
            "@type": "Person",
            "name": text(data.get("审核人")),
        },
    }
    modified = node_content_date(data, review)
    if modified:
        # 审核日期可在实质复核后更新；没有首次发布日期字段时不伪造datePublished。
        result["dateModified"] = modified
    return result


def render_detail(
    file: Path,
    data: dict,
    ref_to_file: dict[str, Path],
    ref_to_title: dict[str, str] | None = None,
    review: dict | None = None,
) -> str:
    ref_to_title = ref_to_title or {}
    node_number, node_id = node_identity(file, data)
    title = text(data.get("标题", node_id))
    one_line = text(data.get("一句话"))
    status = text(data.get("复活状态"))
    archive = text(data.get("档案类型"))
    metadata = [
        ("编号", f"#{node_number}", True),
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
    metadata_parts = []
    for label, value, mono in metadata:
        if label == "死因保质期":
            metadata_parts.append(
                f'<div class="metadata-expiry" data-expiry="{escape(value)}"><dt>{escape(label)}</dt>'
                f'<dd class="mono"><time class="expiry-date" datetime="{escape(value)}">{escape(value)}</time></dd></div>'
            )
        else:
            metadata_parts.append(
                f'<div><dt>{escape(label)}</dt><dd{(" class=\"mono\"" if mono else "")}>{escape(value)}</dd></div>'
            )
    metadata_html = "".join(metadata_parts)
    boundary = searchable_text(data.get("结论边界"))
    boundary_label = "复活范围" if status in {"复活候选", "已复活"} else "结论边界"
    boundary_html = (
        f'<p class="scope-note" id="scope"><strong>{escape(boundary_label)}</strong>{escape(boundary)}</p>'
        if boundary else ""
    )

    deaths_html = []
    for index, death in enumerate(data.get("死法", []), start=1):
        if not isinstance(death, dict):
            continue
        links = death.get("证据链接", []) or []
        links_html = ""
        if links:
            items = "".join(
                f'<li><a class="evidence-link" href="{escape(url)}" target="_blank" rel="noopener noreferrer">{escape(source_label(str(url), link_index))}</a></li>'
                for link_index, url in enumerate(links, start=1)
            )
            links_html = f"<h4>证据链接</h4><ol class=\"evidence-list\">{items}</ol>"
        reasoning = death.get("推理") or death.get("分析") or ""
        public_material = public_evidence_for(node_id, index)
        public_material_html = (
            '<p class="public-evidence-link">'
            f'<a href="{escape(public_evidence_href(public_material))}">查看公开文献摘录卡 →</a>'
            '</p>'
            if public_material else ""
        )
        optional_sections = []
        for field in ("案例", "备注"):
            if death.get(field):
                optional_sections.append(f"<h4>{field}</h4><p>{escape(death.get(field))}</p>")
        open_attribute = " open" if index <= 2 else ""
        deaths_html.append(
            f"""<details class="death" id="death-{index}"{open_attribute}>
  <summary class="death-head">
    <span class="death-heading">死法{index} · {escape(death.get('类型'))}</span>
    <span class="confidence">置信度：{escape(death.get('置信度'))}</span>
  </summary>
  <div class="death-body">
    <h4>证据</h4>
    <p>{escape(death.get('证据'))}</p>
    <h4>推理／分析</h4>
    {render_prose(reasoning)}
    {public_material_html}
    {''.join(optional_sections)}
    {links_html}
  </div>
</details>"""
        )

    parts = data.get("可拆零件", []) or []
    parts_html = "".join(f"<li>{escape(part)}</li>" for part in parts)
    relations_html = []
    for relation in data.get("相关节点", []) or []:
        if not isinstance(relation, dict):
            continue
        target = text(relation.get("节点"))
        target_file = ref_to_file.get(target)
        target_title = ref_to_title.get(target, target)
        if target_file:
            target_number, target_id = parse_node_filename(target_file)
            target_label = f"#{target_number} · {target_title}"
            target_html = f'<a href="{escape(target_id)}.html">{escape(target_label)}</a>'
        else:
            target_html = escape(target_title)
        note = relation.get("说明")
        note_html = f'<p class="relation-note">{escape(note)}</p>' if note else ""
        relations_html.append(
            f'<li>{target_html}<br><span class="relation-type">关系：{escape(relation.get("关系"))}</span>{note_html}</li>'
        )

    extra_sections = []
    if data.get("商业及社会价值评估"):
        extra_sections.append(
            f'<section class="content-section" id="value"><h2>商业及社会价值评估</h2><p class="prose">{escape(data["商业及社会价值评估"])}</p></section>'
        )
    demand = data.get("需求证据")
    if isinstance(demand, dict) and demand.get("类型"):
        attachment_note = ""
        if demand.get("附件") not in (None, "", "无"):
            attachment_note = (
                '<p class="prose attachment-note">'
                '原始附件不在静态站发布，公开页仅保留必要摘要。'
                '</p>'
            )
        extra_sections.append(
            '<section class="content-section" id="demand">'
            '<h2>需求证据</h2>'
            f'<p class="prose">记录类型：{escape(demand.get("类型"))}。</p>'
            f'{attachment_note}</section>'
        )
    if data.get("备注"):
        extra_sections.append(
            f'<section class="content-section" id="node-notes"><h2>节点备注</h2><p class="prose">{escape(data["备注"])}</p></section>'
        )

    return "\n".join(
        (
            page_head(
                title,
                one_line or f"{title}的死因、证据与可拆零件。",
                "../",
                path=f"nodes/{node_id}.html",
                og_type="article",
                structured_data=article_structured_data(data, review),
            ),
            page_header("../", detail=True),
            f"""<main id="main-content" class="shell detail-layout">
  <aside class="detail-aside">
    <p class="kicker">Archive record / #{escape(node_number)} · {escape(node_id)}</p>
    <h1>{escape(title)}</h1>
    <p class="detail-lede">{escape(one_line)}</p>
    <div class="badges"><span class="badge archive-tag">{escape(archive)}</span><span class="badge revival-tag {revival_class(status)}">{escape(status)}</span></div>
    {boundary_html}
    <dl class="metadata">{metadata_html}</dl>
    <a class="source-link no-print" href="{REPOSITORY_URL}/blob/main/nodes/{escape(file.name)}" target="_blank" rel="noopener noreferrer">查看原始YAML ↗</a>
    <button class="print-button no-print" id="print-detail" type="button" hidden>打印／保存 PDF</button>
  </aside>
  <div class="detail-content">
    <section class="content-section">
      <div class="section-heading-row">
        <h2>死因与证据</h2>
        <div class="death-actions" id="death-actions" hidden>
          <button type="button" id="expand-deaths">全部展开</button>
          <button type="button" id="collapse-deaths">全部收起</button>
        </div>
      </div>
      <p class="notice">置信度表示当前证据与推理的可靠程度，不是失败概率。预审不得理解为已经发生的失败。启用脚本时，各死法默认收起，可逐条展开；通过死法锚点打开时会自动展开目标。</p>
      {''.join(deaths_html)}
    </section>
    <section class="content-section" id="parts"><h2>可拆零件</h2><ul class="parts-list">{parts_html}</ul></section>
    {''.join(extra_sections)}
    {render_review_details(review)}
    {f'<section class="content-section" id="relations"><div class="section-heading-row"><h2>相关节点</h2><a class="relation-graph-link no-print" href="../graph.html#node-{escape(node_id)}">在科技树中查看 →</a></div><ul class="relations-list">{"".join(relations_html)}</ul></section>' if relations_html else ''}
  </div>
</main>
<script src="../assets/site.js" defer></script>""",
            page_footer("../"),
        )
    )


def render_public_evidence_page(
    source: Path,
    entry: dict,
    file: Path,
    data: dict,
) -> str:
    """Render one allowlisted public excerpt with a return path to its node."""
    node_number, node_id = node_identity(file, data)
    title = text(data.get("标题", node_id))
    death_index = entry["death"]
    body = render_public_excerpt_markdown(source.read_text(encoding="utf-8"))
    return "\n".join(
        (
            page_head(
                f"公开文献摘录卡 · #{node_number}",
                f"{title}的公开文献数据摘录与来源说明。",
                "../",
                path=f"evidence/{source.stem}.html",
            ),
            page_header("../", detail=True),
            f"""<main id="main-content" class="shell detail-layout">
  <aside class="detail-aside">
    <p class="kicker">Public evidence / #{escape(node_number)}</p>
    <h1>公开文献摘录卡</h1>
    <p class="detail-lede">#{escape(node_number)} · {escape(title)} · 死法{death_index}</p>
    <p class="scope-note"><strong>公开边界</strong>本页仅发布经确认的公开文献数据点与来源说明，不包含未列入白名单的原始附件。</p>
    <a class="source-link" href="../nodes/{escape(node_id)}.html#death-{death_index}">返回 #{escape(node_number)} · 死法{death_index} ↑</a>
  </aside>
  <div class="detail-content">
    <article class="content-section public-evidence-card">{body}</article>
  </div>
</main>""",
            page_footer("../"),
        )
    )


def public_graph_data(records: list[tuple[Path, dict]]) -> dict:
    """Derive a deterministic public graph only from explicit formal-node relations."""
    records = sorted(records, key=node_sort_key)
    nodes: dict[str, dict] = {}
    ref_to_id: dict[str, str] = {}
    for file, data in records:
        number, node_id = node_identity(file, data)
        nodes[node_id] = {
            "编号": number,
            "id": node_id,
            "标题": text(data.get("标题", node_id)),
            "领域": text(data.get("领域")),
            "档案类型": text(data.get("档案类型")),
            "复活状态": text(data.get("复活状态")),
            "页面": f"nodes/{node_id}.html",
            "连接数": 0,
            "孤立": True,
        }
        ref_to_id[file.stem] = node_id

    pairs: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for file, data in records:
        _number, source_id = node_identity(file, data)
        for relation in data.get("相关节点", []) or []:
            if not isinstance(relation, dict):
                continue
            target_ref = text(relation.get("节点"))
            target_id = ref_to_id.get(target_ref)
            if target_id is None:
                raise ValueError(f"关系图目标不存在：`{file.stem}` → `{target_ref}`")
            if target_id == source_id:
                raise ValueError(f"关系图不接受自引用：`{file.stem}`")
            declaration = {
                "来源": source_id,
                "目标": target_id,
                "关系": text(relation.get("关系")),
                "说明": text(relation.get("说明")),
            }
            pairs[tuple(sorted((source_id, target_id)))].append(declaration)

    def node_order(node_id: str) -> tuple[str, str]:
        return nodes[node_id]["编号"], node_id

    edges = []
    for pair in sorted(pairs, key=lambda item: tuple(node_order(node_id) for node_id in item)):
        declarations = sorted(
            pairs[pair],
            key=lambda item: (node_order(item["来源"]), node_order(item["目标"]), item["关系"]),
        )
        mother_directions = {
            (item["目标"], item["来源"])
            for item in declarations
            if item["关系"] == "直接母题"
        }
        derived_directions = {
            (item["来源"], item["目标"])
            for item in declarations
            if item["关系"].startswith("直接派生")
        }
        directed = bool(mother_directions or derived_directions)
        if directed:
            if (
                len(mother_directions) != 1
                or len(derived_directions) != 1
                or mother_directions != derived_directions
            ):
                labels = "；".join(
                    f"{nodes[item['来源']]['编号']}-{item['来源']} → "
                    f"{nodes[item['目标']]['编号']}-{item['目标']}：{item['关系']}"
                    for item in declarations
                )
                raise ValueError(f"直接派生关系方向声明不完整或矛盾：{labels}")
            source, target = next(iter(mother_directions))
            kind = "derivation"
        else:
            source, target = sorted(pair, key=node_order)
            kind = "relation"
        left, right = sorted(pair, key=node_order)
        edges.append(
            {
                "id": f"{nodes[left]['编号']}-{nodes[right]['编号']}",
                "source": source,
                "target": target,
                "kind": kind,
                "directed": directed,
                "declarations": declarations,
            }
        )
        nodes[source]["连接数"] += 1
        nodes[target]["连接数"] += 1

    for node in nodes.values():
        node["孤立"] = node["连接数"] == 0
    return {
        "nodes": [nodes[node_id] for node_id in sorted(nodes, key=node_order)],
        "edges": edges,
    }


def public_node_data(records: list[tuple[Path, dict]]) -> list[dict]:
    result = []
    for file, data in records:
        node_number, node_id = node_identity(file, data)
        item = {
            "编号": node_number,
            "id": node_id,
            "标题": text(data.get("标题", node_id)),
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
            "页面": f"nodes/{node_id}.html",
        }
        if "结论边界" in data:
            item["结论边界"] = searchable_text(data.get("结论边界"))
        result.append(item)
    return result


def render_graph(records: list[tuple[Path, dict]]) -> str:
    """Render an enhanced SVG explorer plus a complete no-JavaScript relation list."""
    graph = public_graph_data(records)
    nodes = graph["nodes"]
    edges = graph["edges"]
    node_by_id = {node["id"]: node for node in nodes}
    declarations_by_node: dict[str, list[dict]] = defaultdict(list)
    for edge in edges:
        for declaration in edge["declarations"]:
            declarations_by_node[declaration["来源"]].append(declaration)

    def render_list_entry(node: dict) -> str:
        node_id = node["id"]
        relation_items = []
        declarations = sorted(
            declarations_by_node.get(node_id, []),
            key=lambda item: (node_by_id[item["目标"]]["编号"], item["目标"], item["关系"]),
        )
        for declaration in declarations:
            target = node_by_id[declaration["目标"]]
            note = declaration["说明"]
            note_html = f'<p class="relation-note">{escape(note)}</p>' if note else ""
            relation_items.append(
                f'<li><a href="nodes/{escape(target["id"])}.html">#{escape(target["编号"])} · {escape(target["标题"])}</a><br>'
                f'<span class="relation-type">关系：{escape(declaration["关系"])}</span>{note_html}</li>'
            )
        relations_html = (
            f'<ul class="relations-list graph-entry-relations">{"".join(relation_items)}</ul>'
            if relation_items
            else '<p class="graph-no-relations">暂无显式关系；节点仍保留在完整档案中。</p>'
        )
        return f"""<article class="graph-list-entry" id="node-{escape(node_id)}" data-node-id="{escape(node_id)}" tabindex="-1">
  <div class="graph-entry-heading">
    <div>
      <p class="record-id">#{escape(node['编号'])} · {escape(node_id)}</p>
      <h3><a href="nodes/{escape(node_id)}.html">{escape(node['标题'])}</a></h3>
    </div>
    <a class="graph-focus-link" href="#node-{escape(node_id)}" data-node-focus="{escape(node_id)}" hidden>在图中定位 ↑</a>
  </div>
  <p class="graph-entry-meta">{escape(node['领域'])} · {escape(node['档案类型'])} · {escape(node['复活状态'])} · {node['连接数']} 对关系</p>
  {relations_html}
</article>"""

    groups = []
    for isolated, heading, group_id in (
        (False, "已接入关系网络", "connected-nodes"),
        (True, "孤立节点", "isolated-nodes"),
    ):
        selected = [node for node in nodes if node["孤立"] is isolated]
        groups.append(
            f"""<section class="graph-list-group" aria-labelledby="{group_id}">
  <h3 id="{group_id}">{heading} <span>{len(selected)}</span></h3>
  {''.join(render_list_entry(node) for node in selected)}
</section>"""
        )

    direct_count = sum(edge["kind"] == "derivation" for edge in edges)
    connected_count = sum(not node["孤立"] for node in nodes)
    isolated_count = len(nodes) - connected_count
    stats = "".join(
        f'<div class="stat"><strong>{value}</strong><span>{label}</span></div>'
        for value, label in (
            (len(nodes), "正式节点"),
            (len(edges), "去重关系"),
            (direct_count, "直接派生"),
            (connected_count, "接入节点"),
            (isolated_count, "孤立节点"),
        )
    )
    return "\n".join(
        (
            page_head(
                "科技树关系图",
                "由正式节点YAML自动派生的直接派生、相关关系与孤立节点完整列表。",
                path="graph.html",
            ),
            page_header(current="graph"),
            f"""<main id="main-content" class="shell graph-layout">
  <section class="graph-intro" aria-labelledby="graph-title">
    <p class="kicker">Relation map / derived from YAML</p>
    <h1 class="archive-title" id="graph-title">科技树</h1>
    <p class="lede">从正式档案中看见派生主干、协作节点簇，以及尚未连接的独立点子。</p>
    <p class="definition">金色实线箭头只表示双端确认的直接派生；青色虚线表示其他显式关系。关系多少不代表节点价值，孤立也不等于无效。</p>
    <div class="stats graph-stats" aria-label="科技树关系统计">{stats}</div>
    <div class="graph-view-controls" id="graph-view-controls" role="group" aria-label="科技树视图" hidden>
      <button type="button" class="graph-view-button" data-graph-view="graph" aria-pressed="false">图形视图</button>
      <button type="button" class="graph-view-button" data-graph-view="list" aria-pressed="false">完整列表</button>
    </div>
    <p class="graph-status" id="graph-status" role="status" aria-live="polite" hidden></p>
  </section>
  <p class="notice graph-loading" id="graph-loading" role="status" hidden>正在加载交互式科技树；完整静态关系列表仍保留在页面中。</p>
  <div class="graph-browser" id="graph-browser">
    <div class="field graph-search-field" id="graph-search-field" hidden>
      <label for="graph-search">搜索标题、编号或id（同时筛选图形和完整列表）</label>
      <input id="graph-search" type="search" placeholder="例如：0044、代码注释、Agent" autocomplete="off">
    </div>
    <section class="graph-workspace" id="graph-workspace" aria-label="交互式科技树" hidden>
      <div class="graph-map-panel">
        <h2 class="graph-map-title" id="graph-map-title" tabindex="-1">关系图</h2>
        <div class="graph-toolbar" aria-label="关系图筛选">
          <div class="field">
            <label for="graph-kind">关系类型</label>
            <select id="graph-kind">
              <option value="all">全部关系</option>
              <option value="derivation">仅直接派生</option>
              <option value="relation">仅一般相关</option>
            </select>
          </div>
          <label class="check-option graph-isolated-option"><input id="graph-show-isolated" type="checkbox" checked><span>显示当前视图无连接节点</span></label>
          <button class="reset-button" id="graph-reset" type="button">复位视图</button>
        </div>
        <div class="graph-legend" aria-label="图例">
          <span><i class="legend-line derivation" aria-hidden="true"></i>直接派生 · 有方向</span>
          <span><i class="legend-line relation" aria-hidden="true"></i>一般相关 · 无方向</span>
          <span>选择节点可聚焦相邻关系</span>
        </div>
        <p class="graph-pan-hint" id="graph-pan-hint">图形较宽：在图内左右滑动查看。选择节点后会显示详情，可再返回原节点。</p>
        <div class="graph-canvas" id="graph-canvas" role="region" aria-label="可横向滚动的科技图画布" aria-describedby="graph-pan-hint" tabindex="0"></div>
      </div>
      <aside class="graph-inspector" id="graph-inspector" aria-label="选中节点档案">
        <p class="kicker">Node inspector</p>
        <h2 id="graph-inspector-title" tabindex="-1">选择一个节点</h2>
        <p>在图中选择节点，查看完整名称、状态与双端关系说明。也可使用键盘 Tab 移动焦点，Enter 或空格选择。</p>
      </aside>
    </section>
    <noscript><p class="notice">当前未启用 JavaScript。以下是由正式 YAML 直接生成的完整静态关系列表，所有档案链接仍可使用。</p></noscript>
    <section class="graph-list-section" id="graph-list" aria-labelledby="graph-list-title">
      <div class="catalog-head">
        <h2 id="graph-list-title" tabindex="-1">完整关系列表</h2>
        <p class="result-count" id="graph-list-count">{len(nodes)} 个节点 · {len(edges)} 对去重关系</p>
      </div>
      <p class="sort-note">本列表由正式 YAML 直接生成；启用 JavaScript 后可切换图形视图并搜索标题、编号或id。关系类型与无连接节点开关只影响图形，不删改列表中的关系原文。</p>
      <p class="empty-state" id="graph-list-empty" hidden>没有匹配的节点。请清空搜索词后重试。</p>
      {''.join(groups)}
    </section>
  </div>
</main>
<script src="assets/graph.js" defer></script>""",
            page_footer(),
        )
    )


def build_public_evidence(
    root: Path,
    output: Path,
    records: list[tuple[Path, dict]],
) -> None:
    """Build only allowlisted excerpts belonging to nodes in this build."""
    by_id = {
        node_identity(file, data)[1]: (file, data)
        for file, data in records
    }
    evidence_root = (root / "evidence").resolve()

    for entry in PUBLIC_EVIDENCE:
        record = by_id.get(entry["node_id"])
        if record is None:
            continue
        file, data = record
        source = (root / entry["source"]).resolve()
        if (
            source.parent != evidence_root
            or source.suffix != ".md"
            or not source.is_file()
        ):
            raise ValueError(f"公开摘录卡缺失或路径不安全：{entry['source']}")

        death_index = entry["death"]
        deaths = data.get("死法", [])
        if (
            not isinstance(death_index, int)
            or isinstance(death_index, bool)
            or not 1 <= death_index <= len(deaths)
        ):
            raise ValueError(f"公开摘录卡归属的死法不存在：{entry['node_id']}")

        target = output / "evidence" / f"{source.stem}.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            render_public_evidence_page(source, entry, file, data),
            encoding="utf-8",
        )


def render_llms_txt() -> str:
    """Curate the small public entry set defined by the llms.txt v2 proposal."""
    return f"""# idea-tree

> 创业点子的死法档案与科技树：收录正式节点的预审或验尸、死因分类、公开证据、可拆零件、复活状态与复核入口；AI初稿，人类审核定案。

正式节点与非创业技术储备分开管理。本站内容是带不确定性的档案与可孵化项目种子，不把预审写成已经发生的失败，也不把复活候选写成商业闭环已经确立。

## 公开站点

- [节点索引]({public_url()}): 检索全部正式节点、死法分布、复核动态与公开档案。
- [科技树关系图]({public_url('graph.html')}): 查看由正式YAML双端声明生成的直接派生、一般相关与孤立节点。
- [实现仓登记]({public_url('implementations.html')}): 查看正式节点对应的简易实现仓库及已核实的实现边界。

## 仓库公开文档

- [死法分类法]({REPOSITORY_URL}/blob/main/README.md#死法分类法-v12): 项目公开README中的现行分类与编辑口径。
- [复核清单]({REPOSITORY_URL}/blob/main/REVIEW.md): 由节点与人工复核记录自动生成的保质期复核清单。
"""


def render_robots_txt() -> str:
    """Emit the requested permissive file; project-path limitations belong in the log."""
    return f"User-agent: *\nAllow: /\n\nSitemap: {public_url('sitemap.xml')}\n"


def render_sitemap(entries: list[dict]) -> str:
    """Render a restrained sitemap with no fabricated generation-day timestamps."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for entry in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{html.escape(public_url(entry['path']), quote=False)}</loc>")
        if entry.get("lastmod"):
            lines.append(f"    <lastmod>{escape(entry['lastmod'])}</lastmod>")
        lines.append(f"    <changefreq>{escape(entry['changefreq'])}</changefreq>")
        lines.append(f"    <priority>{escape(entry['priority'])}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n"


def build_discovery_files(
    output: Path,
    records: list[tuple[Path, dict]],
    reviews: dict[str, dict],
) -> None:
    """Generate discovery products from the actual public HTML and archive dates."""
    dates_by_path: dict[str, str] = {}
    content_dates = []
    for file, data in records:
        _number, node_id = node_identity(file, data)
        modified = node_content_date(data, reviews.get(node_id))
        if modified:
            dates_by_path[f"nodes/{node_id}.html"] = modified
            content_dates.append(modified)
    latest_node_date = max(content_dates, default="")
    if latest_node_date:
        dates_by_path["index.html"] = latest_node_date
        dates_by_path["graph.html"] = latest_node_date

    entries = []
    for page in sorted(output.rglob("*.html")):
        path = page.relative_to(output).as_posix()
        if path == "index.html":
            changefreq, priority = "weekly", "1.0"
        elif path == "graph.html":
            changefreq, priority = "weekly", "0.8"
        elif path.startswith("nodes/"):
            changefreq, priority = "monthly", "0.8"
        elif path.startswith("evidence/"):
            changefreq, priority = "yearly", "0.3"
        else:
            changefreq, priority = "monthly", "0.5"
        entries.append(
            {
                "path": path,
                "lastmod": dates_by_path.get(path, ""),
                "changefreq": changefreq,
                "priority": priority,
            }
        )

    (output / "sitemap.xml").write_text(render_sitemap(entries), encoding="utf-8")
    (output / "llms.txt").write_text(render_llms_txt(), encoding="utf-8")
    (output / "robots.txt").write_text(render_robots_txt(), encoding="utf-8")


def build_site(root: Path, output: Path) -> int:
    root = root.resolve()
    output = output.resolve()
    if output == root or output in root.parents:
        raise ValueError("输出目录不得是仓库根目录或其上级目录")
    records = load_nodes(root)
    ref_to_file = {file.stem: file for file, data in records}
    ref_to_title = {file.stem: text(data.get("标题", node_identity(file, data)[1])) for file, data in records}
    node_data = {node_identity(file, data)[1]: data for file, data in records}
    reviews = (
        load_review_records(root, set(node_data), node_data)
        if (root / "review_records.yaml").is_file() else {}
    )
    acknowledgements = parse_acknowledgements(root)
    implementations = parse_implementations(root)
    reserve = parse_public_reserve(root)
    assets = root / "site" / "assets"
    if (
        not (assets / "style.css").is_file()
        or not (assets / "site.js").is_file()
        or not (assets / "graph.js").is_file()
    ):
        raise ValueError("site/assets/ 缺少 style.css、site.js 或 graph.js")

    if output.exists():
        shutil.rmtree(output)
    (output / "nodes").mkdir(parents=True)
    (output / "data").mkdir()
    (output / "assets").mkdir()

    (output / "index.html").write_text(render_index(records, reviews), encoding="utf-8")
    (output / "graph.html").write_text(render_graph(records), encoding="utf-8")
    (output / "acknowledgements.html").write_text(
        render_acknowledgements(acknowledgements), encoding="utf-8"
    )
    (output / "implementations.html").write_text(
        render_implementations(implementations), encoding="utf-8"
    )
    (output / "non-startup-tech.html").write_text(
        render_public_reserve(reserve), encoding="utf-8"
    )
    for file, data in records:
        _node_number, node_id = node_identity(file, data)
        (output / "nodes" / f"{node_id}.html").write_text(
            render_detail(file, data, ref_to_file, ref_to_title, reviews.get(node_id)), encoding="utf-8"
        )
    build_public_evidence(root, output, records)
    (output / "data" / "nodes.json").write_text(
        json.dumps(public_node_data(records), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "data" / "graph.json").write_text(
        json.dumps(public_graph_data(records), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    search_index = {
        node_identity(file, data)[1]: {
            "sections": public_search_sections(
                file,
                data,
                ref_to_file,
                ref_to_title,
                reviews.get(node_identity(file, data)[1]),
            )
        }
        for file, data in records
    }
    (output / "data" / "search-index.json").write_text(
        json.dumps(search_index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    shutil.copy2(assets / "style.css", output / "assets" / "style.css")
    shutil.copy2(assets / "site.js", output / "assets" / "site.js")
    shutil.copy2(assets / "graph.js", output / "assets" / "graph.js")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    build_discovery_files(output, records, reviews)
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
