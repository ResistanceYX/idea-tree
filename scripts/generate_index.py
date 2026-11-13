#!/usr/bin/env python3
"""Generate a deterministic INDEX.md from validated idea-tree nodes."""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from difflib import unified_diff
from pathlib import Path

import yaml

try:
    from scripts.node_files import node_identity, node_sort_key
except ModuleNotFoundError:  # Direct execution: python scripts/generate_index.py
    from node_files import node_identity, node_sort_key

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
REVIVAL_STATUSES = ("死透", "复活候选", "已复活")
ARCHIVE_TYPES = ("预审", "验尸")


def markdown_cell(value: object) -> str:
    """Escape a scalar for use inside a Markdown table cell."""
    if value is None or value == "":
        return "—"
    text = str(value).replace("\\", "\\\\").replace("|", "\\|")
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def load_nodes(root: Path) -> list[tuple[Path, dict]]:
    nodes_dir = root / "nodes"
    files = sorted(nodes_dir.glob("*.yaml"), key=lambda path: path.name)
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


def ordered_death_types(data: dict) -> list[str]:
    present = {
        death.get("类型")
        for death in data.get("死法", [])
        if isinstance(death, dict) and isinstance(death.get("类型"), str)
    }
    ordered = [death_type for death_type in DEATH_TYPES if death_type in present]
    ordered.extend(sorted(present.difference(DEATH_TYPES)))
    return ordered


def render_index(records: list[tuple[Path, dict]]) -> str:
    """Render the complete index without dates, timestamps or random ordering."""
    records = sorted(records, key=node_sort_key)
    death_counts: Counter[str] = Counter()
    death_nodes: dict[str, set[str]] = defaultdict(set)
    status_counts: Counter[str] = Counter()
    archive_counts: Counter[str] = Counter()

    rows: list[str] = []
    for file, data in records:
        node_number, node_id = node_identity(file, data)
        deaths = [death for death in data.get("死法", []) if isinstance(death, dict)]
        types = ordered_death_types(data)
        status = str(data.get("复活状态", "—"))
        archive = str(data.get("档案类型", "—"))
        status_counts[status] += 1
        archive_counts[archive] += 1
        for death in deaths:
            death_type = death.get("类型")
            if isinstance(death_type, str):
                death_counts[death_type] += 1
                death_nodes[death_type].add(node_id)

        title = markdown_cell(data.get("标题", node_id))
        rows.append(
            "| "
            + " | ".join(
                (
                    f"`{node_number}`",
                    f"[{title}](nodes/{file.name})",
                    f"`{markdown_cell(node_id)}`",
                    markdown_cell(archive),
                    markdown_cell(status),
                    markdown_cell(data.get("领域")),
                    markdown_cell(data.get("子领域")),
                    markdown_cell("、".join(types)),
                    markdown_cell(data.get("重启预算")),
                    markdown_cell(data.get("审核日期")),
                    markdown_cell(data.get("死因保质期")),
                )
            )
            + " |"
        )

    lines = [
        "# 点子索引与死因统计",
        "",
        "> 本文件由 `scripts/generate_index.py` 根据 `nodes/*.yaml` 自动生成，请勿手工维护其中的节点数据。",
        "> 同一批节点重复生成的内容一致；修改节点后应重新生成本文件。",
        "",
        "## 总览",
        "",
        f"- 节点：{len(records)} 个",
        f"- 死法：{sum(death_counts.values())} 条",
        f"- 复活候选：{status_counts['复活候选']} 个",
        f"- 已复活：{status_counts['已复活']} 个",
        "",
        "## 节点索引",
        "",
        "| 编号 | 标题 | id | 档案类型 | 复活状态 | 领域 | 子领域 | 死法类型 | 重启预算 | 审核日期 | 死因保质期 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
        *rows,
        "",
        "## 按死法类型统计",
        "",
        "死法条数按死法条目计数；涉及节点数按出现该死法类型的不同节点计数。",
        "",
        "| 死法类型 | 死法条数 | 涉及节点数 |",
        "|---|---:|---:|",
    ]
    for death_type in DEATH_TYPES:
        lines.append(f"| {death_type} | {death_counts[death_type]} | {len(death_nodes[death_type])} |")
    for death_type in sorted(death_counts.keys() - DEATH_TYPES):
        lines.append(f"| {markdown_cell(death_type)} | {death_counts[death_type]} | {len(death_nodes[death_type])} |")

    lines.extend(
        (
            "",
            "## 按复活状态统计",
            "",
            "| 复活状态 | 节点数 |",
            "|---|---:|",
        )
    )
    for status in REVIVAL_STATUSES:
        lines.append(f"| {status} | {status_counts[status]} |")
    for status in sorted(status_counts.keys() - REVIVAL_STATUSES):
        lines.append(f"| {markdown_cell(status)} | {status_counts[status]} |")

    lines.extend(
        (
            "",
            "## 按档案类型统计",
            "",
            "| 档案类型 | 节点数 |",
            "|---|---:|",
        )
    )
    for archive in ARCHIVE_TYPES:
        lines.append(f"| {archive} | {archive_counts[archive]} |")
    for archive in sorted(archive_counts.keys() - ARCHIVE_TYPES):
        lines.append(f"| {markdown_cell(archive)} | {archive_counts[archive]} |")

    return "\n".join(lines) + "\n"


def expected_index(root: Path) -> str:
    return render_index(load_nodes(root))


def generate_index(root: Path) -> str:
    content = expected_index(root)
    (root / "INDEX.md").write_text(content, encoding="utf-8")
    return content


def index_is_current(root: Path) -> bool:
    output = root / "INDEX.md"
    return output.is_file() and output.read_text(encoding="utf-8") == expected_index(root)


def main() -> int:
    parser = argparse.ArgumentParser(description="根据节点生成或检查 INDEX.md")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="仓库根目录，默认为当前目录")
    parser.add_argument("--check", action="store_true", help="只检查索引是否同步，不写入文件")
    args = parser.parse_args()
    root = args.root.resolve()

    try:
        expected = expected_index(root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"[错误] 无法读取节点：{exc}")
        return 1

    output = root / "INDEX.md"
    if args.check:
        if not output.is_file():
            print("[错误] INDEX.md 不存在，请运行：python scripts/generate_index.py --root .")
            return 1
        current = output.read_text(encoding="utf-8")
        if current != expected:
            print("[错误] INDEX.md 与当前节点不同步，请运行：python scripts/generate_index.py --root .")
            print(
                "\n".join(
                    unified_diff(
                        current.splitlines(),
                        expected.splitlines(),
                        fromfile="INDEX.md（当前）",
                        tofile="INDEX.md（应生成）",
                        lineterm="",
                    )
                )
            )
            return 1
        print(f"索引检查通过：INDEX.md 与 {len(load_nodes(root))} 个节点及统计一致。")
        return 0

    output.write_text(expected, encoding="utf-8")
    print(f"已生成 INDEX.md：收录 {len(load_nodes(root))} 个节点。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
