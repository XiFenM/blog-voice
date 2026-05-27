# 5 个月英语提升计划：听力 / 口语优先（软件工程师 · AI Infra 方向）

## 0. 整体设计

### 我是谁、要解决什么

- 已工作的软件工程师，方向是 AI Infra（本仓库 `blog-voice` 就是为这件事服务的）。
- 六级 + 考研英语二 80 分，**基础不差但英文处理链没有"工程化自动化"**：读得懂、听不全、说不出。
- 优先级：**听力 > 口语 > 阅读 > 写作（不作为目标）**。
- 时间预算：**工作日 60–75 min / 天**，周末可加量。
- 时间周期：**~22 周（150 天）**，刚好覆盖"美剧 150 天 + 口语课 300 集（每天 2 集）"。

### 核心策略（一句话）

> **每天分三块：固定输入（美剧 + 口语课）、可迁移输入（blog-voice 自产 AI Infra 音频 + AI Infra 播客）、即时输出（录音 + shadowing）。所有"被动听"必须配 transcript + 重复 + 模仿，否则不计入训练时长。**

### 三大反原则（哪怕只记三条也行）

1. **不要把"听了 1 小时播客"当成训练**——没有 transcript / 重复 / 跟读 / 复述，全是英语噪声浴。
2. **不要先攒输入再开口**——口语是训练出来的，不是阅读能力自然溢出的副产品。第 1 周就开始录音。
3. **不要重新背单词书**——你缺的是**技术语块（chunks）**和**听-说自动化**，不是更多孤立词。

### 5 个月路线图

| 阶段 | 周次 | 主目标 | 美剧 | 口语课 | AI Infra 听力 | 期末 checkpoint |
| --- | --- | --- | --- | --- | --- | --- |
| Week 0 | -0.5–0 | 基线测试 + 工具搭建 | 选剧 | 试听首集 | — | 基线数据归档 |
| 阶段 1 | 1–4 | 恢复手感、降挫败 | 30 集 (S1–S2) | 60 集 (Ep 1–60) | 暂不上手 | 听 BBC 6-Minute 能抓主旨 |
| 阶段 2 | 5–8 | 技术英语桥接 | 30 集 | 60 集 (61–120) | 2 集/周（轻量） | 听 Practical AI 一集能复述 3 句 |
| 阶段 3 | 9–12 | AI Infra 听力上量 | 30 集 | 60 集 (121–180) | 3 集/周（中等） | 5 min 技术 mini-talk 录音 |
| 阶段 4 | 13–16 | 真实工程师语速 | 30 集 | 60 集 (181–240) | 4 集/周（硬核） | 听 Latent Space 片段能转写 80% |
| 阶段 5 | 17–22 | 产出 + 期末测试 | 30 集 | 60 集 (241–300) | 5 集/周 | 重做 Week 0 测试 + 5 个主题 mini-talk |

---

## 1. Week 0（3–5 天）：基线测试与工具准备

### 1.1 基线测试 SOP（一次性，保留所有原始数据）

把测试结果保存在 `English-learn/baseline/week0/` 下，每月底重测一次同样的题目，对比改进。

**听力基线（3 段，每段单独打分 0–10）**

| 难度 | 材料（举例） | 任务 | 评分维度 |
| --- | --- | --- | --- |
| B1 | BBC 6 Minute English 任一集 | 盲听一遍 → 写出 3 句主旨（中/英都行） | 主旨准确度 |
| B2 | Friends S1E1 开场 3 分钟（无字幕） | 盲听一遍 → 列 5 个角色发生的事 | 细节召回率 |
| 技术 | Practical AI 任一集前 5 分钟 | 盲听一遍 → 复述讨论了什么问题 | 是否抓到主题词 |

**口语基线（2 分钟录音 × 3 个话题）**

录音保存为 `baseline/week0/speak_<topic>.m4a`。每段不写稿，直接讲，自评：

```text
1. Explain what a GPU is, in 2 minutes.
2. Walk through a recent bug you debugged, in 2 minutes.
3. Describe how an LLM does inference at high level, in 2 minutes.
```

