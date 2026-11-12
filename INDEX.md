# 点子索引与死因统计

> 本文件由 `scripts/generate_index.py` 根据 `nodes/*.yaml` 自动生成，请勿手工维护其中的节点数据。
> 同一批节点重复生成的内容一致；修改节点后应重新生成本文件。

## 总览

- 节点：18 个
- 死法：86 条
- 复活候选：4 个
- 已复活：6 个

## 节点索引

| 标题 | id | 档案类型 | 复活状态 | 领域 | 子领域 | 死法类型 | 重启预算 | 审核日期 | 死因保质期 |
|---|---|---|---|---|---|---|---|---|---|
| [AI联合平台](nodes/ai-federation-platform.yaml) | `ai-federation-platform` | 预审 | 死透 | 人工智能 | 多智能体协作平台 | 巨头碾压、冷启动死锁、执行人限制、理论证伪 | 高 | 2026-10-30 | 2027-04-30 |
| [AI游戏修改器及其平台](nodes/ai-game-modifier-platform.yaml) | `ai-game-modifier-platform` | 预审 | 死透 | 游戏 | 单机游戏Mod与修改器 | 钱算不平、巨头碾压、冷启动死锁、信任成本 | 中 | 2026-11-05 | 2028-11-05 |
| [AI法律漏洞搜寻与意见提交](nodes/ai-legal-loophole-hunter.yaml) | `ai-legal-loophole-hunter` | 预审 | 死透 | 法律服务 | 法律科技、AI法律咨询 | 巨头碾压、政策风险、信任成本、执行人限制、理论证伪 | 中 | 2026-10-31 | 2027-01-01 |
| [AI立法意见辅助提交](nodes/ai-legal-loophole-hunter_legislation-feedback.yaml) | `ai-legal-loophole-hunter_legislation-feedback` | 预审 | 死透 | 政务服务 | 立法参与、公民科技 | 伪需求、巨头碾压、执行人限制、理论证伪 | 低 | 2026-10-30 | 2027-06-30 |
| [AI生成红色题材中小体量视觉小说](nodes/ai-red-visual-novel.yaml) | `ai-red-visual-novel` | 预审 | 复活候选 | 游戏 | 互动叙事与红色文化 | 钱算不平、政策风险、信任成本、条件已死 | 中 | 2026-11-05 | 2028-11-05 |
| [AI拦截仿真对话反诈Agent](nodes/ai-scam-interception-agent.yaml) | `ai-scam-interception-agent` | 预审 | 已复活 | 网络安全 | 对话式反诈蜜罐与威胁情报 | 钱算不平、巨头碾压、政策风险、信任成本、条件已死、执行人限制 | 高 | 2026-11-10 | 2027-11-10 |
| [颈深淋巴管／结—静脉吻合术治疗阿尔茨海默病](nodes/alzheimer-dclva-surgery.yaml) | `alzheimer-dclva-surgery` | 验尸 | 复活候选 | 医疗健康 | 阿尔茨海默病创新疗法与显微外科 | 钱算不平、政策风险、信任成本、执行人限制 | 高 | 2026-11-07 | 2027-11-07 |
| [开源arXiv有趣论文发现及总结Agent插件](nodes/arxiv-interesting-paper-discovery-summary-agent-plugin.yaml) | `arxiv-interesting-paper-discovery-summary-agent-plugin` | 预审 | 已复活 | 人工智能 | 预印本发现与个性化科研信息筛选Agent | 伪需求、钱算不平、巨头碾压、政策风险、信任成本、条件已死、执行人限制 | 低 | 2026-11-12 | 2027-11-12 |
| [开源哔哩哔哩自主宠物鲸Agent插件](nodes/bilibili-autonomous-pet-whale-agent-plugin.yaml) | `bilibili-autonomous-pet-whale-agent-plugin` | 预审 | 已复活 | 人工智能 | 内容平台自主Agent与角色化个人信息筛选 | 伪需求、钱算不平、政策风险、信任成本、条件已死、执行人限制 | 低 | 2026-11-11 | 2027-11-11 |
| [云端全流程科研自动化Agent](nodes/cloud-research-automation-agent.yaml) | `cloud-research-automation-agent` | 预审 | 已复活 | 人工智能 | 科研智能体与云端研究工作流 | 钱算不平、巨头碾压、政策风险、信任成本、条件已死 | 高 | 2026-11-07 | 2027-11-07 |
| [大肥鱼赛博墓地](nodes/dafeiyu-cyber-cemetery.yaml) | `dafeiyu-cyber-cemetery` | 预审 | 死透 | 文娱 | 网络meme | 伪需求、政策风险、季节魔咒、执行人限制 | 低 | 2026-10-26 | 2026-11-29 |
| [AI电子鼻（通用气味识别硬件创业）](nodes/electronic-nose-ai.yaml) | `electronic-nose-ai` | 预审 | 复活候选 | 硬科技 | 传感器、AI嗅觉 | 巨头碾压、信任成本、条件已死、执行人限制 | 高 | 2026-10-29 | 2028-01-01 |
| [基于概率学模型的高考志愿填报服务（C端）](nodes/gaokao-zhiyuan-ai.yaml) | `gaokao-zhiyuan-ai` | 预审 | 死透 | 教育 | 高考升学，志愿填报 | 钱算不平、巨头碾压、政策风险、季节魔咒、信任成本 | 中 | 2026-10-28 | 2027-07-15 |
| [开源GitHub有趣仓库发现Agent插件](nodes/github-interesting-repository-discovery-agent-plugin.yaml) | `github-interesting-repository-discovery-agent-plugin` | 预审 | 已复活 | 人工智能 | 开源软件发现与个人信息筛选Agent | 伪需求、钱算不平、巨头碾压、信任成本、条件已死、执行人限制 | 低 | 2026-11-12 | 2027-11-12 |
| [周历史简报及档案网站](nodes/internet-weekly-archive.yaml) | `internet-weekly-archive` | 预审 | 死透 | 内容与媒体 | 网络文化档案 | 伪需求、钱算不平、巨头碾压、执行人限制 | 低 | 2026-11-04 | 2029-11-04 |
| [开源知识库节点AI视频生成器](nodes/knowledge-base-ai-video-generator.yaml) | `knowledge-base-ai-video-generator` | 预审 | 已复活 | 内容与媒体 | 开源创作工具与知识传播 | 钱算不平、巨头碾压、政策风险、信任成本、条件已死 | 低 | 2026-11-08 | 2029-11-08 |
| [长期伴随学习辅助AI](nodes/long-term-learning-companion-ai.yaml) | `long-term-learning-companion-ai` | 预审 | 复活候选 | 人工智能 | 长期个人记忆与智能教育 | 钱算不平、巨头碾压、政策风险、信任成本、执行人限制 | 高 | 2026-11-07 | 2027-11-07 |
| [开源仓库AI视频生成器](nodes/oss-video-generator.yaml) | `oss-video-generator` | 预审 | 死透 | 开发者工具 | 内容生成与项目推广 | 伪需求、钱算不平、巨头碾压、执行人限制 | 低 | 2026-11-02 | 2029-11-02 |

## 按死法类型统计

死法条数按死法条目计数；涉及节点数按出现该死法类型的不同节点计数。

| 死法类型 | 死法条数 | 涉及节点数 |
|---|---:|---:|
| 伪需求 | 7 | 7 |
| 钱算不平 | 13 | 13 |
| 巨头碾压 | 14 | 14 |
| 政策风险 | 11 | 11 |
| 季节魔咒 | 2 | 2 |
| 冷启动死锁 | 2 | 2 |
| 信任成本 | 13 | 13 |
| 条件已死 | 8 | 8 |
| 执行人限制 | 13 | 13 |
| 理论证伪 | 3 | 3 |

## 按复活状态统计

| 复活状态 | 节点数 |
|---|---:|
| 死透 | 8 |
| 复活候选 | 4 |
| 已复活 | 6 |

## 按档案类型统计

| 档案类型 | 节点数 |
|---|---:|
| 预审 | 17 |
| 验尸 | 1 |
