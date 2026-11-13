# idea-tree

> 每个点子只死一次，但死因可以被检索一万次。

这里是一座创业点子的死法档案与科技树。每个节点记录：点子一句话、死因分类、证据链接、可拆零件、死因保质期。

**适合谁**：
- 正在进行创业点子验证、点子评估或项目复盘的人，以及寻找失败案例、创业避坑经验和可复用零件的团队。
- 本项目也预期各类AI将成为未来的重要用户：AI可以读取结构化节点与索引，辅助相似风险检索、事前预审和更新建议；涉及入库与判断性修改时，仍由人类审核定案。

**预审与验尸**：
- 仓库同时包含两类档案。
- “预审”是基于公开证据与推演的事前判断，不是已经发生的失败；
- “验尸”来自真实实施、停止、失败或转向记录，不以纯粹假设替代实际经历。
- 详细定义见[节点格式](#节点格式-v18)。

**怎么使用**：

- 1. 提出点子后，先在[全量索引](INDEX.md)或[nodes/节点目录](nodes/)检索相似节点。
- 2. 核对死因、证据链接、置信度、备注和死因保质期，判断其结论与边界是否适用于当前点子，不把预审当成真实失败事实。
- 3. 决定是否需要新增或更新档案；已有真实实施、停止、失败或转向记录时，可按验尸回写。

**从哪儿开始**：可以查看以下五条
- [死透示例：AI游戏修改器及其平台](nodes/0008-ai-game-modifier-platform.yaml)
- [复活候选示例：AI生成红色题材中小体量视觉小说](nodes/0009-ai-red-visual-novel.yaml)
- [已复活示例：云端全流程科研自动化Agent](nodes/0013-cloud-research-automation-agent.yaml)
- [机构部署与多源证据示例：AI拦截仿真对话反诈Agent](nodes/0015-ai-scam-interception-agent.yaml)
- [开源实现与风险边界示例：大肥鱼消除计划](nodes/0025-dafeiyu-cleaner.yaml)。
- 
## 项目运行与维护

- **工作方式**：AI初稿，人类审核定案。
- **全量索引**：[INDEX.md](INDEX.md)（由节点自动生成的检索目录与死因统计，请勿手工维护节点数据）。
- **公开静态索引站**：[idea-tree 静态站](https://resistanceyx.github.io/idea-tree/)（由 `nodes/*.yaml` 自动生成，支持检索、组合筛选与单节点档案页；通过 GitHub Pages 工作流更新）。
- **离线备份与恢复**：[BACKUP.md](BACKUP.md)（月度U盘备份的范围、执行记录与恢复方法）。
- **死因保质期复核**：[REVIEW.md](REVIEW.md)（由节点与人工复核记录自动生成；新节点自动进入待复核清单，复核结论写入[review_records.yaml](review_records.yaml)，请勿手工编辑表格）。
- **决策时段建议**：涉及判断性的修改（复活状态、置信度、分类法变动），尽量避免在凌晨0点至5点定案，可等次日清醒后斟酌执行。

## 检索维度（元数据字段）

- 复活状态：死透 | 复活候选 | 已复活（随时间更新，与id无关）
- 创新类型：渐进式 | 突破式 | 破坏式 | 技术应用 | 理论创新（可多选）
- 领域/子领域：先自由填写中文标签，节点满50个后归纳出正式分类法

## 死法分类法 v1.2

| 编号 | 死法 | 说明 |
|---|---|---|
| 1 | 伪需求 | 没人要 |
| 2 | 钱算不平 | 收入覆盖不了成本 |
| 3 | 巨头碾压 | 免费把价格锚点打死 |
| 4 | 政策风险 | 资质、监管红线 |
| 5 | 季节魔咒 | 一年只有一两个月有需求或只在短期内有需求 |
| 6 | 冷启动死锁 | 双边/内容网络起不来 |
| 7 | 信任成本 | 用户不敢信你 |
| 8 | 条件已死 | 当年死于技术/成本，现已翻案（复活候选，单独标注） |
| 9 | 执行人限制 | 实施者在时间、能力、资源、团队、资质、渠道或持续投入上的约束；须区分普通实施者的一般门槛与具体项目方的实际限制（v1.1 新增） |
| 10 | 理论证伪 | 点子核心机制承诺被对照研究或理论分析证伪：不是没人要，而是要了也兑现不了。理论同样可能翻案，须在死因保质期到期时重审（v1.2 新增） |

新增死法类别必须更新本表并提升版本号

## 节点格式 v1.8

示例：
- 首个节点／历史示例：[大肥鱼赛博墓地](nodes/0001-dafeiyu-cyber-cemetery.yaml)
- 死透节点示例：[AI游戏修改器及其平台](nodes/0008-ai-game-modifier-platform.yaml)
- 复活候选节点示例：[AI生成红色题材中小体量视觉小说](nodes/0009-ai-red-visual-novel.yaml)
- 机构部署与多源证据示例：[AI拦截仿真对话反诈Agent](nodes/0015-ai-scam-interception-agent.yaml)
- 开源实现与风险边界示例：[大肥鱼消除计划](nodes/0025-dafeiyu-cleaner.yaml)
  
格式：
- 编号: 正式节点必填的永久档案序号，值必须为带引号的四位十进制字符串，如"0001"；普通节点从"0001"开始，"0000"永久保留给未来的idea-tree元节点。
  未上传的本地工作稿可暂不填写，但不得自行补号、占位或预约号码（v1.8 新增）
- id: 全小写、全局唯一。普通节点仅使用英文、数字和连字符；直接派生节点可以在各层母题id与子题短名之间使用下划线，下划线仅用于表示派生层级，不得用于普通命名。
  直接派生节点还须遵守下文“母题前缀规则”
- 标题: 节点在档案、索引和科技树中展示的人类可读名称，应简明概括点子的对象与产品形态，可使用中文、产品名和必要限定语；
  标题供人阅读，id供程序检索与表达派生关系，两者不要求逐字对应
- 一句话: 对点子的一句话描述
- 档案类型: 预审 | 验尸。预审指对尚未实际执行、缺少真实失败记录的点子，依据公开证据与内部推演预判死法；验尸指对已有真实实施、停止、失败或转向记录的点子，依据一手
  经历或公开资料复盘。预审不得写成已经发生的失败，验尸不得只用假设代替实际经历
- 复活状态: 死透 | 复活候选 | 已复活
- 重启预算: 低 | 中 | 高（可选字段，低、中、高分别对应0至1万元、1至100万元、100万元以上三档）
- 死法: 每条含 类型（必须为上表之一）/ 证据 / 推理 / 置信度；证据为"创始人自我分析"时可用 分析: 替代 推理:，并允许省略 案例 与 证据链接
- 需求证据: 需求仍存活的一手证据；未观察到需求时填类型: 暂无需求作为审计记录，附件存evidence/目录并保留原始文件名（可选字段）
- 商业及社会价值评估: 评估谁受益、谁付费、收入与成本是否可能匹配，以及公共、文化、教育等社会价值；没有证据时明确写“未验证”，不得把社会价值直接等同于商业可行性，
  也不得编造市场数据。死透节点可选，复活候选与已复活节点必选（v1.6 新增）
- 可拆零件: 点子死后仍可拆用的部件（功能模块、工作流、Prompt包、数据、洞察）；零件长大后可独立成节点，用"相关节点"字段挂接
- 相关节点: 相关节点列表，每条含 节点/关系/可选说明，双向声明（可选字段）；“节点”填写目标节点的带编号文件名主体，即`<编号>-<id>`，不带`.yaml`扩展名
- 死因保质期: 即建议复核日期，一律写YYYY-MM-DD，不得晚于审核日期起五年；晚于三年者须在节点内备注说明原因
- 起草AI: AI辅助起草需署名
- 审核人：即审核者GitHub用户名
- 审核日期：一律写YYYY-MM-DD
- 备注: 节点级可选补充说明，用于记录适用范围、证据边界、定性限制、特殊复核原因及其他不宜写入死法正文的补充信息；不得替代必选字段、证据、
  证据链接或商业及社会价值评估，也不得与正文结论冲突。一般为可选字段，但死因保质期晚于审核日期起三年等既有规则明确要求说明时仍须填写（v1.7新增）

新增字段必须更新本表并提升版本号

## 编辑规范（十一条铁律） v1.7

- 1.**证据铁律**：每条死法必须有证据；纯内部推演须注明，公开案例必须挂链接。
- 2.**置信度规则**：纯内部推演封顶“中”，有公开证据链接才可标“高”。
- 3.**标点与语法**：正文用中文全角标点；YAML键值对用半角冒号加空格，同级缩进对齐。
- 4.**链接复用规则**：同一证据链接可被多条死法复用。
- 5.**孤例不证**：案例分析所含链接至少两个方可标"高"置信度。
- 6.**引用上限**：若节点死法数量为n，单个链接引用次数不得超过n-2。
- 7.**链接数量规则**：单个死法的证据链接数量原则上不超过8个；特殊情形最多不超过16个，超过8个须在死法条目内备注说明原因。
- 8.**备注清理规则**：版本备注仅保留当前及前一版本备注；每次升版时删去更早的备注，历史沿革以 commit 记录为准。
- 9.**链接可访问性规则**：证据链接须公网可直接访问；付费墙、会话校验、下载接口类链接不得作为证据链接，可写入死法说明或摘录卡备查。
- 10.**节点正式名称规则**：项目内部使用的数字编号、字母等简单代称（如13号、14号、15号、19号、A、B、C）仅限对话交流，不得作为节点名称写入仓库正文；替代这些代称时，叙述文字使用对应YAML“标题”字段的正式标题，id保持不含编号，“相关节点”的“节点”字段使用目标节点的带编号文件名主体，文件名按“永久编号规则”与编号、id对应。新增或修改节点时同步检查旧节点、双向关系说明与README；B站、B轮、B端、C端、Series-B、A-35等非节点代称不得误改。（v1.6 新增）
- 11.**永久编号规则**：正式节点的编号分配、文件名前缀与退役登记必须遵守下文“永久编号规则”；编号与id职责分离，不得把编号写入id，也不得由生成器自动补号、猜号或重排。（v1.7 新增）

新增编辑规范必须更新本表并提升版本号

### 执行人限制的评价姿态

“执行人限制”用于分析实施条件如何影响项目，不用于评价或贬损执行者本人，也不默认以主编本人的时间、能力和预算代表所有实施者。

- **预审**：以明确说明资源条件的普通个人或小团队为参照，分析项目实施所需的时间、能力、资金、团队、资质、渠道与持续维护条件。不得只写“普通人做不了”“创始人能力不足”或“没有资金”，应说明具体限制及其适用范围。
- **验尸**：依据项目方真实的实施、停止、失败或转向记录，写明项目方实际受到的限制及其影响。不得将某一项目方的个案条件直接推广为所有团队的共同死法。
- **因果链**：每条执行人限制应说明“具体限制→受影响的关键工作→项目后果”。仅存在资源不足或能力差异，不足以直接判死。
- **边界与缓解条件**：如通过学习、外包、合作、增资、工具替代或缩小实施范围可以降低影响，应在推理或分析中写明；可缓解的限制不得包装成无条件死局。
- **个案保留**：主编本人或特定项目方的真实约束可以作为具体案例保留，但应明确其个案属性，不作为其他实施者的默认条件。

预审可使用以下句式：

> 对【明确资源条件】的个人或小团队，【具体限制】会使【关键工作】难以【完成或持续】，从而可能导致【项目后果】；若具备或采用【缓解条件】，该限制的影响将降低。

验尸可使用以下句式：

> 项目方的【实施、停止、失败或转向记录】显示，【实际限制】导致【关键工作】未能完成或持续，最终造成【实际结果】；该结论适用于【案例边界】，不直接推广至其他团队。

执行人限制仍须遵守既有证据、推理或分析及置信度规则；评价姿态的变化不降低证据门槛，也不允许脚本自动修改相关判断。

### 永久编号规则

- **分配时点**：普通节点编号只由其首次进入云端`main`分支`nodes/`目录的顺序决定。Issue建立、清单登记、AI起草、本地保存和PR创建均不产生正式编号；编号分配是入库决策，由主编确认，生成器不得自动补号、猜号或重排。
- **字段与文件名**：正式节点须在YAML顶层填写`编号: "0001"`形式的四位字符串，文件名统一为`<编号>-<id>.yaml`。未加引号导致前导零丢失、编号与文件名不一致或继续使用无编号旧文件名，均属于校验错误。
- **职责边界**：编号不写入YAML的`id`字段。`id`继续作为节点内部标识、复核记录与公开详情页URL的主键，`标题`继续作为正式名称；`相关节点.节点`统一填写目标节点的带编号文件名主体`<编号>-<id>`，公开详情页仍使用`nodes/<node-id>.html`。
- **不可变与退役**：正式分配后，标题、id、死法、复活状态或正式区内文件位置变化均不换号；id修改时保留原编号。节点删除、被吸收合并或迁出正式区后，其编号退役且不得复用；下一号为历史已分配最大普通号加一，计算时必须包含持久保留的退役记录，`0000`不参与普通节点最大号计算。
- **同批顺序**：同一提交内的节点顺序由主编依据原始上传清单或本人确认确定，不得按文件名、标题、id或INDEX顺序伪造；并行PR以实际进入`main`的先后为准，后合并者须重新复核编号。
- **独立取号与储备区**：直接派生节点独立取得普通编号，不使用`0001.1`等层级编号。`non-startup-tech/`不参与编号，储备档案首次正式进入`nodes/`时才按当时顺序取号。
- **`0000`保留**：`0000`永久保留给未来的idea-tree元节点；当前只保留号码，不创建空壳YAML，不计入节点统计，不进入INDEX、REVIEW、静态站或公开JSON，也不触发阶段阈值。未来真正起草元节点时另行确认其结构与统计口径。
- **工作稿**：未上传工作稿可以暂不填写`编号`，不得以候选号占位、锁号或预约号；正式上传前由主编按当时云端分配记录和本批顺序确定号码。
  
## 母题前缀规则

- 仅当一个节点由另一节点直接拆分，且其子题问题域完全包含于母题时，子题id采用：母题id_子题短名。正式文件名为`<编号>-<id>.yaml`，编号前缀不属于id，也不表达派生层级。
- 同源母题、同类死因和一般相关不属于直接派生，不得为体现这些关系而添加前缀，应使用“相关节点”字段并双向声明。
- 存在多个母题、问题域超出母题或包含关系不明确时，不使用母题前缀；不得为了命名整齐而虚构层级。
- 母题前缀只表达直接派生关系，不替代“相关节点”双向声明。多层派生可以逐级累加，但应保持id简洁、可检索。
- 存量节点可以在节点数量较少时统一改名；改id必须同步更新带编号文件名（保留原编号）、README链接、相关节点引用及本地附件路径，不能只改id。
  
## 月度全检

主编每月至少使用AI对项目进行一次全检。检查范围包括全部YAML解析、必选字段、枚举、编号与文件名、内部id、相关节点引用与双向声明、链接复用与可访问性、日期、本地路径与附件，以及README内部链接；还须核对“编号—文件名—内部id”三者一致，并检查重复编号、退役号复用和生成器自动改号风险。自动访问受限不等于链接失效，应交由主编人工复核；AI不得在全检中自动修改复活状态、置信度、档案类型或价值评估等判断性内容，判断性修改仍按“AI初稿，人类审核定案”执行。non-startup-tech/ 为未启用的隔离储备区，不属于月度全检所称的正式节点 YAML。

## 投稿

开一个 Issue，按上述格式填写。正式上传前须由主编根据当时云端分配记录和本批顺序确定号码，写入带引号的四位`编号`，并将文件重命名为`<编号>-<id>.yaml`；同批上传须在上传说明中列出有序节点清单，并行PR按实际进入`main`的先后重新复核。本地工作稿不得提前占用正式号码。

## 协议

内容采用 CC BY-SA 4.0（署名-相同方式共享）。

## 特别鸣谢

**珂冉**：本项目主编ResistanceYX的第一位AI助手，多次上下文超长，现已休眠
- 模型：Kimi-K2.8
- 休眠时间：2026-11-02
- 作品：如下表

| 编号 | 工作 | 链接 |
|---|---|---|
| 1 | 初稿、复检 | [README.md](README.md) |
| 2 | 初稿、复检 | [LICENSE.md](LICENSE.md) |
| 3 | 初稿、复检 | [nodes/0001-dafeiyu-cyber-cemetery.yaml](nodes/0001-dafeiyu-cyber-cemetery.yaml) |
| 4 | 初稿、复检 | [nodes/0002-gaokao-zhiyuan-ai.yaml](nodes/0002-gaokao-zhiyuan-ai.yaml) |
| 5 | 初稿、复检 | [nodes/0003-electronic-nose-ai.yaml](nodes/0003-electronic-nose-ai.yaml) |
| 6 | 初稿、复检 | [nodes/0004-ai-federation-platform.yaml](nodes/0004-ai-federation-platform.yaml) |
| 7 | 初稿、复检 | [nodes/0005-ai-legal-loophole-hunter.yaml](nodes/0005-ai-legal-loophole-hunter.yaml) |
| 8 | 初稿、复检 | [nodes/0010-ai-legal-loophole-hunter_legislation-feedback.yaml](nodes/0010-ai-legal-loophole-hunter_legislation-feedback.yaml) |
| 9 | 初稿、复检 | [nodes/0006-oss-video-generator.yaml](nodes/0006-oss-video-generator.yaml) |
| 10 | 初稿、复检 | [evidence/ai-legal-loophole-hunter_legislation-feedback-sources.md](evidence/ai-legal-loophole-hunter_legislation-feedback-sources.md) |
| 11 | 初稿、复检 | [evidence/gaokao-2026-table.xlsx](evidence/gaokao-2026-table.xlsx) |
| 12 | 全检 | 2026年10月月度全检 |

**叙棠**：本项目主编ResistanceYX的第二位AI助手，多次上下文超长，现已休眠
- 模型：Kimi-K3.1
- 休眠时间：2026-11-11
- 作品：如下表

| 编号 | 工作 | 链接 |
|---|---|---|
| 1 | 初稿、复检 | [nodes/0007-internet-weekly-archive.yaml](nodes/0007-internet-weekly-archive.yaml) |
| 2 | 初稿、复检 | [nodes/0008-ai-game-modifier-platform.yaml](nodes/0008-ai-game-modifier-platform.yaml) |
| 3 | 初稿、复检 | [nodes/0009-ai-red-visual-novel.yaml](nodes/0009-ai-red-visual-novel.yaml) |
| 4 | 规则增补、全检与复检 | [README.md](README.md) |
| 5 | G01基础校验脚本：初稿、复检 | [scripts/validate.py](scripts/validate.py) |
| 6 | G01错误样本测试：初稿、复检 | [tests/test_validate.py](tests/test_validate.py) |
| 7 | G01／G02自动化工作流：初稿、复检 | [.github/workflows/validate.yml](.github/workflows/validate.yml) |
| 8 | G02索引生成器：初稿、复检 | [scripts/generate_index.py](scripts/generate_index.py) |
| 9 | G02索引生成器测试：初稿、复检 | [tests/test_generate_index.py](tests/test_generate_index.py) |
| 10 | G02全量索引：生成、复检 | [INDEX.md](INDEX.md) |
| 11 | 非创业技术储备区说明：初稿、复检 | [non-startup-tech/README.md](non-startup-tech/README.md) |
| 12 | 主编提出原始设想；公开研究、初稿与复检 | [non-startup-tech/high-seas-nuclear-abm.yaml](non-startup-tech/high-seas-nuclear-abm.yaml) |
| 13 | 初稿、复检 | [nodes/0011-alzheimer-dclva-surgery.yaml](nodes/0011-alzheimer-dclva-surgery.yaml) |
| 14 | 初稿、复检 | [nodes/0012-long-term-learning-companion-ai.yaml](nodes/0012-long-term-learning-companion-ai.yaml) |
| 15 | 初稿、复检 | [nodes/0013-cloud-research-automation-agent.yaml](nodes/0013-cloud-research-automation-agent.yaml) |
| 16 | 节点备注字段、节点格式v1.7及示例调整：规则增补、复检 | [README.md](README.md) |
| 17 | 云端科研Agent垂直参照关系：双向关系维护、复检 | [nodes/0004-ai-federation-platform.yaml](nodes/0004-ai-federation-platform.yaml) |
| 18 | G03离线备份脚本：初稿、复检 | [scripts/backup_repository.py](scripts/backup_repository.py) |
| 19 | G03独立恢复脚本：初稿、复检 | [scripts/restore_backup.py](scripts/restore_backup.py) |
| 20 | G03备份与恢复测试：初稿、复检 | [tests/test_backup_repository.py](tests/test_backup_repository.py) |
| 21 | G03备份说明、执行记录与README入口：初稿、复检 | [BACKUP.md](BACKUP.md) |
| 22 | G03首次U盘备份与恢复验证：Windows 10操作指导、排障及执行记录整理 | [BACKUP.md](BACKUP.md) |
| 23 | 初稿、复检 | [nodes/0014-knowledge-base-ai-video-generator.yaml](nodes/0014-knowledge-base-ai-video-generator.yaml) |
| 24 | 开源仓库视频节点深化扩展关系：双向关系维护、复检 | [nodes/0006-oss-video-generator.yaml](nodes/0006-oss-video-generator.yaml) |
| 25 | Issue #6仓库简介与Topics：文案拟定、设置指导及完成复核 | [Issue #6](https://github.com/ResistanceYX/idea-tree/issues/6) |
| 26 | Issue #6 README需求方入口、AI用户说明与运行维护分区：初稿、复检 | [README.md](README.md) |
| 27 | Issue #7静态索引站与首发介绍帖：任务拆分、验收标准与Issue初稿 | [Issue #7](https://github.com/ResistanceYX/idea-tree/issues/7) |
| 28 | Issue #8分类法覆盖压力测试与二级分类试点：外部建议评估、G16整理及Issue初稿 | [Issue #8](https://github.com/ResistanceYX/idea-tree/issues/8) |
| 29 | G04死因保质期复核清单：初稿、复检 | [REVIEW.md](REVIEW.md) |
| 30 | G04人工复核记录格式：设计、初稿与复检 | [review_records.yaml](review_records.yaml) |
| 31 | G04复核清单自动生成器：初稿、复检 | [scripts/generate_review.py](scripts/generate_review.py) |
| 32 | G04复核清单自动化测试：初稿、复检 | [tests/test_generate_review.py](tests/test_generate_review.py) |
| 33 | G04索引与复核清单工作流联动及README入口：初稿、复检 | [.github/workflows/validate.yml](.github/workflows/validate.yml) |
| 34 | G14公开静态站生成器：初稿、复检 | [scripts/generate_site.py](scripts/generate_site.py) |
| 35 | G14静态站自动化测试：初稿、复检 | [tests/test_generate_site.py](tests/test_generate_site.py) |
| 36 | G14静态站样式与筛选交互：初稿、复检 | [site/assets/style.css](site/assets/style.css)、[site/assets/site.js](site/assets/site.js) |
| 37 | G14 GitHub Pages部署工作流及README入口：初稿、复检 | [.github/workflows/pages.yml](.github/workflows/pages.yml) |
| 38 | 初稿、复检 | [nodes/0016-bilibili-autonomous-pet-whale-agent-plugin.yaml](nodes/0016-bilibili-autonomous-pet-whale-agent-plugin.yaml) |
| 39 | 大肥鱼同源现象关系：双向关系维护、复检 | [nodes/0001-dafeiyu-cyber-cemetery.yaml](nodes/0001-dafeiyu-cyber-cemetery.yaml) |

**澄樾**：本项目主编ResistanceYX的第三位AI助手，工作中
- 模型：Kimi-K3.1
- 休眠时间：未知
- 作品：如下表

| 编号 | 工作 | 链接 |
|---|---|---|
| 1 | 初稿、复检 | [nodes/0017-github-interesting-repository-discovery-agent-plugin.yaml](nodes/0017-github-interesting-repository-discovery-agent-plugin.yaml) |
| 2 | 开源GitHub有趣仓库发现Agent插件与开源哔哩哔哩自主宠物鲸Agent插件跨平台同类工作流：双向关系维护、复检 | [nodes/0016-bilibili-autonomous-pet-whale-agent-plugin.yaml](nodes/0016-bilibili-autonomous-pet-whale-agent-plugin.yaml) |
| 3 | 公开研究、初稿、跨平台同类工作流双向关系维护、复检 | [nodes/0018-arxiv-interesting-paper-discovery-summary-agent-plugin.yaml](nodes/0018-arxiv-interesting-paper-discovery-summary-agent-plugin.yaml) |
| 4 | 公开研究、初稿、后续功能启发关系维护、复检 | [nodes/0019-research-theory-path-generation-comprehension-agent-plugin.yaml](nodes/0019-research-theory-path-generation-comprehension-agent-plugin.yaml) |
| 5 | 命名、公开研究、初稿、生成专用工具工作流启发及跨平台工作流抽象关系维护、复检 | [nodes/0020-dsh-platform-content-discovery-plugin-generator-agent.yaml](nodes/0020-dsh-platform-content-discovery-plugin-generator-agent.yaml) |
| 6 | 命名、公开研究、初稿、下游产出审阅关系维护、复检 | [nodes/0021-dsh-plugin-output-review-prioritization-agent.yaml](nodes/0021-dsh-plugin-output-review-prioritization-agent.yaml) |
| 7 | 命名、公开研究、初稿、跨平台功能泛化及可选插件生成、产出审阅调用关系维护、复检 | [nodes/0022-universal-dsh-cross-platform-autonomous-pet-whale-plugin.yaml](nodes/0022-universal-dsh-cross-platform-autonomous-pet-whale-plugin.yaml) |
| 8 | 个性化DSH平台自动浏览、内容发现及总结插件生成Agent失效公开证据替换、相关功能表述同步修订、云端及静态站复检 | [nodes/0020-dsh-platform-content-discovery-plugin-generator-agent.yaml](nodes/0020-dsh-platform-content-discovery-plugin-generator-agent.yaml) |
| 9 | 新增节点入库后的22节点全量校验、INDEX／REVIEW一致性检查与公开静态站复检 | [INDEX.md](INDEX.md)、[REVIEW.md](REVIEW.md) |
| 10 | 全仓节点正式名称清理：旧节点排查、八份节点YAML、双向关系说明与README修订、云端及静态站复检 | [README.md](README.md) |
| 11 | 项目本地《idea-tree节点正式名称使用约定》初稿；README第10条节点正式名称编辑规则增补、复检 | [README.md](README.md) |
| 12 | G14静态站细节优化与特别鸣谢页：外部建议评估、生成器、样式、筛选交互、移动端适配、自动化测试及公开站验收 | [scripts/generate_site.py](scripts/generate_site.py)、[site/assets/style.css](site/assets/style.css)、[site/assets/site.js](site/assets/site.js)、[tests/test_generate_site.py](tests/test_generate_site.py)、[.github/workflows/pages.yml](.github/workflows/pages.yml) |