自评 4 项（每项 1–5 分）：

| 维度 | 含义 |
| --- | --- |
| 流畅度 | 长停顿（>3s）次数 / 分钟 |
| 准确度 | 语法 / 用词错误数 |
| 信息密度 | 2 分钟说了多少有效要点 |
| 技术感 | 用到的技术 chunk 数（trade-off / fall back to / under the hood / ...） |

**阅读基线（1 篇 ~1200 词）**

材料：本仓库 `articles/pytorch-internals/source.txt` 的前 1200 词（或任一你想读的 AI Infra 博客）。

记录：

- 阅读时间（秒）→ wpm = 1200 × 60 / 秒数
- 卡顿次数（停下来想/查词的瞬间）
- 主旨 3 句话总结准确度

### 1.2 工具栈（固定，不要再换）

| 用途 | 工具 | 备注 |
| --- | --- | --- |
| 间隔重复 | **Anki**（桌面 + 手机） | 准备一个 deck `AI-infra-chunks`，每天最多新增 5 张 |
| 查词 | **Cambridge Dictionary**（首选） + **Oxford Learner's** | 不再开第三个 |
| 真实发音 | **YouGlish** | 输入短语，看 YouTube 真实视频里怎么说 |
| 字幕 | **Language Reactor**（Chrome 扩展） | Netflix/YouTube 双语字幕、按句重听、导出 |
| 录音 | 手机录音 App（不限） | 文件名 `YYYY-MM-DD_<topic>.m4a` |
| 听写 | Whisper（本仓库已经能跑） | 用 fish.audio 或自带 ASR 做听写对照 |
| 节拍器/打卡 | **多邻国**（10 min/天） | 不为学，为续 streak，建立"每日英语"习惯 |

### 1.3 选定美剧与口语课

**美剧（如果"听懂美剧150天"已确定）**：直接用。建议第一部选 **Friends** 或 **Modern Family**，理由是：

- 单集 22 min 左右（剪掉广告），适合 45 min 时间块做 1 集精听。
- 句长短、生活场景、语速适中，B1–B2 都能撑住。
- 没有大量技术术语干扰，专注听力解码本身。

不要从 The Office / Silicon Valley / The Bear 开始——语速过快或行业黑话过多，会反复挫败。

**口语课（如果"口语系统课300集"已确定）**：直接用。要求：

- 每集结束**当场录音 60 秒**复述课程要点（哪怕磕磕巴巴），否则课程白上。
- 每周末把 5 天的 5 段录音回听一次，标 1 件下周要改的事（**只标 1 件**）。

### 1.4 项目侧准备（一次性）

```bash
# 把现成的 AI Infra 文章音频备好，作为日常听力的"自产弹药"
uv run blog-voice article pipeline pytorch-internals --enhance
uv run blog-voice article lrc pytorch-internals --translate-zh --include-metadata

# 听 LRC 字幕版（用任意支持 LRC 的播放器，比如 Apple Music / netease）
# merged.wav + subtitle.lrc 一起拖进播放器
```

后续阶段 2 起，每 2–3 周用 `blog-voice article add` 加一篇新 AI Infra 文章，**自产 transcript + audio**，这是这个项目对你英语训练最大的杠杆。

---

## 2. 每日时间块（工作日 60–75 min）

> **铁律**：每天先做"核心 25 min"，再做"输入 30 min"，最后做"复盘 10 min"。顺序不能反——疲劳时英语解码会快速劣化，必须把高产出动作放前面。

### 2.1 主时间块（必须做，60 min）

| 时段 | 时长 | 内容 | 备注 |
| --- | --- | --- | --- |
| 早 / 通勤前 | 10 min | **多邻国** | 不为学，为热身 + streak |
| 主动训练 1 | 30 min | **口语系统课 2 集** + 每集结束录音 60s | 录音文件归档 |
| 主动训练 2 | 15 min | **blog-voice / AI Infra 听力 3 遍法**（见 §3.3） | 5–8 min 片段反复 |
| 复盘 | 5 min | 当天新增 ≤5 张 Anki 卡 + 复习到期卡 | 卡片模板见 §4 |

