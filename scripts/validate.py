#!/usr/bin/env python3
"""Validate idea-tree's local structure without changing editorial judgments."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlparse

import yaml

try:
    from scripts.node_files import NODE_NUMBER_RE, node_identity, parse_node_filename
except ModuleNotFoundError:  # Direct execution: python scripts/validate.py
    from node_files import NODE_NUMBER_RE, node_identity, parse_node_filename

DEATH_TYPES = {
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
}
REVIVAL_STATUSES = {"死透", "复活候选", "已复活"}
INNOVATION_TYPES = {"渐进式", "突破式", "破坏式", "技术应用", "理论创新"}
ARCHIVE_TYPES = {"预审", "验尸"}
BUDGETS = {"低", "中", "高"}
CONFIDENCE_LEVELS = {"高", "中", "低"}

REQUIRED_TOP_FIELDS = (
    "编号",
    "id",
    "标题",
    "档案类型",
    "一句话",
    "复活状态",
    "创新类型",
    "领域",
    "子领域",
    "死法",
    "可拆零件",
    "死因保质期",
    "起草AI",
    "审核人",
    "审核日期",
)
ALLOWED_TOP_FIELDS = set(REQUIRED_TOP_FIELDS) | {
    "重启预算",
    "需求证据",
    "商业及社会价值评估",
    "相关节点",
    "备注",
}
ALLOWED_DEATH_FIELDS = {"类型", "证据", "推理", "分析", "案例", "证据链接", "置信度", "备注"}
ALLOWED_RELATION_FIELDS = {"节点", "关系", "说明"}

NORMAL_ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
DERIVED_ID_RE = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)*")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
EVIDENCE_PATH_RE = re.compile(r"evidence/[A-Za-z0-9._-]+")
PURE_INTERNAL_EVIDENCE = {"创始人自我分析", "内部推演", "内部推理", "逻辑推理", "纯内部推演"}


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        # February 29 becomes February 28 in a non-leap target year.
        return value.replace(year=value.year + years, day=28)


def parse_date(value: object) -> date | None:
    if isinstance(value, datetime):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def safe_local_path(root: Path, value: str) -> Path | None:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return root.joinpath(*path.parts)


def validate_repository(root: Path) -> dict[str, object]:
    root = root.resolve()
    errors: list[str] = []
    warnings: list[str] = []
    nodes: dict[Path, dict] = {}
    all_links: dict[str, list[str]] = defaultdict(list)

    def error(location: str, message: str) -> None:
        errors.append(f"{location}: {message}")

    def warning(location: str, message: str) -> None:
        warnings.append(f"{location}: {message}")

    nodes_dir = root / "nodes"
    files = sorted(nodes_dir.glob("*.yaml")) if nodes_dir.is_dir() else []
    if not files:
        error("nodes/", "没有找到任何 YAML 节点")

    for file in files:
        location = f"nodes/{file.name}"
        try:
            data = yaml.safe_load(file.read_text(encoding="utf-8"))
        except Exception as exc:
            error(location, f"YAML 解析失败：{exc}")
            continue
        if not isinstance(data, dict):
            error(location, "顶层必须是映射")
            continue
        nodes[file] = data

        for field in REQUIRED_TOP_FIELDS:
            if field not in data:
                error(location, f"缺少必选字段 `{field}`")
        for field in data:
            if field not in ALLOWED_TOP_FIELDS:
                error(location, f"存在节点格式未定义的顶层字段 `{field}`")

        try:
            file_number, file_id = parse_node_filename(file)
        except ValueError as exc:
            error(location, str(exc))
            file_number, file_id = None, None

        number = data.get("编号")
        if "编号" in data:
            if not isinstance(number, str) or not NODE_NUMBER_RE.fullmatch(number):
                error(location, "编号必须是带引号的四位数字字符串")
            elif number == "0000":
                error(location, "0000 永久保留，不得用于普通正式节点")
            elif file_number is not None and number != file_number:
                error(location, f"编号与文件名前四位不一致：`{number}` / `{file_number}`")

        node_id = data.get("id")
        if not nonempty_string(node_id) or not DERIVED_ID_RE.fullmatch(node_id):
            error(location, "id 必须使用全小写英文、数字、连字符及合法的派生下划线")
        elif "_" not in node_id and not NORMAL_ID_RE.fullmatch(node_id):
            error(location, "普通节点 id 只能使用英文、数字和连字符")
        if file_id is not None and node_id != file_id:
            error(location, f"id 与文件名不一致：`{node_id}` / `{file_id}`")

        for field in ("标题", "一句话", "领域", "子领域", "起草AI", "审核人"):
            if field in data and not nonempty_string(data.get(field)):
                error(location, f"`{field}` 必须是非空字符串")

        if data.get("档案类型") not in ARCHIVE_TYPES:
            error(location, "档案类型必须是 `预审` 或 `验尸`")
        status = data.get("复活状态")
        if status not in REVIVAL_STATUSES:
            error(location, "复活状态枚举错误")
        if "重启预算" in data and data.get("重启预算") not in BUDGETS:
            error(location, "重启预算必须是 `低`、`中` 或 `高`")

        innovation = data.get("创新类型")
        if (
            not isinstance(innovation, list)
            or not innovation
            or any(not isinstance(item, str) or item not in INNOVATION_TYPES for item in innovation)
        ):
            error(location, "创新类型必须是非空合法字符串数组")

        parts = data.get("可拆零件")
        if not isinstance(parts, list) or any(not nonempty_string(item) for item in parts):
            error(location, "可拆零件必须是非空字符串数组")

        value_assessment = data.get("商业及社会价值评估")
        if status in {"复活候选", "已复活"} and not nonempty_string(value_assessment):
            error(location, "复活候选与已复活节点必须填写商业及社会价值评估")
        if value_assessment is not None and not nonempty_string(value_assessment):
            error(location, "商业及社会价值评估如填写则必须是非空字符串")

        demand = data.get("需求证据")
        if demand is not None:
            if not isinstance(demand, dict) or not nonempty_string(demand.get("类型")):
                error(location, "需求证据必须是映射，并包含非空 `类型`")
            elif "附件" in demand and demand.get("附件") != "无":
                attachment = demand.get("附件")
                if not nonempty_string(attachment):
                    error(location, "需求证据附件必须是路径字符串或 `无`")
                else:
                    path = safe_local_path(root, attachment)
                    if path is None or not path.is_file():
                        error(location, f"需求证据附件不存在或路径不安全：`{attachment}`")

        review = parse_date(data.get("审核日期"))
        expiry = parse_date(data.get("死因保质期"))
        if review is None:
            error(location, "审核日期必须是有效的 YYYY-MM-DD 日期")
        if expiry is None:
            error(location, "死因保质期必须是有效的 YYYY-MM-DD 日期")
        if review is not None and expiry is not None:
            if expiry < review:
                error(location, "死因保质期不得早于审核日期")
            if expiry > add_years(review, 5):
                error(location, "死因保质期不得晚于审核日期起五年")
            if expiry > add_years(review, 3) and not nonempty_string(data.get("备注")):
                error(location, "死因保质期晚于审核日期起三年时必须在节点内备注原因")

        deaths = data.get("死法")
        if not isinstance(deaths, list) or not deaths:
            error(location, "死法必须是非空数组")
            continue

        node_links: list[str] = []
        for index, death in enumerate(deaths, start=1):
            death_location = f"{location} 死法{index}"
            if not isinstance(death, dict):
                error(death_location, "条目必须是映射")
                continue
            for field in death:
                if field not in ALLOWED_DEATH_FIELDS:
                    error(death_location, f"存在未定义字段 `{field}`")
            if death.get("类型") not in DEATH_TYPES:
                error(death_location, "死法类型不在分类法中")

            evidence = death.get("证据")
            if not nonempty_string(evidence):
                error(death_location, "缺少非空证据")
                evidence = ""
            if death.get("置信度") not in CONFIDENCE_LEVELS:
                error(death_location, "置信度必须是 `高`、`中` 或 `低`")

            if evidence == "创始人自我分析":
                if not nonempty_string(death.get("推理")) and not nonempty_string(death.get("分析")):
                    error(death_location, "创始人自我分析必须包含推理或分析")
            elif not nonempty_string(death.get("推理")):
                error(death_location, "非创始人自我分析的死法必须包含推理")

            links = death.get("证据链接", [])
            if links is None:
                links = []
            if not isinstance(links, list) or any(not nonempty_string(item) for item in links):
                error(death_location, "证据链接必须是字符串数组")
                links = []

            if len(links) > 16:
                error(death_location, "单条死法的证据链接不得超过16个")
            if len(links) > 8 and not nonempty_string(death.get("备注")):
                error(death_location, "单条死法超过8个证据链接时必须备注原因")
            if len(links) != len(set(links)):
                warning(death_location, "单条死法内存在重复链接")
            if death.get("置信度") == "高":
                if len(set(links)) < 2:
                    error(death_location, "高置信度至少需要两个不同证据链接")
                if evidence in PURE_INTERNAL_EVIDENCE:
                    error(death_location, "纯内部推演不得标为高置信度")
            if not links and ("公开" in evidence or "过往案例" in evidence):
                error(death_location, "声明公开案例或公开证据时必须挂证据链接")

            for url in links:
                parsed = urlparse(url)
                if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                    error(death_location, f"证据链接格式异常：`{url}`")
                lowered = (parsed.path + "?" + parsed.query).lower()
                if lowered.endswith(".pdf") or "/download/" in lowered or "download=" in lowered:
                    error(death_location, f"不得使用 PDF 直链或下载接口作为证据链接：`{url}`")
                node_links.append(url)
                all_links[url].append(f"{location}#{index}")

        reuse_limit = len(deaths) - 2
        for url, count in Counter(node_links).items():
            if count > reuse_limit:
                error(location, f"链接 `{url}` 复用 {count} 次，超过 n-2={reuse_limit}")

        raw_text = file.read_text(encoding="utf-8")
        for reference in sorted(set(EVIDENCE_PATH_RE.findall(raw_text))):
            path = safe_local_path(root, reference)
            if path is None or not path.is_file():
                error(location, f"正文引用的本地证据不存在：`{reference}`")

    ids: dict[str, list[Path]] = defaultdict(list)
    for file, data in nodes.items():
        if isinstance(data.get("id"), str):
            ids[data["id"]].append(file)
    for node_id, owners in ids.items():
        if len(owners) > 1:
            names = "、".join(file.name for file in owners)
            error("nodes/", f"id `{node_id}` 重复：{names}")

    numbers: dict[str, list[Path]] = defaultdict(list)
    for file, data in nodes.items():
        if isinstance(data.get("编号"), str):
            numbers[data["编号"]].append(file)
    for number, owners in numbers.items():
        if len(owners) > 1:
            names = "、".join(file.name for file in owners)
            error("nodes/", f"编号 `{number}` 重复：{names}")

    known_ids = set(ids)
    known_refs = set()
    ref_to_file = {}
    for file, data in nodes.items():
        try:
            node_identity(file, data)
        except ValueError:
            continue
        known_refs.add(file.stem)
        ref_to_file[file.stem] = file

    for file, data in nodes.items():
        node_id = data.get("id")
        location = f"nodes/{file.name}"
        if isinstance(node_id, str) and "_" in node_id:
            parent_id, child_name = node_id.rsplit("_", 1)
            if parent_id not in known_ids:
                error(location, f"直接派生节点缺少对应母题节点：`{parent_id}`")
            if not NORMAL_ID_RE.fullmatch(child_name):
                error(location, "派生节点的子题短名只能使用英文、数字和连字符")

        relations = data.get("相关节点", [])
        if relations is None:
            relations = []
        if not isinstance(relations, list):
            error(location, "相关节点必须是数组")
            continue
        for relation in relations:
            if not isinstance(relation, dict):
                error(location, "相关节点条目必须是映射")
                continue
            for field in relation:
                if field not in ALLOWED_RELATION_FIELDS:
                    error(location, f"相关节点存在未定义字段 `{field}`")
            target = relation.get("节点")
            if not nonempty_string(target) or not nonempty_string(relation.get("关系")):
                error(location, "相关节点条目必须包含非空节点和关系")
                continue
            if target == file.stem:
                error(location, "相关节点不得指向自身")
            if target not in known_refs:
                error(location, f"相关节点不存在或未使用带编号文件名主体：`{target}`")
                continue
            target_file = ref_to_file[target]
            target_relations = nodes[target_file].get("相关节点", []) or []
            has_return = any(
                isinstance(back, dict) and back.get("节点") == file.stem for back in target_relations
            )
            if not has_return:
                error(location, f"相关节点 `{target}` 缺少回程声明")

    readme = root / "README.md"
    if not readme.is_file():
        error("README.md", "文件不存在")
    else:
        for target in MARKDOWN_LINK_RE.findall(readme.read_text(encoding="utf-8")):
            target = target.strip()
            parsed = urlparse(target)
            if parsed.scheme or target.startswith("#"):
                continue
            local_target = unquote(parsed.path)
            if not local_target:
                continue
            path = safe_local_path(root, local_target)
            if path is None or not path.exists():
                error("README.md", f"本地链接不存在或路径不安全：`{target}`")

    return {
        "errors": errors,
        "warnings": warnings,
        "nodes": len(nodes),
        "deaths": sum(len(data.get("死法", [])) for data in nodes.values()),
        "unique_links": len(all_links),
        "link_occurrences": sum(len(locations) for locations in all_links.values()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="检查 idea-tree 节点结构、字段、关系和本地引用")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="仓库根目录，默认为当前目录")
    args = parser.parse_args()
    result = validate_repository(args.root)

    for item in result["warnings"]:
        print(f"[警告] {item}")
    for item in result["errors"]:
        print(f"[错误] {item}")
    print(
        "检查汇总："
        f"节点 {result['nodes']} 个，"
        f"死法 {result['deaths']} 条，"
        f"不同证据链接 {result['unique_links']} 个，"
        f"链接出现 {result['link_occurrences']} 次，"
        f"错误 {len(result['errors'])} 个，"
        f"警告 {len(result['warnings'])} 个。"
    )
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
