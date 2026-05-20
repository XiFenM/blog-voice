# blog-voice

把英文技术博客转成"任意角色音色"的语音音频。当前实例：用《鸣潮》角色**爱弥斯**的音色朗读 ezyang 的 *PyTorch internals*。

整个流水线分三段：

```
wiki.kurobbs.com ──► scrape_voices.py ──► voices/<角色>/*.wav  (参考音色库)
ezyang's blog    ──► split_sentences.py ─► pytorch_internals_sentences.txt
        ┌──────────────────────────────────┘
        ▼
generate_tts.py (Chatterbox + 参考音色) ──► tts_out/####.wav
```

## 环境

### 前置工具

**1. uv**（Python 包/虚拟环境管理）

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2. playwright-cli**（仅在抓博客文本 / 调试 wiki 接口时用到）

```bash
npm install -g @playwright/cli@latest
playwright-cli install --skills    # 安装配套的 Claude Code skill
```

**3. 本机 Chrome 开启远程调试 + 端口转发到远程机器**

> 仅当 playwright-cli 跑在远程开发机、Chrome 在本机时需要。如果两者同机可跳过。

本机完全退出 Chrome 后用调试端口启动：

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
# Linux
google-chrome --remote-debugging-port=9222
# Windows (PowerShell)
& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

验证：本机浏览器打开 `http://localhost:9222/json/version` 看到 JSON。

把 9222 转到远程开发机。在本机 `~/.ssh/config` 加 `RemoteForward`：

```sshconfig
Host my-dev-box
  HostName <ip>
  User root
  IdentityFile ~/.ssh/id_ed25519
  RemoteForward 9222 localhost:9222
  ServerAliveInterval 30
  ServerAliveCountMax 3
```

VSCode Remote-SSH 会复用这份 config，连接后自动建好转发。验证：远程机上 `curl http://localhost:9222/json/version` 拿到 JSON。

之后用：
```bash
playwright-cli attach --cdp=http://localhost:9222
```

### Python 依赖

uv 管理的 Python 3.12 虚拟环境，依赖见 `pyproject.toml`：
- `httpx`（API 抓取）
- `chatterbox-tts`、`torch`、`torchaudio`（TTS）

```bash
uv sync           # 安装全部依赖
```

## 1. 抓角色语音 — `scrape_voices.py`

直接调用库街区 wiki 的开放 API（`POST /wiki/core/catalogue/item/getEntryDetail`），无需登录，无需浏览器。

```bash
# 用 wiki URL
uv run python scrape_voices.py https://wiki.kurobbs.com/mc/item/1457744312692867072

# 或直接给 ID
uv run python scrape_voices.py 1457744312692867072 --out voices
```

产出：
- `voices/<角色名>/###_<标题>.wav` — 全部音频（爱弥斯共 116 条）
- `voices/<角色名>/manifest.json` — 完整索引

换其他角色只需替换 ID（在 wiki 角色页 URL 里 `/item/` 后那串数字）。

## 2. 抓博客文本 + 切句 — `split_sentences.py`

**先抓文本**（一次性，已完成；如换博客重做）：

```bash
playwright-cli attach --cdp=http://localhost:9222   # 连本机 Chrome（需 --remote-debugging-port=9222 启动）
playwright-cli goto https://blog.ezyang.com/2019/05/pytorch-internals/
playwright-cli --raw eval "() => document.querySelector('article.post').innerText" > pytorch_internals_raw.txt
```

**再切句**：

```bash
uv run python split_sentences.py
```

输出 `pytorch_internals_sentences.txt`，每句一段，段间一空行；常见英文缩写（Mr./e.g./No./Inc. 等）已加白名单防误切。

## 3. 生成语音 — `generate_tts.py`

Chatterbox-TTS，5–20s 参考音频 → 克隆音色。爱弥斯里已挑了 [voices/爱弥斯/022_自我介绍.wav](voices/爱弥斯/022_自我介绍.wav)（10.6s 纯独白）作默认参考。

```bash
# CPU 默认；GPU 加 --device cuda
uv run python generate_tts.py
uv run python generate_tts.py --device cuda

# 其他参数
uv run python generate_tts.py \
  --sentences pytorch_internals_sentences.txt \
  --ref voices/爱弥斯/022_自我介绍.wav \
  --out tts_out \
  --limit 5            # 只跑前 N 句做试听
```

每句一个 wav 写到 `tts_out/####.wav`，**断点续跑**：已存在的文件直接跳过，所以可以随时 Ctrl-C 后再重启。

### 性能参考

| 环境 | rt 倍率 | 全文 250 句（约 17 分钟音频）耗时 |
|---|---|---|
| 这台 4 核 CPU、无 GPU | ~10–20× 慢于实时 | 3–6 小时 |
| 任意 6–8 GB VRAM 的 GPU（参考 voice.md） | ~0.3–0.5× 实时 | 5–15 分钟 |

CPU 下推荐先 `--limit 5` 试听一遍再决定参考音色和参数。

### 换参考音色的挑选标准

参考 voice.md 第 1 条："10–15s、无背景噪音、语调自然"。在 `voices/爱弥斯/` 里几条已经验证合适的：
- `022_自我介绍.wav` — 10.6s
- `021_闲趣3.wav` — 14.8s
- `030_突破4.wav` — 10.1s
- `031_突破5.wav` — 15.9s

战斗类语音多带音效或喊叫，不适合做 reference。

## 文件清单

| 文件 | 说明 |
|---|---|
| `scrape_voices.py` | 角色语音抓取（API 直连） |
| `split_sentences.py` | 博客文本切句 |
| `generate_tts.py` | Chatterbox TTS 生成（支持断点续跑、CPU/GPU 切换） |
| `voice.md` | TTS 选型 & 工程建议（开源 vs 托管、参考音频准备、术语预处理等） |
| `voices/<角色>/` | 抓回来的语音库 |
| `pytorch_internals_raw.txt` | 博客 innerText（playwright eval 输出，JSON 转义） |
| `pytorch_internals_sentences.txt` | 切句后的可朗读文本 |
| `tts_out/` | TTS 生成结果 |

## 已知坑

- Chatterbox 是自回归模型，长文按段调用时**每次都用同一份 reference**，能防止音色漂移（脚本已经这么做）。
- 技术博客有大量缩写/符号/版本号/代码块，目前**没做术语预处理**。后续如果听感不行，按 voice.md 第 3 条做一遍 LLM 预处理（展开缩写、删代码块、规范标点）效果会更明显。
- `pytorch_internals_raw.txt` 第一行是个 JSON 字符串（playwright `--raw eval` 的格式），`split_sentences.py` 内做了 `json.loads` 解码，别直接当 plaintext 读。
- playwright-cli 通过 CDP 连本机 Chrome 需要 Chrome 用 `--remote-debugging-port=9222` 启动 + SSH 端口转发；ssh config 里加 `RemoteForward 9222 localhost:9222`。