### 2.2 副时间块（强烈推荐，15 min；时间紧可砍）

| 时段 | 时长 | 内容 |
| --- | --- | --- |
| 午休 / 晚饭后 | 15 min | **美剧 1 集**先看一遍（中英字幕都开，纯娱乐流畅看完）。当天晚上或次日做精听段，见 §3.1 |

**美剧"流畅看 + 次日精听"的拆法**：把 45 min 美剧拆成两段——第一遍 22 min 当娱乐（中英字幕），降低挫败；次日早上花 15–20 min 挑 1–2 个片段做 §3.1 的精听 SOP。这样 60–75 min 的预算就够了。

### 2.3 散时（不占主时间块，但记得用）

通勤、走路、运动、做饭、排队时，循环播放：

- **本仓库自产的 AI Infra 音频**（merged.wav）→ 熟悉技术语块发音
- AI Infra 中文播客（阶段 1–2 用，建立背景知识）→ 见 §3.3
- 当周 Friends 已看集的纯音频版（不看画面）→ 检验是否真的听懂

散时听**不算训练**，但能保持耳朵热度。

### 2.4 周末加量（每周日 60 min）

| 内容 | 时长 |
| --- | --- |
| 5 min mini-talk 录音（本周一个 AI Infra 主题） | 10 min |
| 回听本周 5 段口语课课后录音，标 1 件改进 | 10 min |
| 重听本周 1 段 AI Infra 播客片段（深度 shadowing） | 20 min |
| 整理 Anki 卡片（删冗余、补例句） | 10 min |
| 写本周打卡数据（§6.1 表格） | 10 min |

---

## 3. 四套核心练习 SOP（要练熟，不要每次想流程）

### 3.1 美剧精听 SOP（每周 5 次 × 15–20 min）

不是看剧，是**用剧做听力解码训练**。选片段 1–2 min，**只挑你想反复听的那段**（爆笑梗 / 关键情节 / 信息密集对话）。

```text
第 1 遍：盲听（无字幕，原速）          → 抓主题，列出听清的 3 句
第 2 遍：盲听（无字幕，0.85x）          → 标出"认识但没听出来"的词
第 3 遍：英文字幕 + 原速                → 对照漏洞，理解 idiom / 缩读 / 连读
第 4 遍：跟读 2 句 × 各 3 次（不停顿） → 模仿重音 + 停顿 + 语调（不强求口音）
第 5 遍：关字幕复述这段在讲什么（30s）  → 转化为输出
```

**"认识但没听出来"** 的词最值钱——把它们整理成 Anki 卡（前面：原句音频片段；后面：transcript + 你的解释）。

### 3.2 口语系统课消化 SOP（每集 15 min 课程 + 5 min 课后操作）

| 步骤 | 时长 | 操作 |
| --- | --- | --- |
| 听课 | 12 min | 跟着课程节奏走 |
| 课中标记 | (顺手) | 标 1 个本集"我以后想用"的表达 |
| 课后录音 | 60 s | 关掉课程，用本集教的表达造 2 句话，录下来 |
| 写卡 | 60 s | 把本集 1 个表达做成 Anki 卡（模板见 §4） |
| （周日批量回听） | — | 周日一次性听完本周 5 段录音 |

**关键**：不要听完两集就关掉。**录音 60s** 是把课程从"知道"变成"会用"的唯一桥梁。

### 3.3 AI Infra 听力"3 遍法"（每周 2→5 集递增）

材料阶段性升级，每阶段先用低难度 4 集打底，再升级：

| 阶段 | 主推材料 | 每集时长 | 集数/周 |
| --- | --- | --- | --- |
| 1 (1–4 周) | BBC 6 Minute English（任意主题） | 6 min | 不算 AI Infra，只做听力恢复 |
| 2 (5–8 周) | Practical AI（前 5–10 min 截选） | 5–10 min | 2 |
| 3 (9–12 周) | Latent Space 入门集 + a16z《Building the Real-World Infra for AI》 | 10–20 min | 3 |
| 4 (13–16 周) | TWIML《How to Engineer AI Inference Systems》、Kubernetes Podcast《LLM-D》 | 整集 | 4 |
| 5 (17–22 周) | Dwarkesh《Dylan Patel on 3 bottlenecks》、No Priors《Jensen Huang on AI Chip Design》 | 整集 | 5 |

