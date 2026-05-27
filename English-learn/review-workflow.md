# 复习流程：从"亲手踩的坑"到墨墨记忆卡

这套流程把日常学习里**亲身犯错 / 想记住的点**，规范化地沉淀成墨墨记忆卡（Markji）的可复习卡片。核心设计原则只有一句：

> **每张卡都挂着一个"我当时在干嘛、说错了什么"的场景钩子。复习时先想起场景，再回忆正确表达——比背孤立知识点记得牢得多。**

配套 [English-learn.md §4](English-learn.md) 的"只收 4 类、每天 ≤5 张"原则，以及 [ai-chat-prompt.md](ai-chat-prompt.md) 里 AI 教练产出的 "Chunk of the day"。

---

## 四步流程总览

```
1. 问题发现        2. 过程记录              3. 整理成卡               4. 复习
─────────         ─────────               ─────────                ─────────
学习中踩坑    →   当天写进 log/day-NN.md   →  当天 AI 教练把本日        →  墨墨里复习，
或 AI 教练         （自然语言，带场景，        log 整理成墨墨表格           看到场景 →
指出问题点         不要求卡片格式）            (cards/day-NN.md)         回忆正确表达
                                            + 告诉你怎么导入
```

**按天走**：每天学完就记 → 当天整理成卡 → 当天导入墨墨 → 当天/次日就能复习，不必等到周末批量。`day-NN` 是学习日序号（只有真正学习的那天才建文件，跳过的日子不占号），日期写在文件标题里。

每一步的产物都是**纯文本、可 git 跟踪**的（音频除外）——你能像 review 代码一样 review 自己的英语进步。

---

## 目录结构

```
English-learn/
├── review-workflow.md       # 本文件：流程说明
├── log/
│   ├── _template.md         # 每日日志模板（复制它开新的一天）
│   ├── day-01.md            # 学习日 1：一天一个文件，自然语言记录
│   └── day-02.md            # 学习日 2 ...
└── cards/
    ├── _templates.md        # 三种墨墨卡型模板（粘到墨墨「表格导入」左侧面板）
    ├── day-01.md            # 学习日 1 生成的卡片表格（TSV，粘进墨墨下载的表格）
    └── day-02.md            # 学习日 2 ...
```

`day-NN` 是学习日序号，一天一个文件；日期写在文件标题（`# 学习日志 · Day NN — YYYY-MM-DD`）。跳过没学的日子不占号。每周日在 [English-learn.md §6.1](English-learn.md) 的周打卡里汇总本周几个 day 文件。

---

## Step 1 — 问题发现：什么值得做成卡？

**收**（非纯单词、有"踩坑/想记"价值的点）：

| 类型 | 例子 |
| --- | --- |
| 搭配 / 词块 | `make a decision`（不是 do）、`address an issue`、`spin up an instance` |
| 工程惯用语 | `fall back to`、`under the hood`、`thrash the cache`、`punt on it` |
| 易混词 | mitigate vs solve、hit vs reach、latency vs delay |
| 语法点（影响表意的） | 第三人称单数、条件句时态、可数/不可数 |
| 听力漏洞 | 听到 `gonna / kinda / spin up` 没反应过来 |

**不收**（进了也是电子墓园）：

- 纯单词 = 中文意思（`obscure = 模糊的`）
- 一眼就懂、不会再错的
- 太长、塞了 3 个知识点的"复合题"——拆成原子卡

**发现来源**：你自己读/听/说时卡住的瞬间；或 AI 教练（[ai-chat-prompt.md](ai-chat-prompt.md)）在对话里指出的 ❌→✅ 和 "Chunk of the day"。

---

## Step 2 — 过程记录：当天日志怎么写

复制 `log/_template.md` → 新建当天的 `log/day-NN.md`，**用自然语言**追加。**不要求**卡片格式，但**强烈建议每条带「场景」**——那是 Step 4 复习时的记忆钩子。

每条用一个 `[类型]` 标签开头（方便 Step 3 自动归类，可省略，AI 也能推断）：

```markdown
# 学习日志 · Day 03 — 2026-05-28 周四

来源：AI 教练对话

- [纠错] ❌ do a decision → ✅ make a decision
  - 场景：和 AI 讨论要不要给推理服务加缓存层，我想说"我们得做个决定"
  - 为什么：decision 跟 make 搭配，不跟 do
- [语法] what happen → what happens
  - 场景：问 "when the KV cache is full, what happen?"
  - 为什么：what 作主语视作第三人称单数
- [词块] spin up an instance = 临时拉起一个实例
  - 场景：听 Latent Space 讲 Modal serverless 时听到，想记住
- [选择] mitigate vs solve
  - 场景：我写 "this solves the latency risk"，AI 指出 risk 要搭 mitigate
```

**省力技巧**：和 AI 教练对话时，直接说 *"把刚才的纠错点按 review-workflow Step 2 格式追加到今天的日志"*，让它替你写这段。

---

## Step 3 — 整理成卡：AI 把日志转成墨墨表格

每天学完（或任意你想制卡时），让 AI 教练做这件事。一句话指令：

> **"读 `English-learn/log/day-NN.md`，按 review-workflow Step 3 整理成墨墨表格，写到 `cards/day-NN.md`。"**

AI 会把每条日志映射到下面三种卡型之一，输出**与模板字段顺序一致的 TSV**。

### 三种卡型（模板见 [cards/_templates.md](cards/_templates.md)）

**① 纠错卡（主力，覆盖 ~80%）**——你亲手写错的搭配/词块/用词。
正面给"中文意图 + 场景"，逼你产出英语；背面给正确 + 你当时的错 + 原因。

