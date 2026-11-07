from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import backup_repository as backup


SAMPLE_ISSUES = {
    "format_version": 1,
    "repository": "ResistanceYX/idea-tree",
    "fetched_at": "2026-11-07T00:00:00Z",
    "issue_count": 1,
    "comment_count": 1,
    "issues": [{
        "number": 5,
        "title": "备份测试",
        "state": "open",
        "created_at": "2026-11-01T00:00:00Z",
        "updated_at": "2026-11-01T00:00:00Z",
        "user": {"login": "tester"},
        "labels": [],
        "body": "正文",
        "comments_data": [{
            "created_at": "2026-11-02T00:00:00Z",
            "user": {"login": "reviewer"},
            "body": "评论",
        }],
    }],
}


class BackupRepositoryTests(unittest.TestCase):
    def make_payload(self, snapshot: Path) -> None:
        snapshot.mkdir()
        (snapshot / "repository.bundle").write_bytes(b"test-bundle")
        with zipfile.ZipFile(snapshot / "working-tree.zip", "w") as archive:
            archive.writestr("idea-tree/README.md", "test")
        backup.write_issues_files(snapshot, SAMPLE_ISSUES)
        backup.write_manifest(snapshot, SAMPLE_ISSUES["repository"], "abc123", SAMPLE_ISSUES)

    def test_issues_markdown_contains_body_and_comment(self) -> None:
        rendered = backup.render_issues_markdown(SAMPLE_ISSUES)
        self.assertIn("Issue #5：备份测试", rendered)
        self.assertIn("正文", rendered)
        self.assertIn("评论：reviewer", rendered)

    def test_payload_hash_verification_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = Path(temporary) / "snapshot"
            self.make_payload(snapshot)
            backup.verify_payload(snapshot)
            (snapshot / "repository.bundle").write_bytes(b"tampered")
            with self.assertRaisesRegex(RuntimeError, "哈希校验失败"):
                backup.verify_payload(snapshot)

    def test_local_git_bundle_can_be_restored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            subprocess.run(["git", "init", "-b", "main", str(source)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(source), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(source), "config", "user.email", "test@example.com"], check=True)
            (source / "README.md").write_text("restorable", encoding="utf-8")
            subprocess.run(["git", "-C", str(source), "add", "README.md"], check=True)
            subprocess.run(["git", "-C", str(source), "commit", "-m", "initial"], check=True, capture_output=True)
            head = subprocess.run(
                ["git", "-C", str(source), "rev-parse", "HEAD"],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
            snapshot = root / "snapshot"
            snapshot.mkdir()
            created_head = backup.create_git_snapshot(str(source), root / "work", snapshot)
            self.assertEqual(created_head, head)
            backup.write_issues_files(snapshot, SAMPLE_ISSUES)
            backup.write_manifest(snapshot, SAMPLE_ISSUES["repository"], head, SAMPLE_ISSUES)
            report = backup.restore_snapshot(snapshot, root / "restore", run_project_checks=False)
            self.assertEqual((root / "restore/restored-repository/README.md").read_text(), "restorable")
            self.assertIn("恢复验证成功", report[-1])

    def test_fetch_issues_downloads_comments_and_ignores_pull_requests(self) -> None:
        issue = {
            "number": 1, "title": "issue", "state": "open", "comments": 1,
            "comments_url": "https://api.github.com/comments/1", "labels": [],
        }
        pull_request = {"number": 2, "pull_request": {"url": "https://example.test"}}
        responses = {
            "/issues?state=all&per_page=100&page=1": [issue, pull_request],
            "/issues?state=all&per_page=100&page=2": [],
            "/comments/1?per_page=100&page=1": [{"body": "comment", "user": {"login": "reader"}}],
            "/comments/1?per_page=100&page=2": [],
        }

        class FakeResponse:
            def __init__(self, value):
                self.value = value

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return None

            def read(self):
                return json.dumps(self.value).encode()

        def fake_urlopen(request, timeout):
            for suffix, value in responses.items():
                if request.full_url.endswith(suffix):
                    return FakeResponse(value)
            raise AssertionError(request.full_url)

        with patch.object(backup.urllib.request, "urlopen", fake_urlopen):
            data = backup.fetch_issues("ResistanceYX/idea-tree")
        self.assertEqual(data["issue_count"], 1)
        self.assertEqual(data["comment_count"], 1)
        self.assertEqual(data["issues"][0]["comments_data"][0]["body"], "comment")

    def test_snapshot_names_do_not_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "2026-11-07").mkdir()
            name, staging = backup.allocate_snapshot(root, None)
            self.assertNotEqual(name, "2026-11-07")
            self.assertFalse(staging.exists())
            with self.assertRaisesRegex(RuntimeError, "拒绝覆盖"):
                backup.allocate_snapshot(root, "2026-11-07")


if __name__ == "__main__":
    unittest.main()
