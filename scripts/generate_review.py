#!/usr/bin/env python3
"""Generate REVIEW.md from nodes and separate human review records."""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from datetime import date, datetime
from difflib import unified_diff
from pathlib import Path

import yaml

try:
    from scripts.node_files import node_identity
except ModuleNotFoundError:  # Direct execution: python scripts/generate_review.py
    from node_files import node_identity

REVIEW_STATUSES = {"待复核", "已复核", "暂缓"}
REVIEW_CONCLUSIONS = {"维持原判", "调整死因", "调整置信度", "调整复活状态", "修复证据"}
RECORD_FIELDS = {"复核状态", "复核结论", "复核后日期", "备注"}


def markdown_cell(value: object) -> str:
    """Escape a scalar for use inside a Markdown table cell."""
    if value is None or value == "":
        return "—"
    text = str(value).replace("\\", "\\\\").replace("|", "\\|")
    return text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "<br>")


def date_text(value: object) -> str:
    if isinstance(value, datetime):
        return ""
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value
    return ""


def valid_date(value: object) -> bool:
    text = date_text(value)
    if not text:
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


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


def load_review_records(root: Path, known_ids: set[str]) -> dict[str, dict]:
    path = root / "review_records.yaml"
    if not path.is_file():
        raise ValueError("review_records.yaml 不存在")

    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if payload is None:
        payload = {"records": {}}
    if not isinstance(payload, dict) or set(payload) != {"records"}:
        raise ValueError("review_records.yaml 顶层只能包含 records")
    records = payload.get("records")
    if records is None:
        records = {}
    if not isinstance(records, dict):
        raise ValueError("review_records.yaml 的 records 必须是映射")

    validated: dict[str, dict] = {}
    for node_id, record in records.items():
        if not isinstance(node_id, str) or not node_id:
            raise ValueError("复核记录的节点 id 必须是非空字符串")
        if node_id not in known_ids:
            raise ValueError(f"复核记录指向不存在的节点：{node_id}")
        if not isinstance(record, dict):
            raise ValueError(f"{node_id} 的复核记录必须是映射")
        unknown_fields = set(record) - RECORD_FIELDS
        if unknown_fields:
            names = "、".join(sorted(str(field) for field in unknown_fields))
            raise ValueError(f"{node_id} 的复核记录存在未定义字段：{names}")

        status = record.get("复核状态")
        if status not in REVIEW_STATUSES:
            raise ValueError(f"{node_id} 的复核状态必须是待复核、已复核或暂缓")

        for field in ("复核结论", "备注"):
            if field in record and not isinstance(record[field], str):
                raise ValueError(f"{node_id} 的{field}必须是字符串")

        conclusion = record.get("复核结论", "")
        if conclusion:
            parts = conclusion.split("、")
            if any(part not in REVIEW_CONCLUSIONS for part in parts):
                raise ValueError(f"{node_id} 的复核结论包含未定义值：{conclusion}")
            if len(parts) != len(set(parts)):
                raise ValueError(f"{node_id} 的复核结论不得重复")
            if "维持原判" in parts and len(parts) > 1:
                raise ValueError(f"{node_id} 的维持原判不得与其他调整结论并列")

        reviewed_at = record.get("复核后日期")
        if reviewed_at not in (None, "") and not valid_date(reviewed_at):
            raise ValueError(f"{node_id} 的复核后日期必须是有效的 YYYY-MM-DD 日期")
        if status == "已复核" and (not conclusion or reviewed_at in (None, "")):
            raise ValueError(f"{node_id} 已复核时必须填写复核结论和复核后日期")
        if status == "暂缓" and not record.get("备注", "").strip():
            raise ValueError(f"{node_id} 暂缓时必须在备注中写明原因和下次检查条件")

        validated[node_id] = record
    return validated


