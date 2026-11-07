#!/usr/bin/env python3
"""Independently restore and verify an existing offline idea-tree snapshot."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from backup_repository import restore_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="从U盘快照恢复idea-tree并运行验证。")
    parser.add_argument("--snapshot", type=Path, required=True, help="U盘中的月份快照目录")
    parser.add_argument("--output", type=Path, required=True, help="电脑上的空目录或尚不存在的恢复目录")
    args = parser.parse_args()
    try:
        report = restore_snapshot(args.snapshot, args.output, run_project_checks=True)
    except Exception as exc:
        print(f"恢复失败：{exc}", file=sys.stderr)
        return 1
    print("\n".join(report))
    print(f"恢复仓库位于：{args.output / 'restored-repository'}")
    print(f"恢复Issues位于：{args.output / 'restored-ISSUES.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