每集**只取 5–10 min 片段**（除非整集才 6 min），不要"听完一整集"自我感动。

```text
第 1 遍：盲听 5–10 min                 → 主题 + 嘉宾 + 核心论点（1 句话）
第 2 遍：开 transcript 同步听          → 标"认识但没听出来"的技术语块（≥3 个）
第 3 遍：选 60–90s 做 shadowing × 3   → 重点是术语发音 + 句子节奏
最后 2 min：英文复述                    → 用 §3.4 的模板
```

中文 AI Infra 播客（《十字路口》《晚点聊》《OnBoard!》）阶段 1 起作为**散时听**——它们不练英语，但补背景知识，让你阶段 3 听英文播客时不至于因为"概念不熟"而误判为"英语听不懂"。

### 3.4 录音复盘 SOP（每周 1 次 5-min mini-talk）

每周选 1 个 AI Infra 主题，从阶段 3 起每周做一次（前 8 周可以先做 2 分钟）。

**主题池（22 周用 22 个，列在这里随取）**

```text
1.  Why is GPU memory the bottleneck for LLM inference?
2.  Explain KV cache in transformer decoding.
3.  Compare data parallelism vs tensor parallelism.
4.  Walk through what happens when a single prompt hits vLLM.
5.  Why is continuous batching better than static batching?
6.  Explain prefill vs decode phases of LLM inference.
7.  What does a serving framework like Triton actually do?
8.  Compare GPU clouds (CoreWeave / Lambda / Modal) at a high level.
9.  Why is power the real bottleneck for AI data centers?
10. Walk through how Kubernetes schedules a GPU pod.
11. Explain why LLM workloads don't fit traditional K8s.
12. What is speculative decoding and why does it help?
13. Compare RAG vs fine-tuning for domain adaptation.
14. Why do vector databases need ANN indexes?
15. Explain Flash Attention in one minute.
16. What does NVLink solve that PCIe doesn't?
17. Walk through a model deployment pipeline end-to-end.
18. Why is observability hard for LLM apps?
19. Compare serverless GPU (Modal) vs reserved GPU clusters.
20. Explain the economics of training a 70B model.
21. What is an inference gateway and why do we need one?
22. Walk through your own pytorch-internals article in 5 minutes.
```

**固定骨架（背下来）**

```text
The problem is ...
The current approach is ...
The key trade-off is ...
In practice, I would ...
One thing I'm still unsure about is ...
```

**录后自检（只看 1 项，按周轮）**

| 周次 | 只检查这一项 |
| --- | --- |
| 1–4 | 是否能说满 2 min（之后升到 5 min） |
| 5–8 | 长停顿（>3s）次数是否 < 5 次 / 5min |
| 9–12 | 是否用了 ≥3 个连接词（because / however / therefore / for example） |
| 13–16 | 是否说清了 trade-off 和 constraint |
| 17–22 | 是否能不看任何提示讲完整 5 min |

---

## 4. Anki 卡片模板（每天 ≤5 张，只收 4 类）

**只收这 4 类，其他一律不进卡**：

| 类型 | 例子 |
| --- | --- |
| AI Infra 技术语块 | KV cache, prefill phase, tensor parallelism, continuous batching |
| 工程通用 chunk | fall back to, at the cost of, under the hood, edge case, reason about |
| 文章/口语连接词 | as a result, in contrast, that said, notably, more importantly |
| 听力漏洞（从美剧/播客来） | gonna / wanna / kinda / you know what I mean |

**卡片模板（cloze 填空式，不是英→中翻译）**

```text
Front:
The decode phase of LLM inference is __________ because each token depends on the previous one.

Back:
sequential / autoregressive

Example (from Latent Space S2E14, 04:32):
"...the decode phase is fundamentally sequential, which is why batching helps so much..."
```