def render_review(root: Path) -> str:
    nodes = load_nodes(root)
    known_ids = {node_identity(file, data)[1] for file, data in nodes}
    human_records = load_review_records(root, known_ids)
    nodes = sorted(
        nodes,
        key=lambda record: (
            date_text(record[1].get("死因保质期")) or "9999-12-31",
            node_identity(*record)[0],
        ),
    )

    status_counts: Counter[str] = Counter()
    rows: list[str] = []
    for file, data in nodes:
        node_number, node_id = node_identity(file, data)
        record = human_records.get(node_id, {})
        status = record.get("复核状态", "待复核")
        status_counts[status] += 1
        title = markdown_cell(data.get("标题", node_id))
        rows.append(
            "| "
            + " | ".join(
                (
                    f"`{node_number}`",
                    f"[{title}](nodes/{file.name})",
                    markdown_cell(data.get("审核日期")),
                    markdown_cell(data.get("死因保质期")),
                    markdown_cell(status),
                    markdown_cell(record.get("复核结论")),
                    markdown_cell(date_text(record.get("复核后日期"))),
                    markdown_cell(record.get("备注")),
                )
            )
            + " |"
        )

    lines = [
        "# 死因保质期复核清单",
        "",
        "> 本文件由 `scripts/generate_review.py` 根据 `nodes/*.yaml` 与 `review_records.yaml` 自动生成，请勿手工编辑表格。",
        "> 节点日期、顺序和新节点由脚本维护；人工复核结论写入 `review_records.yaml`。",
        "> 本清单覆盖全部正式节点，不包含 `non-startup-tech/` 储备区，也不自动修改节点中的判断性内容。",
        "",
        "## 复核规则",
        "",
        "1. 复核状态使用：待复核｜已复核｜暂缓。没有人工记录的节点自动标为待复核；待复核包括尚未进入复核窗口的节点，不表示已经逾期。",
        "2. 已到期或未来30日内到期的节点优先复核。表格按死因保质期排序，具体是否进入优先窗口以实际检查日期计算。",
        "3. 复核时同时检查：死因是否仍成立，复活状态与置信度是否需要调整，证据是否仍支持原结论，证据链接是否仍可访问，以及本地附件是否仍存在。",
        "4. 自动访问受限、反自动化响应或超时不等于链接失效，应转人工复核；不得仅凭访问结果改判。",
        "5. 完成实际复核后，才更新节点的审核日期与死因保质期，并在 `review_records.yaml` 登记结论；不得只顺延日期。",
        "6. 复核结论可填写：维持原判｜调整死因｜调整置信度｜调整复活状态｜修复证据；同时发生多项时用“、”连接，尚未复核填“—”。",
        "7. 复核后日期是实际完成复核的日期，不是新的死因保质期；新的死因保质期以节点YAML为准。",
        "8. 选择暂缓时，必须在备注中写明原因和下次检查条件。新的死因保质期仍须遵守节点格式规范，所有判断性修改均由人工审核定案。",
        "",
        "## 复核清单",
        "",
        f"当前共{len(nodes)}个正式节点：待复核{status_counts['待复核']}个，已复核{status_counts['已复核']}个，暂缓{status_counts['暂缓']}个。",
        "",
        "| 编号 | 节点 | 审核日期 | 死因保质期 | 复核状态 | 复核结论 | 复核后日期 | 备注 |",
        "|---|---|---|---|---|---|---|---|",
        *rows,
    ]
    return "\n".join(lines) + "\n"


def review_is_current(root: Path) -> bool:
    output = root / "REVIEW.md"
    return output.is_file() and output.read_text(encoding="utf-8") == render_review(root)


def generate_review(root: Path) -> str:
    content = render_review(root)
    (root / "REVIEW.md").write_text(content, encoding="utf-8")
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description="根据节点与人工记录生成或检查 REVIEW.md")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="仓库根目录，默认为当前目录")
    parser.add_argument("--check", action="store_true", help="只检查清单是否同步，不写入文件")
    args = parser.parse_args()
    root = args.root.resolve()

    try:
        expected = render_review(root)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"[错误] 无法生成复核清单：{exc}")
        return 1

    output = root / "REVIEW.md"
    if args.check:
        if not output.is_file():
            print("[错误] REVIEW.md 不存在，请运行：python scripts/generate_review.py --root .")
            return 1
        current = output.read_text(encoding="utf-8")
        if current != expected:
            print("[错误] REVIEW.md 与节点或人工复核记录不同步，请运行：python scripts/generate_review.py --root .")
            print(
                "\n".join(
                    unified_diff(
                        current.splitlines(),
                        expected.splitlines(),
                        fromfile="REVIEW.md（当前）",
                        tofile="REVIEW.md（应生成）",
                        lineterm="",
                    )
                )
            )
            return 1
        print(f"复核清单检查通过：REVIEW.md 与 {len(load_nodes(root))} 个节点及人工记录一致。")
        return 0

    output.write_text(expected, encoding="utf-8")
    print(f"已生成 REVIEW.md：收录 {len(load_nodes(root))} 个节点。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
