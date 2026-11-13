<!-- BEGIN FILE: scripts/node_files.py -->
```python
#!/usr/bin/env python3
"""Parse permanently numbered formal-node filenames without assigning numbers."""

from __future__ import annotations

import re
from pathlib import Path

NODE_NUMBER_RE = re.compile(r"[0-9]{4}")
NODE_STEM_RE = re.compile(r"(?P<number>[0-9]{4})-(?P<node_id>[a-z0-9]+(?:[-_][a-z0-9]+)*)")


def parse_node_stem(stem: str) -> tuple[str, str]:
    """Return (number, internal id) from a <four-digits>-<id> file stem."""
    match = NODE_STEM_RE.fullmatch(stem)
    if not match:
        raise ValueError(f"节点文件名主体必须为 `<四位数字>-<id>`：`{stem}`")
    return match.group("number"), match.group("node_id")


def parse_node_filename(file: Path) -> tuple[str, str]:
    """Return (number, internal id) from a formal-node YAML path."""
    if file.suffix != ".yaml":
        raise ValueError(f"正式节点必须使用 .yaml 扩展名：`{file.name}`")
    try:
        return parse_node_stem(file.stem)
    except ValueError as exc:
        raise ValueError(f"nodes/{file.name} 的文件名必须为 `<四位数字>-<id>.yaml`") from exc


def node_identity(file: Path, data: dict) -> tuple[str, str]:
    """Validate filename/metadata agreement and return (number, internal id)."""
    file_number, file_id = parse_node_filename(file)
    number = data.get("编号")
    if not isinstance(number, str) or not NODE_NUMBER_RE.fullmatch(number):
        raise ValueError(f"nodes/{file.name} 的 `编号` 必须是带引号的四位数字字符串")
    if number == "0000":
        raise ValueError(f"nodes/{file.name} 不得使用永久保留的 `0000` 编号")
    if number != file_number:
        raise ValueError(f"nodes/{file.name} 的 `编号` 与文件名前四位不一致：`{number}` / `{file_number}`")
    node_id = data.get("id")
    if node_id != file_id:
        raise ValueError(f"nodes/{file.name} 的 `id` 与编号前缀后的文件名主体不一致：`{node_id}` / `{file_id}`")
    return number, node_id


def node_sort_key(record: tuple[Path, dict]) -> tuple[str, str]:
    """Sort by the assigned permanent number; never assign or renumber nodes."""
    return node_identity(*record)
```
<!-- END FILE: scripts/node_files.py -->