**禁忌**：

- ❌ `obscure = 模糊的`（孤立单词 + 中文翻译）
- ❌ 一次性导入 100 张
- ❌ 漏卡 3 天以上不补——错过的卡比错的卡杀伤大

---

## 5. 5 个月分阶段详表

### 阶段 1（Week 1–4）：恢复手感，降挫败

**目标**：建立每日英语习惯，让英文重新成为日常输入；不追求难度。

**周节奏**

| 星期 | 工作日核心 | 周末加量 |
| --- | --- | --- |
| 一 | 多邻国 10 + 口语课 2 集 30 + 美剧前一晚 1 集精听段 15 + 复盘 5 | — |
| 二 | 同上，美剧换新一集前一晚的段 | — |
| 三 | 同上 | — |
| 四 | 同上 | — |
| 五 | 同上 | — |
| 六 | 多邻国 10 + 口语课 2 集 + **新看美剧 2 集**（流畅看，不精听） | — |
| 日 | §2.4 周末加量（60 min） | ✓ |

**阶段 1 数量目标**

- 美剧 30 集（Friends S1 + S2 前半）
- 口语课 60 集（每集课后 60s 录音 = 60 段录音）
- Anki 总卡数 ≤ 100 张
- AI Infra 听力暂不上手
- 散时听：本仓库 `pytorch-internals/merged.wav` 重复 ≥ 3 轮

**阶段 1 末 checkpoint（Week 4 末测）**

- [ ] BBC 6 Minute English 任一集，盲听后能复述 3 句主旨
- [ ] 60s 录音能稳定说满，不超过 3 次长停顿
- [ ] Anki 卡平均每天复习 ≥ 10 张

### 阶段 2（Week 5–8）：技术英语桥接

**目标**：让 AI Infra 词汇进耳朵；blog-voice 开始产出第二篇文章。

**新动作**

- **AI Infra 听力上手 2 集/周**：Practical AI 前 5–10 min 截选，按 §3.3 3 遍法
- **再产 1 篇 AI Infra 文章**：用 `blog-voice article add` 加一篇短文（建议 1500–2500 词，比如 vLLM 官方博客一篇）→ pipeline 跑完 → 散时听 + 周末做精听段
- **Anki 加入"AI Infra 技术语块"分类**：每周 ≥ 10 个新语块

**阶段 2 末 checkpoint（Week 8 末测）**

- [ ] Practical AI 一集（5 min 片段），盲听后能复述 3 句技术要点
- [ ] 2 min 技术 mini-talk 录音能稳定说满
- [ ] Anki 技术语块卡 ≥ 60 张

### 阶段 3（Week 9–12）：AI Infra 听力上量

**目标**：进入真实工程师播客（非"学习材料"），首次做 5 min mini-talk。

**新动作**

- AI Infra 听力升到 **3 集/周**，材料切到 Latent Space 入门集（推荐《Modal: Truly Serverless Infra for AI Engineers》）+ a16z《Building Real-World Infrastructure for AI》
- 第一次完整 **5 min mini-talk** 录音，主题从 §3.4 主题池抽
- 再产 1 篇 AI Infra 文章（累计 3 篇）

**阶段 3 末 checkpoint（Week 12 末测）**

- [ ] Latent Space 任意 10 min 片段，开 transcript 听一遍后能复述 5 句要点
- [ ] 5 min mini-talk 全程录音，长停顿 < 5 次
- [ ] 自评对比 Week 0 基线：阅读 wpm 提升 ≥ 20%

### 阶段 4（Week 13–16）：真实工程师语速

**目标**：硬刚整集 AI Infra 播客；开始处理嘉宾的口音差异。

**新动作**

- AI Infra 听力升到 **4 集/周**，材料：TWIML《How to Engineer AI Inference Systems》、Kubernetes Podcast《LLM-D, with Clayton Coleman and Rob Shaw》、Software Engineering Daily 任意 AI Infra 单集
- 每周 mini-talk 升级要求：必须用 ≥ 3 个连接词、≥ 2 个技术 chunk
- 美剧升级（可选）：Friends 看完转 Modern Family / The Big Bang Theory（注：The Big Bang Theory 有大量科学术语，适合你）

