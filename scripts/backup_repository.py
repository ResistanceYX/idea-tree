#!/usr/bin/env python3
"""Create and verify an offline idea-tree backup on a removable drive."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_REPOSITORY = "ResistanceYX/idea-tree"
PAYLOAD_FILES = ("repository.bundle", "working-tree.zip", "issues.json", "ISSUES.md")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_command(args: list[str], cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"找不到命令：{args[0]}。请先安装并重新打开终端。") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"命令执行失败：{' '.join(args)}\n{exc.stdout}") from exc
    return result.stdout.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def api_json(url: str, token: str | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "idea-tree-offline-backup/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub API返回HTTP {exc.code}：{url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"无法访问GitHub API：{url}；{exc.reason}") from exc


def fetch_pages(url: str, token: str | None = None) -> list[dict[str, Any]]:
    separator = "&" if "?" in url else "?"
    page = 1
    records: list[dict[str, Any]] = []
    while True:
        batch = api_json(f"{url}{separator}per_page=100&page={page}", token)
        if not isinstance(batch, list):
            raise RuntimeError(f"GitHub API未返回列表：{url}")
        records.extend(batch)
        if len(batch) < 100:
            return records
        page += 1


def fetch_issues(repository: str, token: str | None = None) -> dict[str, Any]:
    base = f"https://api.github.com/repos/{repository}"
    raw_issues = fetch_pages(f"{base}/issues?state=all", token)
    issues: list[dict[str, Any]] = []
    comment_count = 0
    for issue in raw_issues:
        if "pull_request" in issue:
            continue
        comments = fetch_pages(issue["comments_url"], token) if issue.get("comments", 0) else []
        stored = dict(issue)
        stored["comments_data"] = comments
        issues.append(stored)
        comment_count += len(comments)
    issues.sort(key=lambda item: item["number"])
    return {
        "format_version": 1,
        "repository": repository,
        "fetched_at": now_iso(),
        "issue_count": len(issues),
        "comment_count": comment_count,
        "issues": issues,
    }


def render_issues_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# idea-tree Issues 离线档案",
        "",
        f"- 仓库：{data['repository']}",
        f"- 获取时间：{data['fetched_at']}",
        f"- Issues：{data['issue_count']}个",
        f"- 评论：{data['comment_count']}条",
        "",
        "本文件由issues.json生成；恢复时以JSON为结构化数据源。",
    ]
    for issue in data["issues"]:
        labels = "、".join(label["name"] for label in issue.get("labels", [])) or "无"
        user = (issue.get("user") or {}).get("login", "未知")
        lines.extend([
            "",
            f"## Issue #{issue['number']}：{issue['title']}",
            "",
            f"- 状态：{issue['state']}",
            f"- 作者：{user}",
            f"- 创建时间：{issue.get('created_at', '未知')}",
            f"- 更新时间：{issue.get('updated_at', '未知')}",
            f"- 标签：{labels}",
            "",
            issue.get("body") or "（无正文）",
        ])
        for comment in issue.get("comments_data", []):
            author = (comment.get("user") or {}).get("login", "未知")
            lines.extend([
                "",
                f"### 评论：{author}，{comment.get('created_at', '未知')}",
                "",
                comment.get("body") or "（空评论）",
            ])
    lines.append("")
    return "\n".join(lines)


def write_issues_files(snapshot: Path, data: dict[str, Any]) -> None:
    (snapshot / "issues.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (snapshot / "ISSUES.md").write_text(render_issues_markdown(data), encoding="utf-8")


def create_git_snapshot(repository_url: str, work_dir: Path, snapshot: Path) -> str:
    mirror = work_dir / "source-mirror.git"
    run_command(["git", "clone", "--mirror", repository_url, str(mirror)])
    head_ref = run_command(["git", f"--git-dir={mirror}", "symbolic-ref", "HEAD"])
    branch = head_ref.removeprefix("refs/heads/")
    head = run_command(["git", f"--git-dir={mirror}", "rev-parse", branch])
    bundle = snapshot / "repository.bundle"
    run_command(["git", f"--git-dir={mirror}", "bundle", "create", str(bundle), "--all"])
    run_command(["git", f"--git-dir={mirror}", "bundle", "verify", str(bundle)])
    run_command([
        "git", f"--git-dir={mirror}", "archive", "--format=zip",
        f"--prefix=idea-tree/", "--output", str(snapshot / "working-tree.zip"), branch,
    ])
    return head


def write_manifest(
    snapshot: Path,
    repository: str,
    source_head: str,
    issues: dict[str, Any],
    restore_verified: bool = False,
) -> dict[str, Any]:
    files = {
        name: {"bytes": (snapshot / name).stat().st_size, "sha256": sha256_file(snapshot / name)}
        for name in PAYLOAD_FILES
    }
    manifest = {
        "format_version": 1,
        "repository": repository,
        "created_at": now_iso(),
        "source_head": source_head,
        "issue_count": issues["issue_count"],
        "comment_count": issues["comment_count"],
        "restore_verified": restore_verified,
        "files": files,
    }
    (snapshot / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def verify_payload(snapshot: Path) -> dict[str, Any]:
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    for name, expected in manifest["files"].items():
        path = snapshot / name
        if not path.is_file():
            raise RuntimeError(f"备份缺少文件：{name}")
        if path.stat().st_size != expected["bytes"] or sha256_file(path) != expected["sha256"]:
            raise RuntimeError(f"备份哈希校验失败：{name}")
    with zipfile.ZipFile(snapshot / "working-tree.zip") as archive:
        broken = archive.testzip()
        if broken:
            raise RuntimeError(f"文件快照ZIP损坏：{broken}")
    issues = json.loads((snapshot / "issues.json").read_text(encoding="utf-8"))
    if issues["issue_count"] != len(issues["issues"]):
        raise RuntimeError("Issues数量与JSON内容不一致")
    if (snapshot / "ISSUES.md").read_text(encoding="utf-8") != render_issues_markdown(issues):
        raise RuntimeError("ISSUES.md与issues.json不一致")
    return manifest


def restore_snapshot(snapshot: Path, output_root: Path, run_project_checks: bool = True) -> list[str]:
    verify_payload(snapshot)
    restored = output_root / "restored-repository"
    if restored.exists():
        raise RuntimeError(f"恢复目标已存在，拒绝覆盖：{restored}")
    output_root.mkdir(parents=True, exist_ok=True)
    report = [f"开始恢复验证：{now_iso()}", "1. 备份文件哈希、ZIP及Issues一致性检查通过。"]
    run_command(["git", "clone", str(snapshot / "repository.bundle"), str(restored)])
    report.append("2. 已从U盘Bundle重新克隆完整Git仓库。")
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    restored_head = run_command(["git", "rev-parse", "HEAD"], cwd=restored)
    if restored_head != manifest["source_head"]:
        raise RuntimeError(f"恢复commit不一致：{restored_head} != {manifest['source_head']}")
    report.append(f"3. 恢复后的HEAD与来源一致：{restored_head}。")
    if run_project_checks:
        run_command([sys.executable, "scripts/validate.py", "--root", "."], cwd=restored)
        run_command([sys.executable, "scripts/generate_index.py", "--root", ".", "--check"], cwd=restored)
        run_command([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], cwd=restored)
        report.append("4. 恢复仓库中的G01、G02及全部自动化测试通过。")
    issues = json.loads((snapshot / "issues.json").read_text(encoding="utf-8"))
    regenerated = output_root / "restored-ISSUES.md"
    regenerated.write_text(render_issues_markdown(issues), encoding="utf-8")
    if regenerated.read_text(encoding="utf-8") != (snapshot / "ISSUES.md").read_text(encoding="utf-8"):
        raise RuntimeError("Issues恢复结果与原档案不一致")
    report.append(
        f"5. Issues结构化恢复通过：{issues['issue_count']}个Issues、{issues['comment_count']}条评论。"
    )
    report.append(f"恢复验证成功：{now_iso()}")
    return report


def append_log(backup_root: Path, name: str, success: bool, details: str) -> None:
    log = backup_root / "backup-log.md"
    if not log.exists():
        log.write_text("# idea-tree U盘备份日志\n", encoding="utf-8")
    status = "成功" if success else "失败"
    with log.open("a", encoding="utf-8") as handle:
        handle.write(f"\n## {now_iso()}｜{name}｜{status}\n\n{details}\n")


def allocate_snapshot(backup_root: Path, requested: str | None) -> tuple[str, Path]:
    if requested:
        if requested in {".", ".."} or any(char in requested for char in "/\\"):
            raise ValueError("快照名称不得包含路径分隔符")
        name = requested
    else:
        name = datetime.now().astimezone().strftime("%Y-%m-%d")
        if (backup_root / name).exists():
            name += datetime.now().astimezone().strftime("_%H%M%S")
    final = backup_root / name
    if final.exists():
        raise RuntimeError(f"快照已存在，拒绝覆盖：{final}")
    staging = backup_root / f".{name}.tmp-{uuid.uuid4().hex[:8]}"
    return name, staging


def backup_repository(
    usb_root: Path,
    repository: str = DEFAULT_REPOSITORY,
    source_url: str | None = None,
    snapshot_name: str | None = None,
) -> Path:
    if not usb_root.is_dir():
        raise RuntimeError(f"U盘路径不存在或不可访问：{usb_root}")
    backup_root = usb_root / "idea-tree-backups"
    backup_root.mkdir(parents=True, exist_ok=True)
    name, staging = allocate_snapshot(backup_root, snapshot_name)
    final = backup_root / name
    source_url = source_url or f"https://github.com/{repository}.git"
    issues: dict[str, Any] | None = None
    try:
        staging.mkdir()
        with tempfile.TemporaryDirectory(prefix="idea-tree-backup-") as temporary:
            work = Path(temporary)
            print("[1/6] 下载完整Git历史并生成Bundle和文件快照……", flush=True)
            head = create_git_snapshot(source_url, work, staging)
            print(f"      来源commit：{head}", flush=True)
            print("[2/6] 下载全部Issues及评论……", flush=True)
            issues = fetch_issues(repository)
            write_issues_files(staging, issues)
            print(f"      {issues['issue_count']}个Issues，{issues['comment_count']}条评论。", flush=True)
            print("[3/6] 计算U盘文件哈希……", flush=True)
            write_manifest(staging, repository, head, issues)
            verify_payload(staging)
            print("[4/6] 从U盘Bundle恢复仓库并运行完整检查……", flush=True)
            report = restore_snapshot(staging, work / "restore-test", run_project_checks=True)
            print("[5/6] 重新读取并恢复Issues档案……", flush=True)
            write_manifest(staging, repository, head, issues, restore_verified=True)
            verify_payload(staging)
            (staging / "restore-report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
        staging.rename(final)
        append_log(
            backup_root,
            name,
            True,
            f"来源commit：`{head}`；Issues：{issues['issue_count']}个；评论：{issues['comment_count']}条；恢复验证：通过。",
        )
        print("[6/6] 备份及实际恢复验证全部通过。", flush=True)
        print(f"备份位置：{final}", flush=True)
        print("请将上述日期、commit、Issues数量和恢复结果登记到主仓库BACKUP.md。", flush=True)
        return final
    except Exception as exc:
        failure = staging.with_name(staging.name + ".failed")
        if staging.exists() and not failure.exists():
            (staging / "restore-report.txt").write_text(f"备份失败：{exc}\n", encoding="utf-8")
            staging.rename(failure)
        append_log(backup_root, name, False, str(exc))
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="将idea-tree完整备份到U盘，并实际验证可恢复性。")
    parser.add_argument("--usb-root", type=Path, required=True, help="U盘根目录，例如Windows的E:\\")
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY, help="GitHub仓库，格式为所有者/名称")
    parser.add_argument("--source-url", help=argparse.SUPPRESS)
    parser.add_argument("--snapshot-name", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        backup_repository(args.usb_root, args.repository, args.source_url, args.snapshot_name)
    except Exception as exc:
        print(f"\n备份失败：{exc}", file=sys.stderr, flush=True)
        print("此次不得登记为成功；请保留错误信息并排查后重试。", file=sys.stderr, flush=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
