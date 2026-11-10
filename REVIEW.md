# 死因保质期复核清单

> 本文件由 `scripts/generate_review.py` 根据 `nodes/*.yaml` 与 `review_records.yaml` 自动生成，请勿手工编辑表格。
> 节点日期、顺序和新节点由脚本维护；人工复核结论写入 `review_records.yaml`。
> 本清单覆盖全部正式节点，不包含 `non-startup-tech/` 储备区，也不自动修改节点中的判断性内容。

## 复核规则

1. 复核状态使用：待复核｜已复核｜暂缓。没有人工记录的节点自动标为待复核；待复核包括尚未进入复核窗口的节点，不表示已经逾期。
2. 已到期或未来30日内到期的节点优先复核。表格按死因保质期排序，具体是否进入优先窗口以实际检查日期计算。
3. 复核时同时检查：死因是否仍成立，复活状态与置信度是否需要调整，证据是否仍支持原结论，证据链接是否仍可访问，以及本地附件是否仍存在。
4. 自动访问受限、反自动化响应或超时不等于链接失效，应转人工复核；不得仅凭访问结果改判。
5. 完成实际复核后，才更新节点的审核日期与死因保质期，并在 `review_records.yaml` 登记结论；不得只顺延日期。
6. 复核结论可填写：维持原判｜调整死因｜调整置信度｜调整复活状态｜修复证据；同时发生多项时用“、”连接，尚未复核填“—”。
7. 复核后日期是实际完成复核的日期，不是新的死因保质期；新的死因保质期以节点YAML为准。
8. 选择暂缓时，必须在备注中写明原因和下次检查条件。新的死因保质期仍须遵守节点格式规范，所有判断性修改均由人工审核定案。

## 复核清单

当前共16个正式节点：待复核16个，已复核0个，暂缓0个。

| 节点 | 审核日期 | 死因保质期 | 复核状态 | 复核结论 | 复核后日期 | 备注 |
|---|---|---|---|---|---|---|
| [大肥鱼赛博墓地](nodes/dafeiyu-cyber-cemetery.yaml) | 2026-10-26 | 2026-11-29 | 待复核 | — | — | — |
| [AI法律漏洞搜寻与意见提交](nodes/ai-legal-loophole-hunter.yaml) | 2026-10-31 | 2027-01-01 | 待复核 | — | — | — |
| [AI联合平台](nodes/ai-federation-platform.yaml) | 2026-10-30 | 2027-04-30 | 待复核 | — | — | — |
| [AI立法意见辅助提交](nodes/ai-legal-loophole-hunter_legislation-feedback.yaml) | 2026-10-30 | 2027-06-30 | 待复核 | — | — | — |
| [基于概率学模型的高考志愿填报服务（C端）](nodes/gaokao-zhiyuan-ai.yaml) | 2026-10-28 | 2027-07-15 | 待复核 | — | — | — |
| [颈深淋巴管／结—静脉吻合术治疗阿尔茨海默病](nodes/alzheimer-dclva-surgery.yaml) | 2026-11-07 | 2027-11-07 | 待复核 | — | — | — |
| [云端全流程科研自动化Agent](nodes/cloud-research-automation-agent.yaml) | 2026-11-07 | 2027-11-07 | 待复核 | — | — | — |
| [长期伴随学习辅助AI](nodes/long-term-learning-companion-ai.yaml) | 2026-11-07 | 2027-11-07 | 待复核 | — | — | — |
| [AI拦截仿真对话反诈Agent](nodes/ai-scam-interception-agent.yaml) | 2026-11-10 | 2027-11-10 | 待复核 | — | — | — |
| [开源哔哩哔哩自主宠物鲸Agent插件](nodes/bilibili-autonomous-pet-whale-agent-plugin.yaml) | 2026-11-11 | 2027-11-11 | 待复核 | — | — | — |
| [AI电子鼻（通用气味识别硬件创业）](nodes/electronic-nose-ai.yaml) | 2026-10-29 | 2028-01-01 | 待复核 | — | — | — |
| [AI游戏修改器及其平台](nodes/ai-game-modifier-platform.yaml) | 2026-11-05 | 2028-11-05 | 待复核 | — | — | — |
| [AI生成红色题材中小体量视觉小说](nodes/ai-red-visual-novel.yaml) | 2026-11-05 | 2028-11-05 | 待复核 | — | — | — |
| [开源仓库AI视频生成器](nodes/oss-video-generator.yaml) | 2026-11-02 | 2029-11-02 | 待复核 | — | — | — |
| [周历史简报及档案网站](nodes/internet-weekly-archive.yaml) | 2026-11-04 | 2029-11-04 | 待复核 | — | — | — |
| [开源知识库节点AI视频生成器](nodes/knowledge-base-ai-video-generator.yaml) | 2026-11-08 | 2029-11-08 | 待复核 | — | — | — |