**阶段 4 末 checkpoint（Week 16 末测）**

- [ ] TWIML 一集（5 min 片段），盲听后能写出 5 句要点（写下来，不只是脑内复述）
- [ ] 5 min mini-talk 录音让 ChatGPT/Claude 转写后，对照原意保真度 ≥ 80%

### 阶段 5（Week 17–22）：产出 + 期末测试

**目标**：能用英文讲 AI Infra；重做 Week 0 基线，量化进步。

**新动作**

- AI Infra 听力升到 **5 集/周**，材料：Dwarkesh《Dylan Patel on 3 bottlenecks》、No Priors《Jensen Huang on AI Chip Design》、Latent Space 难集
- **每周 1 个主题 mini-talk**（5 集 × 5 主题，覆盖 §3.4 列表前 5 个）
- **Week 22 末重做 Week 0 三项基线测试**，所有数据归档到 `English-learn/baseline/week22/`，对比写一份 1 页总结

**阶段 5 末 checkpoint（Week 22）**

- [ ] 听力基线 3 段平均分提升 ≥ 50%
- [ ] 口语基线 2 分钟录音，长停顿 < 3 次 / 2 min
- [ ] 阅读基线 wpm 提升 ≥ 50%
- [ ] Anki 总卡 ≥ 400 张，其中技术语块 ≥ 200 张
- [ ] 22 个 mini-talk 录音全部归档

---

## 6. 打卡 + 数据追踪

### 6.1 周打卡表（每周日填，存在 `English-learn/weekly/week_NN.md`）

```markdown
# Week NN (YYYY-MM-DD ~ YYYY-MM-DD)

## 完成情况
- 美剧集数：__ / 7
- 口语课集数：__ / 14（课后录音段数：__）
- AI Infra 听力集数：__
- blog-voice 新增文章：__
- mini-talk 录音：是 / 否
- Anki 新增卡：__，复习卡：__

## 本周一个"听见的高光时刻"
（一句具体的：哪个词突然不用翻译就听懂了 / 哪个 chunk 第一次用出来了）

## 下周只改一件事
（不超过一句话；只标 1 件）
```

### 6.2 月度对比（每月末填）

| 月份 | 听力基线均分 | 口语 2min 长停顿 | 阅读 wpm | Anki 总卡 | 最大进步点 |
| --- | --- | --- | --- | --- | --- |
| Month 0 (Week 0) | _ | _ | _ | _ | — |
| Month 1 (Week 4) | _ | _ | _ | _ | _ |
| Month 2 (Week 8) | _ | _ | _ | _ | _ |
| Month 3 (Week 12) | _ | _ | _ | _ | _ |
| Month 4 (Week 16) | _ | _ | _ | _ | _ |
| Month 5 (Week 22) | _ | _ | _ | _ | _ |

### 6.3 偷懒红线

任何一项触发，下一周必须降难度 + 砍量 25%：

- 连续 3 天没碰英语（多邻国不算）
- 周打卡完成率 < 50%
- 周日复盘录音连续 2 周没做

---

## 7. 替代方案对比（你已选课程的备份方案）

### 7.1 「听懂美剧150天」的替代：DIY 美剧精听方案

**优点**：免费，材料完全自选，可以挑你真正喜欢的剧（兴趣驱动 > 任何方法论）。
**缺点**：没人帮你拆段、没标重点，全靠自律和 SOP（§3.1）。

如果走 DIY：

| 阶段 | 推荐剧 | 难度 | 理由 |
| --- | --- | --- | --- |
| 1–2 | **Friends**（10 季） | B1–B2 | 句子短、生活场景、笑声提示节奏 |
| 3–4 | **Modern Family** | B2 | 家庭场景 + 略快语速 + 一点工作 jargon |
| 5 | **The Big Bang Theory** | B2+ | 科学术语 + 快语速，过渡到技术口音 |
| 进阶（不在 22 周内） | **Silicon Valley** / **The Bear** | C1 | 真实工程师/厨房高强度对话，建议 22 周后再上 |