```
正面：             背面：
┌──────────────┐   ┌────────────────────────┐
│ 我们得做个决定  │   │ ✅ make a decision       │
│ 📍 讨论要不要   │   │ ❌ 我写的：do a decision  │
│   加缓存层      │   │ 💡 decision 跟 make 搭配 │
│ 👉 英语怎么说？ │   └────────────────────────┘
└──────────────┘
```

**② 选择题卡**——易混词/二选一。墨墨原生交互，做完才出解析。

**③ 语法 / 概念卡**——Q&A，正面问题、背面答案 + 例句 + 场景。

### TSV 输出格式（AI 产出，你直接复制）

每种卡型一个 TSV 代码块，**首行是表头（字段名），顺序必须和墨墨模板里 `{{}}` 出现的顺序一致**。例如纠错卡：

```tsv
意图	场景	正确	错误	说明
我们得做个决定	讨论要不要给推理服务加缓存层	make a decision	do a decision	decision 跟 make 搭配，不跟 do
什么时候 KV cache 会满	问 vLLM 推理时	when does the KV cache fill up	when the KV cache is full what happen	what 作主语视作第三人称单数
```

### 导入墨墨的操作步骤（一次性配好模板，以后每天只换数据）

1. 墨墨里打开**你自己创建的原创牌组** → 右上角「**表格导入**」。
2. 左侧面板**粘贴对应卡型的模板**（从 [cards/_templates.md](cards/_templates.md) 复制）。`{{字段}}` 会被标绿。
3. 点「下载表格」拿到 xlsx，**把上面 TSV 的数据行粘进去**（TSV 粘到 Excel/Numbers/Sheets 会自动按制表符分列，列顺序天然对齐）。
4. 上传表格 → 预览确认无误 → 开始导入。
5. 之后这些卡就进了你的牌组，按墨墨的间隔重复算法复习。

> 模板里已经写好所有样式（`[T#B#]` 加粗、`[T#!36b59d#]` 墨墨绿、`[P#H1#]` 大标题等），**数据行保持纯文本**即可——样式和内容分离，最省心也最不容易出错。

---

## Step 4 — 复习：用"犯错场景"加深记忆

在墨墨里复习这些卡时，刻意走这个心理动作（而不是直接翻答案）：

1. 看到正面的**场景 + 中文意图** → 先在脑子里（或小声）**说出英语**。
2. **回忆当时是怎么错的**——"哦，我上次写成了 do a decision"。这一步的"提取-纠正"是记忆变深的关键。
3. 翻面核对 ✅，确认 💡 原因。
4. 错了就标记"模糊/忘记"，让墨墨缩短下次间隔。

每周日把本周几天的复习收获汇总，在 [English-learn.md §6.1 周打卡](English-learn.md) 的"高光时刻"里记一句：**哪个曾经踩坑的点，这次脱口而出了。**

---

## 完整示例（端到端走一遍）

**Step 1–2**：和 AI 教练讨论推理服务架构，写出 "this approach can solve the latency risk and we need do a decision"。AI 指出两个问题。你（或让 AI）在当天的 `log/day-15.md` 追加：

```markdown
# 学习日志 · Day 15 — 2026-07-15 周三
来源：AI 教练对话（讨论推理服务加不加缓存层）

- [选择] solve vs mitigate the risk
  - 场景：我写 "this approach can solve the latency risk"
  - 为什么：risk 只能 reduce/mitigate，不能 solve（solve 搭 problem）
- [纠错] ❌ need do a decision → ✅ need to make a decision
  - 场景：同一句话，想说"得做个决定"
  - 为什么：need to do；decision 跟 make 搭配
```

**Step 3**：当天让 AI 整理，它写出 `cards/day-15.md`：

纠错卡 TSV：
```tsv
意图	场景	正确	错误	说明
我们得做个决定	讨论推理服务加不加缓存层	we need to make a decision	need do a decision	need to do；decision 跟 make 搭配
```

选择题卡 TSV：
```tsv
题干	答案	选项1	选项2	选项3	解析	场景
"这个方案能____延迟风险"，该用哪个词？	A	mitigate	solve	fix	risk 搭 reduce/mitigate；solve 搭 problem	我写成了 this solves the latency risk
```

**Step 4**：导入后，下次复习看到"讨论加不加缓存层 / 我们得做个决定"，你先想起那次写错的句子，再脱口 "we need to make a decision" —— 场景 + 纠错一起被强化。

---

## 附录：墨墨记忆卡语法速查

来自官方文档（[内容语法说明](references/markji-content-syntax.md)、[表格导入说明](references/markji-table-import.md)）。制卡时**样式写进模板**，数据行保持纯文本。

| 语法 | 作用 | 例子 |
| --- | --- | --- |
| `---` | 答案线，分隔正/反面 | 见模板 |
| `[T#B#文字]` | 加粗 | `[T#B#make]` |
| `[T#!36b59d#文字]` | 文字颜色（墨墨绿；一个 `!`，颜色码小写） | `[T#!36b59d#正确]` |
| `[T#!!c5f1c0#文字]` | 背景色（两个 `!`） | — |
| `[T#B,!36b59d#文字]` | 叠加（逗号分隔，不分先后） | 加粗+绿色 |
| `[F##文字]` | 填空挖空（复习时可点开） | `[F##make]` |
| `[P#H1#文字]` | 整行大标题；`,center` 居中 | `[P#H1,center#概念]` |
| `[Choice#ans/A#\n- 选项\n- 选项\n]` | 选择题，`ans/` 直接指定答案字母 | 见模板 |
| `[E##E=mc^2]` | 公式（Katex 语法） | — |

注意：挖空 `[F##]` 不能跨行、不能嵌套加粗；选择题选项支持高亮但不支持挖空。
