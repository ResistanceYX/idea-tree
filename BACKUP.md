# idea-tree 离线备份与恢复

## 当前状态

- 首次实际U盘备份：**已完成（2026-11-08）**。
- 最近成功备份：2026-11-08，快照目录为`idea-tree-backups/2026-11-08/`。
- 最近恢复验证：2026-11-08，通过；已从U盘Bundle恢复仓库，并通过G01、G02及全部自动化测试。
- 本文件只登记备份元数据与执行证据，不保存仓库压缩包、Issues正文或任何访问凭证。

在首次备份从U盘实际恢复并通过全部检查之前，不得将G03或本文件状态改为已完成。

## 备份规则

- 范围：完整Git历史、分支和标签，当前文件快照，全部开放及关闭Issues与评论。
- 位置：ResistanceYX持有的256GB离线U盘，卷标`IDEA_TREE_BACKUP`；根目录下的`idea-tree-backups/`。
- 频率：每月一次，建议与月度全检一并执行；相邻两次成功备份不应超过35天。
- 负责人：ResistanceYX。
- 保留方式：保留全部月份快照，不自动覆盖或删除旧备份。
- 隔离要求：备份只写入该U盘，不得上传到其他公开仓库、公开附件或公开网盘；平时断开U盘并妥善保管。
- 失败记录：脚本失败、U盘未写入、哈希不符或恢复验证失败均不得登记为成功；失败或月份遗漏须在下方执行记录中补记。

## 每次备份包含什么

```text
idea-tree-backups/
├── YYYY-MM-DD/
│   ├── repository.bundle
│   ├── working-tree.zip
│   ├── issues.json
│   ├── ISSUES.md
│   ├── manifest.json
│   └── restore-report.txt
└── backup-log.md
```

- `repository.bundle`：完整Git历史、分支和标签。
- `working-tree.zip`：当前文件快照，可直接解压阅读。
- `issues.json`：结构化Issues及评论，是Issues恢复的数据源。
- `ISSUES.md`：由JSON生成的可读Issues档案。
- `manifest.json`：来源commit、数量、文件大小和SHA-256。
- `restore-report.txt`：本次从U盘实际恢复的检查结果。

## Windows 10首次准备

1. 安装Git for Windows和64位Python 3.12。安装Python时勾选加入PATH及`py`启动器；Git保持默认选项即可。
2. 重新打开PowerShell，检查命令：

   ```powershell
   git --version
   py --version
   py -m pip install "PyYAML>=6.0,<7"
   ```

3. 下载主仓库最新ZIP并解压，进入包含`scripts`、`nodes`和本文件的目录。
4. 插入U盘，在文件资源管理器确认其盘符。以下示例使用`E:`，实际操作必须替换为自己的盘符；不要格式化U盘。
5. 在仓库目录运行：

   ```powershell
   py scripts\backup_repository.py --usb-root "E:\"
   ```

脚本会依次生成备份、校验U盘文件、从U盘Bundle恢复仓库、运行G01／G02及全部测试，并重新生成Issues档案。只有最后显示“备份及实际恢复验证全部通过”，本次备份才成功。

如果同日重试，脚本会创建带时间后缀的新目录，不覆盖前一次记录。失败目录以`.failed`结尾，应保留至问题查明，不得当作可用备份。

## 独立恢复与复核

日常备份已自动执行一次恢复验证。以后需要单独复核时，在包含脚本的目录运行：

```powershell
py scripts\restore_backup.py --snapshot "E:\idea-tree-backups\YYYY-MM-DD" --output "$HOME\Desktop\idea-tree-restore-test"
```

恢复结果包括：

- `restored-repository/`：从U盘Bundle克隆出的完整Git仓库；
- `restored-ISSUES.md`：从U盘JSON重新生成的Issues档案。

脚本会核对来源commit，运行G01、G02和全部测试，并比较Issues恢复结果。恢复目标中的`restored-repository`若已存在，脚本会拒绝覆盖。

若GitHub主仓库不可用，可直接使用：

```powershell
git clone "E:\idea-tree-backups\YYYY-MM-DD\repository.bundle" restored-repository
```

Issues以`issues.json`和`ISSUES.md`离线恢复使用。若需重新发布到GitHub，必须另行人工审核；不得静默覆盖现有Issues，也不承诺保留原作者、原编号或原始发布时间。

## 完成一次备份后

1. 将下方执行记录补齐，包括快照日期、来源commit、Issues数量和恢复结果。
2. 将“当前状态”改为最近真实成功的记录。
3. 核对U盘根目录的`backup-log.md`与公开记录一致。
4. 安全弹出U盘并断开保存。
5. 首次实际恢复通过后，方可关闭Issue #5中的G03事项。

## 执行记录

| 执行日期 | 快照目录 | 来源commit | Issues／评论 | 恢复验证 | 结果与说明 |
|---|---|---|---|---|---|
| 2026-11-08 | 未形成有效快照 | `918f70f791f5ae161d53f80f448521a07430c0c0` | 6／0 | 未通过 | Python 3.15恢复环境缺少PyYAML；已保留失败记录 |
| 2026-11-08 | 未形成有效快照 | `918f70f791f5ae161d53f80f448521a07430c0c0` | 未完成下载 | 未进入恢复 | Python 3.12根证书未配置；已保留失败记录 |
| 2026-11-08 | `2026-11-08` | `918f70f791f5ae161d53f80f448521a07430c0c0` | 6／0 | 通过 | 使用Python 3.12.10、PyYAML 6.0.3及certifi；首次备份成功 |