**关键**：不要换太勤。1 部剧至少看完 1 季再换，**重复的角色/场景/口头禅才是耳朵的"训练集"**。

### 7.2 「口语系统课300集」的替代：BBC LE + TOEFL Speaking + Shadowing 三件套

**优点**：完全免费，每天可控在 20–30 min。
**缺点**：没有系统化课程递进，需要自己把内容串起来。

| 时间 | 内容 |
| --- | --- |
| 10 min | **BBC 6 Minute English** 一集（音频 + transcript 都有） |
| 10 min | **TOEFL Speaking Independent Task** 题目 → 自录 1 min 回答（题库免费） |
| 5–10 min | **Shadowing** TED-Ed 或 Software Engineering Radio 任意 1 min 片段 |

**推荐何时考虑替代**：如果原口语课进度跟不上（每天 30 min 太满）、或课程内容偏日常聊天而你想要更工程/技术化的输出训练，可以换掉一半（保留每天 1 集课程 + 10 min TOEFL Speaking 输出）。

### 7.3 多邻国的备份：Anki + 散时听本仓库自产音频

多邻国主要价值是**心理 streak**，不是真的提升。如果哪天觉得它在浪费时间，直接用"每天打开 Anki 复习一次"代替即可——本质都是"维持每日英语接触感"。

---

## 8. 不要做的事（清单）

- ❌ **同时学多个口语课**——选定一个跟到底，反复变换会让"开口"重新变成"挑选课程"的拖延。
- ❌ **听播客不看 transcript**——播客没 transcript 的，直接跳过，市面上有 transcript 的 AI Infra 播客很多。
- ❌ **每篇技术文章都精读**——精读提高上限，泛读提高流畅度。AI Infra 文章里只挑你**真的想用在工作里**的那 1/3 精读。
- ❌ **追求口音像 native**——重点是重音清楚、句子能连起来、技术 chunk 用得准。
- ❌ **背 GRE / 雅思词表**——你已经过六级了，缺的是 chunks 不是单词。
- ❌ **每天换学习计划**——计划改超过 2 次，问题就不是计划，是焦虑。计划允许在每月末 review 时调整 1 次。

---

## 9. 一句话总结

> **你不是在"学英语"。你是在用 5 个月时间，把英语装到你 AI Infra 工程师工作的运行环境里——以后听 Latent Space、读 vLLM 文档、用英文解释 KV cache，都不再需要手动切换"中文/英文"模式。**

每天 60–75 min，22 周，错过 1 天可以，错过 1 周就得在下一周补一次复盘——但不要追加学习量。**断链才是最大的失败模式**。

---

## 附录 A：本仓库与英语训练的集成点

| 文件/命令 | 作用 |
| --- | --- |
| `uv run blog-voice article add <slug>` | 加新 AI Infra 文章入库 |
| `uv run blog-voice article pipeline <slug> --enhance` | 一键跑 split + enhance + tts + merge + lrc |
| `articles/<slug>/merged.wav` | 散时听的主音频 |
| `articles/<slug>/subtitle.lrc` | 播放器同步字幕（双语） |
| `articles/<slug>/sentences.txt` | shadowing 时的英文原文 |
| `voices_split/爱弥斯/refs/lively_20s.wav` | 声音克隆参考（你听久了不会反感的女声） |

**节奏建议**：每 2–3 周用本仓库新产一篇 AI Infra 文章音频。22 周累计 8–10 篇，等价于自产了一个**完全为你听力定制的 AI Infra 教材**。这是任何课程都给不了的杠杆。

## 附录 B：参考资料原始来源

- 本计划综合了 `references/reference-advice1.md`（12 周双轨阅读法 + 听力 20 min 流程）、`references/reference-advice2.md`（70/30 技术英语主线 + 词块库）、`references/reference-advice3.md`（Narrator / JAM / Shadowing 三技巧）的核心方法。
- AI Infra 播客来源：`references/AI-infra-podcast.md` §1 节目清单与 §4 10 集入门路线，已映射到本计划阶段 3–5 的听力升级路径。
