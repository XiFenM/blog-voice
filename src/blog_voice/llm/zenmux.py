"""ZenMux client factory with DeepSeek-native fallback.

ZenMux is an OpenAI-compatible router that fronts OpenAI / Anthropic /
Google / DeepSeek / etc. We use it for everything that talks to an LLM —
translation, sentence enhancement, audio verification — so a single
`ZENMUX_API_KEY` covers all three call sites and the model is swappable
per command via the `provider/model-name` id format.

ZenMux's free tier has a tight rolling quota; when that fires (HTTP 402
quota_exceeded) or any other transient error hits, `chat_completion`
transparently retries against the **DeepSeek native API**
(`https://api.deepseek.com`) for any `deepseek/*` model. The native
DeepSeek model id is derived by mapping the ZenMux slug to the closest
official equivalent (`deepseek-reasoner` for reasoner variants, otherwise
`deepseek-chat`). Non-DeepSeek models (Google/OpenAI/etc.) have no
fallback and re-raise.

Docs: https://zenmux.ai/docs/guide/quickstart.html
      https://api-docs.deepseek.com/
"""

import os
import threading

from dotenv import load_dotenv

BASE_URL = "https://zenmux.ai/api/v1"
API_KEY_ENV = "ZENMUX_API_KEY"

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"

DEFAULT_TRANSLATION_MODEL = "deepseek/deepseek-v4-flash"
DEFAULT_ENHANCEMENT_MODEL = "deepseek/deepseek-v4-pro"
DEFAULT_VERIFY_MODEL = "google/gemini-3.5-flash"

_zenmux_client = None
_deepseek_client = None
_deepseek_lookup_done = False
_client_lock = threading.Lock()


def _new_openai_client(api_key: str, base_url: str):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("openai package is not installed. Run `uv sync`.") from exc
    return OpenAI(api_key=api_key, base_url=base_url)


def get_client():
    """Return a process-wide ZenMux client (lazy + cached)."""
    global _zenmux_client
    if _zenmux_client is None:
        with _client_lock:
            if _zenmux_client is None:
                load_dotenv()
                api_key = os.environ.get(API_KEY_ENV)
                if not api_key:
                    raise SystemExit(
                        f"{API_KEY_ENV} is missing. Sign up at https://zenmux.ai "
                        "and put your key in .env."
                    )
                _zenmux_client = _new_openai_client(api_key, BASE_URL)
    return _zenmux_client


def _get_deepseek_client():
    """Return a process-wide DeepSeek native client, or None if DEEPSEEK_API_KEY is absent."""
    global _deepseek_client, _deepseek_lookup_done
    if _deepseek_lookup_done:
        return _deepseek_client
    with _client_lock:
        if _deepseek_lookup_done:
            return _deepseek_client
        load_dotenv()
        api_key = os.environ.get(DEEPSEEK_API_KEY_ENV)
        if api_key:
            _deepseek_client = _new_openai_client(api_key, DEEPSEEK_BASE_URL)
        _deepseek_lookup_done = True
        return _deepseek_client


def _deepseek_native_model(zenmux_model: str) -> str | None:
    """Map a `deepseek/*` ZenMux slug to a DeepSeek native API model id.

    Returns None for non-DeepSeek models so the fallback path skips them.
    """
    if not zenmux_model.startswith("deepseek/"):
        return None
    suffix = zenmux_model.split("/", 1)[1].lower()
    if "reasoner" in suffix or "r1" in suffix:
        return "deepseek-reasoner"
    return "deepseek-chat"


def chat_completion(model: str, **kwargs):
    """Run a chat completion via ZenMux; on failure fall back to DeepSeek native for `deepseek/*` models."""
    try:
        return get_client().chat.completions.create(model=model, **kwargs)
    except Exception as exc:
        fb_model = _deepseek_native_model(model)
        if fb_model is None:
            raise
        fb_client = _get_deepseek_client()
        if fb_client is None:
            raise
        print(
            f"  [fallback] zenmux failed for {model} ({type(exc).__name__}: {exc}); "
            f"retrying via api.deepseek.com with {fb_model}"
        )
        return fb_client.chat.completions.create(model=fb_model, **kwargs)
