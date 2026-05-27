# 学习日志 · Day 01 — 2026-05-25 周一

> 格式见 [../review-workflow.md](../review-workflow.md) Step 2。每条带「场景」做记忆钩子。
> 学完当天就整理成墨墨表格（review-workflow Step 3 → [../cards/day-01.md](../cards/day-01.md)），当天即可导入复习。
>
> 来源：早期 AI 英语反馈——在做 blog-voice 项目、用英文讨论 verify / split-text 流程时写的句子，原始反馈存为 [../anki-grammar-feedback-2026-05-25.tsv](../anki-grammar-feedback-2026-05-25.tsv)（Anki Cloze 格式）。下面转成本日志格式，便于整理进墨墨。

## 冠词 (a / the)

- [语法] ❌ in verifying phase → ✅ in **the** verifying phase
  - 场景：描述 "in ___ verifying phase, the model proposes a fix"
  - 为什么：可数单数名词前要加冠词
- [语法] ❌ fix the mistake in transcription → ✅ in **the** transcription
  - 场景：说"如果转写里有错就修"
  - 为什么：特指、已提到过的名词 → the
- [语法] ❌ push directly to main branch → ✅ to **the** main branch
  - 场景：说"可以直接 push 到 main 分支"
  - 为什么：特指那个分支 → the
- [语法] ❌ Issue #171 is actually error → ✅ is actually **an** error
  - 场景：描述 Issue #171
  - 为什么：可数单数 → a/an；元音音开头 → an

## 动词形态 / 时态

- [语法] ❌ if LLM think there is a mistake → ✅ if the LLM **thinks**
  - 场景：说"如果 LLM 认为有错，它就修"
  - 为什么：第三人称单数现在时加 -s（外加 the LLM 的冠词）
- [纠错] ❌ the sentence was splited → ✅ was **split** into two parts
  - 场景：说"句子被切成了两段"
  - 为什么：split 是不规则动词，split / split / split，没有 "splited"
- [语法] ❌ fix it if it was wrong → ✅ if it **is** wrong
  - 场景：描述一条通用规则"如果转写错了就修"
  - 为什么：陈述一般规则用现在时，不用过去时

## 副词语序

- [语法] ❌ Issue #171 actually is a splitting error → ✅ **is actually** a splitting error
  - 场景：强调 #171 其实是切句错误
  - 为什么：副词放在 be 动词之后
- [语法] ❌ it's ok to directly push to main → ✅ to **push directly** to main
  - 场景：说"可以直接 push 到 main"
  - 为什么：副词放在实义动词之后

## 单复数

- [语法] ❌ use the other two reference → ✅ the other two **references**
  - 场景：说"每个 reference 有两次机会，所以用另外两个 reference"
  - 为什么：two 之后名词用复数

## 介词

- [纠错] ❌ I tried these abbreviations in the Fish Audio website → ✅ **on** the website
  - 场景：说"我在 Fish Audio 网站上试了这些缩写"
  - 为什么：网站用 on a website，不用 in
- [纠错] ❌ rerun the TTS of this sentence → ✅ **for / on** this sentence
  - 场景：说"重跑这句的 TTS"
  - 为什么：for / on this sentence，不用 of

## 选词

- [选择] correct voice vs correct **pronunciation**
  - 场景：我写 "I got the correct voice for all of them"，想说"发音都对了"
  - 为什么：pronunciation = 一个词怎么读；voice = 音色。想说"读音对"要用 pronunciation
- [选择] At last vs **Finally / Lastly**
  - 场景：列举最后一点"最后，verifier 还应该修文本"
  - 为什么：Finally / Lastly 用于列表的最后一项；At last 表示"久等之后终于"的如释重负

## 拼写

- [纠错] ❌ verifing / refernece / respository → ✅ **verifying / reference / repository**
  - 场景：项目讨论里反复拼错这三个词
  - 为什么：verify→verifying（保留 y）；reference（中间 e-r-e）；repository（没有多余的 s）
