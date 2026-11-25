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

## 当前复核周期分布

> 每个正式节点按当前死因保质期与统计基准日期的日历间隔只计入一档：有已完成复核记录时取最新复核后日期，否则取节点审核日期；多次复核不累加。
> 三个月内指不足三个月；带“至”的中间区间均不含两端，单独列出的三个月、六个月、一年、两年和三年按日历日期判断；三年至五年不含三年、包含五年。
> 本统计只反映当前复核周期设定，用于发现模板化集中，不表示剩余时间或逾期状态，也不自动修改日期或节点结论。

| 当前复核周期 | 节点数 |
|---|---:|
| 三个月内 | 1 |
| 三个月 | 1 |
| 三至六个月 | 0 |
| 六个月 | 6 |
| 六至十二个月 | 4 |
| 一年 | 32 |
| 一年至两年 | 2 |
| 两年 | 2 |
| 两年至三年 | 0 |
| 三年 | 3 |
| 三年至五年 | 0 |
| **合计** | **51** |

## 复核清单

当前共51个正式节点：待复核49个，已复核2个，暂缓0个。

| 编号 | 节点 | 审核日期 | 死因保质期 | 复核状态 | 复核结论 | 复核后日期 | 备注 |
|---|---|---|---|---|---|---|---|
| `0005` | [AI法律漏洞搜寻与意见提交](nodes/0005-ai-legal-loophole-hunter.yaml) | 2026-10-31 | 2027-01-01 | 待复核 | — | — | — |
| `0001` | [大肥鱼赛博墓地](nodes/0001-dafeiyu-cyber-cemetery.yaml) | 2026-11-19 | 2027-02-19 | 已复核 | 调整置信度、修复证据 | 2026-11-19 | 第一次到期前实质复核。维持预审、死透及四类死法；补充大肥鱼活跃期情感投入与扩散报道、B站社区规范和风控报道，<br>修正“弃养即不会缅怀”的绝对推理；季节魔咒因缺少特定热梗衰退及墓地需求直接证据，由高调整为中。<br>原有六个证据链接均可读取且仍支持各自的一般机制或历史案例；无节点专用本地附件，不存在附件缺失。<br>新证据只支持需求分层、季节依赖和平台风险，不证明赛博墓地已实现、已有持续使用或商业闭环。<br> |
| `0004` | [AI联合平台](nodes/0004-ai-federation-platform.yaml) | 2026-10-30 | 2027-04-30 | 待复核 | — | — | — |
| `0043` | [俄乌多源战线与战报溯源档案库](nodes/0043-ukraine-multisource-frontline-archive.yaml) | 2026-11-20 | 2027-05-20 | 待复核 | — | — | — |
| `0044` | [可选块可调注释通用代码注释Agent](nodes/0044-code-comment-agent.yaml) | 2026-11-25 | 2027-05-25 | 待复核 | — | — | — |
| `0048` | [专业CI工作流注释与说明Agent](nodes/0048-single-language_fixed_ci.yaml) | 2026-11-25 | 2027-05-25 | 待复核 | — | — | — |
| `0050` | [Agent交流式遗留代码故障知识库](nodes/0050-agent-legacy-code-failure-knowledge-base.yaml) | 2026-11-25 | 2027-05-25 | 待复核 | — | — | — |
| `0051` | [自指式程序修改Agent及其平台](nodes/0051-self-referential-program-modifier-platform.yaml) | 2026-11-25 | 2027-05-25 | 待复核 | — | — | — |
| `0010` | [AI立法意见辅助提交](nodes/0010-ai-legal-loophole-hunter_legislation-feedback.yaml) | 2026-10-30 | 2027-06-30 | 待复核 | — | — | — |
| `0002` | [基于概率学模型的高考志愿填报服务（C端）](nodes/0002-gaokao-zhiyuan-ai.yaml) | 2026-10-28 | 2027-07-15 | 待复核 | — | — | — |
| `0045` | [不可选块可调注释通用代码注释Agent](nodes/0045-code-comment-agent_batch.yaml) | 2026-11-25 | 2027-08-25 | 待复核 | — | — | — |
| `0049` | [固定注释策略类比修改与合并Agent](nodes/0049-single-language_fixed_variant-composer.yaml) | 2026-11-25 | 2027-08-25 | 待复核 | — | — | — |
| `0011` | [颈深淋巴管／结—静脉吻合术治疗阿尔茨海默病](nodes/0011-alzheimer-dclva-surgery.yaml) | 2026-11-07 | 2027-11-07 | 待复核 | — | — | — |
| `0012` | [长期伴随学习辅助AI](nodes/0012-long-term-learning-companion-ai.yaml) | 2026-11-07 | 2027-11-07 | 待复核 | — | — | — |
| `0013` | [云端全流程科研自动化Agent](nodes/0013-cloud-research-automation-agent.yaml) | 2026-11-07 | 2027-11-07 | 待复核 | — | — | — |
| `0015` | [AI拦截仿真对话反诈Agent](nodes/0015-ai-scam-interception-agent.yaml) | 2026-11-10 | 2027-11-10 | 待复核 | — | — | — |
| `0016` | [开源哔哩哔哩自主宠物鲸Agent插件](nodes/0016-bilibili-autonomous-pet-whale-agent-plugin.yaml) | 2026-11-11 | 2027-11-11 | 待复核 | — | — | — |
| `0017` | [开源GitHub有趣仓库发现Agent插件](nodes/0017-github-interesting-repository-discovery-agent-plugin.yaml) | 2026-11-12 | 2027-11-12 | 待复核 | — | — | — |
| `0018` | [开源arXiv有趣论文发现及总结Agent插件](nodes/0018-arxiv-interesting-paper-discovery-summary-agent-plugin.yaml) | 2026-11-12 | 2027-11-12 | 待复核 | — | — | — |
| `0019` | [开源理论研究路径生成及记录辅助理解Agent插件](nodes/0019-research-theory-path-generation-comprehension-agent-plugin.yaml) | 2026-11-12 | 2027-11-12 | 待复核 | — | — | — |
| `0020` | [个性化DSH平台自动浏览、内容发现及总结插件生成Agent](nodes/0020-dsh-platform-content-discovery-plugin-generator-agent.yaml) | 2026-11-12 | 2027-11-12 | 待复核 | — | — | — |
| `0021` | [DSH插件产出内容汇总审核与优先级排序Agent](nodes/0021-dsh-plugin-output-review-prioritization-agent.yaml) | 2026-11-12 | 2027-11-12 | 待复核 | — | — | — |
| `0022` | [通用DSH跨平台自主宠物鲸插件](nodes/0022-universal-dsh-cross-platform-autonomous-pet-whale-plugin.yaml) | 2026-11-12 | 2027-11-12 | 待复核 | — | — | — |
| `0023` | [上市企业多源风险定时监测Agent插件](nodes/0023-listed-company-multi-source-risk-monitoring-agent.yaml) | 2026-11-13 | 2027-11-13 | 待复核 | — | — | — |
| `0024` | [政府部门权力滥用与贪腐风险扫描反馈Agent](nodes/0024-government-power-abuse-corruption-risk-scanning-agent.yaml) | 2026-11-13 | 2027-11-13 | 待复核 | — | — | — |
| `0025` | [大肥鱼消除计划](nodes/0025-dafeiyu-cleaner.yaml) | 2026-11-13 | 2027-11-13 | 待复核 | — | — | — |
| `0026` | [可插卡使用蜂窝数据的平板设备](nodes/0026-cellular-tablet-device.yaml) | 2026-11-14 | 2027-11-14 | 待复核 | — | — | — |
| `0027` | [防水防油一次性手套](nodes/0027-water-oil-resistant-disposable-gloves.yaml) | 2026-11-14 | 2027-11-14 | 待复核 | — | — | — |
| `0028` | [开源建筑图纸低级风险智能检测Agent](nodes/0028-open-source-building-drawing-risk-checker-agent.yaml) | 2026-11-14 | 2027-11-14 | 待复核 | — | — | — |
| `0030` | [开源家庭网络漏洞检查与修复辅助Agent](nodes/0030-open-source-home-network-vulnerability-repair-agent.yaml) | 2026-11-14 | 2027-11-14 | 待复核 | — | — | — |
| `0031` | [DNA健康信息与就医讨论辅助Agent](nodes/0031-dna-health-information-clinical-discussion-agent.yaml) | 2026-11-14 | 2027-11-14 | 待复核 | — | — | — |
| `0032` | [AI自助生成与使用表情包插件](nodes/0032-ai-generated-chat-sticker-plugin.yaml) | 2026-11-14 | 2027-11-14 | 待复核 | — | — | — |
| `0033` | [开源古籍版本比对与校勘辅助Agent插件](nodes/0033-open-source-guji-collation-agent-plugin.yaml) | 2026-11-14 | 2027-11-14 | 待复核 | — | — | — |
| `0034` | [开源知网论文全量扫描与科研诚信反馈Agent](nodes/0034-open-source-cnki-paper-integrity-feedback-agent.yaml) | 2026-11-15 | 2027-11-15 | 待复核 | — | — | — |
| `0035` | [开源单文献学术评议Agent](nodes/0035-open-source-single-paper-academic-review-agent.yaml) | 2026-11-15 | 2027-11-15 | 待复核 | — | — | — |
| `0036` | [基于多次多模态回传的超深海数据传输系统](nodes/0036-hadal-multimodal-store-forward-data-transfer.yaml) | 2026-11-16 | 2027-11-16 | 待复核 | — | — | — |
| `0037` | [超深海既有数据识别与未知候选搜索反馈Agent](nodes/0037-hadal-data-recognition-unknown-search-agent.yaml) | 2026-11-16 | 2027-11-16 | 待复核 | — | — | — |
| `0029` | [开源裁判文书形式异常检测反馈Agent](nodes/0029-open-source-judgment-formal-error-feedback-agent.yaml) | 2026-11-17 | 2027-11-17 | 已复核 | 调整复活状态、修复证据 | 2026-11-17 | 第一次提前复核。核对三个同作者公开MCP仓库及0029原有证据，确认局部专项软件原型已存在，<br>调整复活状态并补充证据；项目自述、示例与自带测试均未当作独立司法效果或真实需求证明。<br> |
| `0038` | [授权系统攻击模拟与漏洞复核Agent](nodes/0038-authorized-attack-simulation-vulnerability-review-agent.yaml) | 2026-11-17 | 2027-11-17 | 待复核 | — | — | — |
| `0039` | [超深海多模态环境记录与时空对齐离线Agent](nodes/0039-hadal-multimodal-environment-record-alignment-offline-agent.yaml) | 2026-11-17 | 2027-11-17 | 待复核 | — | — | — |
| `0040` | [超深海多模态观测总结与证据回链离线Agent](nodes/0040-hadal-multimodal-observation-summary-evidence-offline-agent.yaml) | 2026-11-17 | 2027-11-17 | 待复核 | — | — | — |
| `0041` | [多传感器识别与激光自动灭蚊器](nodes/0041-multisensor-laser-mosquito-control.yaml) | 2026-11-20 | 2027-11-20 | 待复核 | — | — | — |
| `0042` | [三甲医院诊疗档案区域统一系统](nodes/0042-tertiary-hospital-clinical-record-interoperability.yaml) | 2026-11-20 | 2027-11-20 | 待复核 | — | — | — |
| `0046` | [不可选块可调注释单语言代码注释Agent](nodes/0046-code-comment-agent_batch_single-language.yaml) | 2026-11-25 | 2027-11-25 | 待复核 | — | — | — |
| `0003` | [AI电子鼻（通用气味识别硬件创业）](nodes/0003-electronic-nose-ai.yaml) | 2026-10-29 | 2028-01-01 | 待复核 | — | — | — |
| `0047` | [不可选块固定注释单语言代码注释Agent](nodes/0047-batch_single-language_fixed.yaml) | 2026-11-25 | 2028-05-25 | 待复核 | — | — | — |
| `0008` | [AI游戏修改器及其平台](nodes/0008-ai-game-modifier-platform.yaml) | 2026-11-05 | 2028-11-05 | 待复核 | — | — | — |
| `0009` | [AI生成红色题材中小体量视觉小说](nodes/0009-ai-red-visual-novel.yaml) | 2026-11-05 | 2028-11-05 | 待复核 | — | — | — |
| `0006` | [开源仓库AI视频生成器](nodes/0006-oss-video-generator.yaml) | 2026-11-02 | 2029-11-02 | 待复核 | — | — | — |
| `0007` | [周历史简报及档案网站](nodes/0007-internet-weekly-archive.yaml) | 2026-11-04 | 2029-11-04 | 待复核 | — | — | — |
| `0014` | [开源知识库节点AI视频生成器](nodes/0014-knowledge-base-ai-video-generator.yaml) | 2026-11-08 | 2029-11-08 | 待复核 | — | — | — |
