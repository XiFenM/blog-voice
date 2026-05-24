# blog-voice

把英文技术博客转成"任意角色音色"的语音音频 + 双语 LRC 字幕，并用多模态 LLM 校验生成质量。当前实例：用《鸣潮》角色**爱弥斯**的音色朗读 ezyang 的 *PyTorch internals*。

整个流水线：

```
voice library
  wiki.kurobbs.com  ──► voice scrape ──► voices/<角色>/*.wav + transcript + manifest
                    └─► voice split  ──► voices_split/<角色>/{normal,mecha}/

article pipeline (per slug)
  blog URL ──► (playwright eval) ──► articles/<slug>/source.txt
       └─► article split-text   ──► sentences.txt
       └─► article enhance      ──► sentences_enhanced.txt   (可选; LLM 注入 Fish 标签, 仅 fish 后端)
       └─► article tts          ──► audio/####.wav           (chatterbox 本地 / fish API)
       └─► article merge        ──► merged.wav
       └─► article lrc          ──► subtitle.lrc             (可 --translate-zh 加中文翻译)
       └─► article verify       ──► verify_report.json       (可选; 多模态 LLM 校验音频)
```

每篇文章一个目录，自带 `meta.json` 存默认 ref 音色和后端选择，所以同时跑多篇互不打架。所有 LLM 调用统一走 [ZenMux 网关](https://zenmux.ai)（OpenAI 协议），纯文本调用（翻译 / 标签增强）失败时自动回退到 DeepSeek 官方 API。

## 5 分钟 quickstart

从零跑通"爱弥斯念 PyTorch internals"：

```bash
# 1. 安装
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone git@github.com:XiFenM/blog-voice.git && cd blog-voice
uv sync

# 2. 配置 key（.env 文件）
cp .env.example .env
# 编辑 .env，至少填 ZENMUX_API_KEY + FISH_API_KEY（chatterbox 本地后端可不要 fish）

# 3. 抓角色语音库（116 条，约 30s）
uv run blog-voice voice scrape https://wiki.kurobbs.com/mc/item/1457744312692867072
uv run blog-voice voice split   # 用仓库自带的 voice_labels.json 拆 normal/mecha

# 4. 抓博客文本（用本机 Chrome + playwright-cli，见下文"前置工具"）
playwright-cli attach --cdp=http://localhost:9222
playwright-cli goto https://blog.ezyang.com/2019/05/pytorch-internals/
playwright-cli --raw eval "() => document.querySelector('article.post').innerText" > /tmp/blog.txt

# 5. 创建文章并跑全流程（fish API + 标签增强 + 中文字幕 + 音频校验）
uv run blog-voice article add pytorch-internals --source /tmp/blog.txt \
  --title "PyTorch internals" --artist 爱弥斯 \
  --ref-voice voices_split/爱弥斯/refs/lively_20s.wav \
  --backend fish --fish-reference-id <你在 fish.audio 上传 lively_20s.wav 后拿到的 id>

uv run blog-voice article pipeline pytorch-internals \
  --enhance --translate-zh --verify --include-metadata --gap 0.3
```

跑完输出在 [articles/pytorch-internals/](articles/pytorch-internals/)：
- `merged.wav` —— 完整音频（fish 出 44.1kHz/16-bit，250 句约 37 分钟）
- `subtitle.lrc` —— 双语 LRC 字幕
- `verify_report.json` —— 每句的 QA 报告，含整体 pass rate 和失败 index

后续修改单个步骤可以单独重跑，所有阶段都断点续跑（已生成的 wav / 已缓存的翻译 / 已校验的句子都会跳过）。

## 安装

### 前置工具

**1. uv**（Python 包/虚拟环境管理）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. playwright-cli**（仅在抓博客文本 / 调试 wiki 接口时用到）

```bash
npm install -g @playwright/cli@latest
playwright-cli install --skills
```

**3. 本机 Chrome 调试端口 + SSH 端口转发**（仅当 playwright-cli 跑在远程开发机时）

本机退出 Chrome 后用调试端口启动：

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
# Linux
google-chrome --remote-debugging-port=9222
# Windows (PowerShell)
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

`~/.ssh/config` 加 `RemoteForward 9222 localhost:9222`，VSCode Remote-SSH 会复用。验证：远程机上 `curl http://localhost:9222/json/version` 拿到 JSON。

连上：

```bash
playwright-cli attach --cdp=http://localhost:9222
```

### Python 依赖

```bash
uv sync   # 装全部依赖 + 注册 `blog-voice` CLI 入口
```

### `.env` 配置（按需）

复制 `.env.example` 到 `.env`，按以下需求填：

| key | 何时必需 | 说明 |
|---|---|---|
| `ZENMUX_API_KEY` | 用 `enhance` / `lrc --translate-zh` / `verify` 任一时 | LLM 网关 [zenmux.ai](https://zenmux.ai)，一把 key 同时覆盖三处（翻译 / 标签增强 / 音频校验），model id 走 `provider/model-name` 格式 |
| `DEEPSEEK_API_KEY` | 可选 | ZenMux 配额耗尽/网络异常时**自动回退**到 [DeepSeek 官方 API](https://platform.deepseek.com/api_keys)，仅对 `deepseek/*` 模型有效。音频校验（Gemini）没有兜底 |
| `FISH_API_KEY` | TTS 后端选 `fish` 时 | [fish.audio](https://fish.audio/app/api-keys/) |
| `HF_ENDPOINT` | chatterbox 首次下载模型时（可选） | 设为 `https://hf-mirror.com` 走镜像 |

**默认模型**（在 [src/blog_voice/llm/zenmux.py](src/blog_voice/llm/zenmux.py) 集中改）：
- 翻译：`deepseek/deepseek-v4-flash`
- 标签增强：`deepseek/deepseek-v4-pro`
- 音频校验：`google/gemini-3.5-flash`

## CLI 总览

`uv run blog-voice` 是统一入口，按领域分两组：

| 子命令 | 作用 |
|---|---|
| `voice scrape <id-or-url>` | 从 wiki.kurobbs.com 抓某角色全部语音到 `voices/<角色>/` |
| `voice classify` | 无监督 KMeans 把单角色音色聚成两类，输出 TSV 报告 |
| `voice split` | 用手工标的 [voice_labels.json](voice_labels.json) 拆分混合片段到 `voices_split/<角色>/{normal,mecha}/` |
| `article add <slug> --source FILE` | 创建 `articles/<slug>/`，写入 `source.txt` + `meta.json` |
| `article split-text <slug>` | 切句到 `sentences.txt` |
| `article enhance <slug>` | 走 ZenMux 给每句注入 Fish 标签（`[break]/[emphasis]/[curious]`…），写 `sentences_enhanced.txt`。**仅 fish 后端有意义** |
| `article tts <slug>` | 每句生成一个 wav 到 `audio/####.wav`，支持断点续跑。fish 后端会自动用 enhanced 版本（如果存在） |
| `article merge <slug>` | 拼成单个 `merged.wav` |
| `article lrc <slug>` | 生成 `subtitle.lrc`，`--translate-zh` 给每句加一行中文翻译（走 ZenMux） |
| `article verify <slug>` | 把每条音频 + 原句送给支持音频输入的多模态模型（默认 `google/gemini-3.5-flash`），输出 `verify_report.json` |
| `article pipeline <slug>` | 串起 split-text + (enhance) + tts + merge + lrc + (verify) 一把梭，用 `--enhance` / `--verify` 开关启用可选步骤 |

每个子命令 `--help` 看完整参数。

## 1. 抓角色语音 — `voice scrape`

直接调 wiki 开放 API（`POST /wiki/core/catalogue/item/getEntryDetail`），无登录、无浏览器。

```bash
# 用 URL
uv run blog-voice voice scrape https://wiki.kurobbs.com/mc/item/1457744312692867072
# 或直接给 ID
uv run blog-voice voice scrape 1457744312692867072 --out voices
```

产出：
- `voices/<角色名>/###_<标题>.wav` —— 全部音频（爱弥斯共 116 条）
- `voices/<角色名>/###_<标题>.wav.transcript.txt` —— 每条音频对应的中文台词（从 wiki `content` 字段抓的）
- `voices/<角色名>/manifest.json` —— 完整索引（含 `text` 字段）

换角色只需替换 ID（在 wiki 角色页 URL 里 `/item/` 后那串数字）。重跑 scrape 是幂等的——音频已存在会跳过下载，但 transcript / manifest 会重新写一遍，可以用来给旧的语音库补上文字。

## 2. 区分角色不同音色模式 — `voice split`

爱弥斯有"常态"和"机甲"两种音色，混在 116 条里。流程：

1. **手工标注**：听一遍后填好 [voice_labels.json](voice_labels.json)：
   - `pure_normal` / `pure_mecha` —— 纯一种音色的文件编号
   - `split_normal_then_mecha` / `split_mecha_then_normal` —— 中途切换音色的文件编号
   - `manual_split_ratios` —— 算法切偏时手工指定切点（0–1 比例）

2. **跑切分**：

   ```bash
   uv run blog-voice voice split
   ```

   - 用 pure_* 文件训练参考模型（MFCC + 谱特征 + KMeans，约 84% 准确率），打印分类准确率
   - 纯文件直接复制
   - 混合文件用滑窗扫描 + 误分类最小化找最佳切点，按方向切成两段
   - 输出到 `voices_split/<角色>/{normal,mecha}/`

也可以用无监督版本快速摸底（不需要先标注）：

```bash
uv run blog-voice voice classify --voice-dir voices/爱弥斯 --split
```

## 3. 抓博客文本 — playwright-cli

```bash
playwright-cli attach --cdp=http://localhost:9222
playwright-cli goto https://blog.ezyang.com/2019/05/pytorch-internals/
playwright-cli --raw eval "() => document.querySelector('article.post').innerText" > /tmp/blog.txt
```

注意：`--raw eval` 的输出第一行是 **JSON 编码字符串**（带字面 `\n`），不是 plaintext。`split-text` 内部会 `json.loads(first_line)` 解码。

## 4. 录入文章 — `article add`

```bash
uv run blog-voice article add pytorch-internals \
  --source /tmp/blog.txt \
  --title "PyTorch internals" \
  --artist 爱弥斯 \
  --ref-voice voices_split/爱弥斯/normal/104_滑翔.wav \
  --backend chatterbox
```

会创建：
```
articles/pytorch-internals/
├── meta.json     # 标题、音色、后端等默认配置
├── source.txt    # 拷贝自 --source
└── audio/        # （此时为空）
```

## 5. 切句 — `article split-text`

```bash
uv run blog-voice article split-text pytorch-internals
```

写 `articles/pytorch-internals/sentences.txt`，每句一段、段间一空行。常见英文缩写（Mr./e.g./No./Inc. …）已加白名单。

## 6. 生成语音 — `article tts`

两种后端，按 `meta.json` 或命令行 `--backend` 选：

### A. chatterbox（本地）

权重首次自动下载到 `.model-cache/chatterbox/`，约 1.8 GB。每句都用同一份 ref，防自回归漂移。

```bash
# 默认 cpu、用 meta.json 里的 ref；先 limit 5 试听
uv run blog-voice article tts pytorch-internals --limit 5

# GPU
uv run blog-voice article tts pytorch-internals --device cuda

# 临时换 ref
uv run blog-voice article tts pytorch-internals \
  --ref voices_split/爱弥斯/normal/022_自我介绍.wav --limit 5
```

### B. fish-audio（API，免 GPU）

需要 `FISH_API_KEY`。两种参考方式：

- `--ref voices_split/...wav` —— 本地 wav 直接做零样本克隆。fish API 要求 ref 配一段对应文本：如果 wav 旁边已经有 `<wav>.transcript.txt`（`voice scrape` 抓 wiki 时已经自动写好，纯文件被 `voice split` 复制时也带走），直接用；否则脚本会自动调 fish ASR 转录、缓存在同样的文件名下，`--fish-ref-language zh` 指定语言。手工编辑这个 txt 文件下次会被尊重。
- `--fish-reference-id <id>` —— 在 fish.audio 上已经上传/保存好的 voice model id，最快最稳，长跑首选。

```bash
uv run blog-voice article tts pytorch-internals \
  --backend fish \
  --ref voices_split/爱弥斯/normal/104_滑翔.wav \
  --fish-ref-language zh \
  --limit 5

# 或用预存的 voice id
uv run blog-voice article tts pytorch-internals \
  --backend fish --fish-reference-id 802e3bc2b27e49c2995d23ef70e6ac89
```

### 通用

每句一个 wav 写到 `audio/####.wav`，**断点续跑**：已存在的非空文件跳过，可随时 Ctrl-C 后再重启。

| 后端 / 环境 | rt 倍率 | 全文 250 句（≈17 分钟音频）耗时 |
|---|---|---|
| chatterbox / 4 核 CPU | ~10–20× 慢于实时 | 3–6 小时 |
| chatterbox / 6–8 GB VRAM GPU | ~0.3–0.5× 实时 | 5–15 分钟 |
| fish-audio API | ~0.5–1× 实时 | 视并发，几分钟到十几分钟 |

## 6.5. （fish 专用）句子标签增强 — `article enhance`

只对 fish 后端有意义。chatterbox 不认 `[break]` `[emphasis]` 这类标签会按字面读出来。

```bash
uv run blog-voice article enhance pytorch-internals \
  --model deepseek/deepseek-v4-pro --concurrency 10
```

走 ZenMux 调 LLM，按一份 prompt（内置 Fish S2-Pro 支持的标签清单 + 放置规则）给每句注入最小量的标签，写到 `articles/<slug>/sentences_enhanced.txt`：

```
原句:    I'm not going to lie: the PyTorch codebase can be a bit overwhelming at times.
增强后:  I'm not going to lie: [short pause] the PyTorch codebase can be a bit [emphasis]overwhelming at times.
```

可断点续跑：缓存在 `enhancements.json`，重跑只补缺。后续 `article tts --backend fish` 会自动用这份增强后的文本（`--use-enhanced` 默认 `auto`），LRC 字幕仍展示原句。

## 7. 合并音频 — `article merge`

```bash
uv run blog-voice article merge pytorch-internals          # 直接拼
uv run blog-voice article merge pytorch-internals --gap 0.3 # 句间加 0.3s 静音
```

输出 `articles/<slug>/merged.wav`（16-bit PCM）。

## 8. 生成字幕 — `article lrc`

```bash
# 纯英文
uv run blog-voice article lrc pytorch-internals --include-metadata

# 双语（英文行下面紧跟中文翻译，DeepSeek 翻译，按句缓存到 translations_zh.json）
uv run blog-voice article lrc pytorch-internals --translate-zh --include-metadata
```

## 8.5. 音频校验 — `article verify`

把每条 `audio/####.wav` 和原句一起发给支持音频输入的多模态模型，让它判断"读对了吗 / 自然吗"，结果写到 `articles/<slug>/verify_report.json`：

```bash
uv run blog-voice article verify pytorch-internals \
  --model google/gemini-3.5-flash --concurrency 5 --language English
```

报告里每条记录长这样：
```json
{
  "index": 1, "audio": "0001.wav",
  "sentence": "PyTorch internals May 16, 2019",
  "ok": true, "matches_text": true, "naturalness": 5,
  "transcription": "PyTorch internals, May 16, 2019",
  "issues": []
}
```

末尾汇总 `passed / total` 和 `failed_indexes`，可断点续跑：已校验的句子在 `verify_report.json` 里、重跑只补新生成的。

## 9. 全流程一把梭 — `article pipeline`

`split-text` → (`enhance`) → `tts` → `merge` → `lrc` → (`verify`)，方括号项用 flag 开启：

```bash
# chatterbox + 中文字幕
uv run blog-voice article pipeline pytorch-internals \
  --backend chatterbox --device cuda \
  --ref voices_split/爱弥斯/refs/lively_20s.wav \
  --gap 0.3 --translate-zh --include-metadata

# fish + 标签增强 + 字幕翻译 + 音频校验
uv run blog-voice article pipeline pytorch-internals \
  --backend fish \
  --enhance --enhance-model deepseek/deepseek-v4-pro \
  --translate-zh --translation-model deepseek/deepseek-v4-flash \
  --verify --verify-model google/gemini-3.5-flash \
  --include-metadata
```

## 目录结构

```
blog-voice/
├── pyproject.toml          # `blog-voice` CLI 入口注册在这里
├── voice_labels.json       # 角色音色人工标注（爱弥斯）
├── voice.md                # TTS 选型 + 工程建议
├── src/blog_voice/
│   ├── cli.py              # 总入口 (argparse 子命令)
│   ├── paths.py            # ArticlePaths + ArticleMeta
│   ├── llm/zenmux.py       # ZenMux OpenAI-compatible 客户端
│   ├── voices/             # scrape / classify / split
│   ├── text/               # sentences (切句) + enhance (Fish 标签注入)
│   ├── tts/                # base / chatterbox / fish_audio / runner
│   ├── audio/merge.py      # 合并 wav
│   ├── subtitle/lrc.py     # 生成 LRC（走 ZenMux 翻译）
│   └── verify/audio.py     # 多模态 LLM 音频 QA
├── voices/<角色>/          # 原始抓取
├── voices_split/<角色>/    # 拆分后的 normal/mecha
├── articles/<slug>/        # 每篇文章一目录
│   ├── meta.json                  # 默认 ref / backend / artist 等
│   ├── source.txt
│   ├── sentences.txt              # 原始切句（LRC、verify 都用这版）
│   ├── sentences_enhanced.txt     # fish 标签增强版（fish TTS 自动读）
│   ├── enhancements.json          # 增强缓存（断点续跑）
│   ├── audio/####.wav
│   ├── merged.wav
│   ├── subtitle.lrc
│   ├── translations_zh.json       # 翻译缓存
│   └── verify_report.json         # 音频 QA 报告
└── .model-cache/           # chatterbox 权重缓存
```

## 已知坑

- **TTS 输出格式不一致**：chatterbox 默认写 IEEE_FLOAT 32-bit，fish 默认 PCM；`article merge` 走 `soundfile` 统一读，输出 16-bit PCM。
- **fish 后端的 ref 转录**：第一次用本地 wav 做参考会调用 fish ASR 转录中文台词、缓存在 `<ref>.transcript.txt`。ASR 不理想时可手工编辑这个文件。
- **ZenMux 免费配额很紧**：跑全文翻译 / 增强（250 句 × 2 ≈ 500 次调用）可能就把 rolling window 耗光，会返回 HTTP 402 `quote_exceeded`。配 `DEEPSEEK_API_KEY` 后纯文本部分自动兜底；音频校验（Gemini）没有兜底，撞了只能等配额刷新或升级 ZenMux 套餐。
- **缩写/符号/版本号**：技术博客 TTS 最大的坑。已通过 `article enhance` 给 fish 加 `[break]/[emphasis]` 缓解部分节奏问题，但术语展开（`API → A P I`、`v2.5.1 → version two point five point one`）仍未做。如听感不行，参考 voice.md §3 做 LLM 预处理后再喂给 TTS。
- **copyright**：`voices/`、`voices_split/`、`articles/*/source.txt` / `sentences*.txt` / `audio/` / `merged.wav` / `subtitle.lrc` 等用户内容已 gitignore（看 `.gitignore`），不要推到公开仓库；只有 `meta.json` + `voice_labels.json` 这些"配置/标注"文件会被跟踪。
