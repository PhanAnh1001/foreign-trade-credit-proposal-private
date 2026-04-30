import re
import os
import time
import logging
import math
from functools import lru_cache
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv(".env")


@lru_cache(maxsize=8)
def get_llm(model: str = "llama-3.3-70b-versatile", temperature: float = 0.0,
            max_tokens: int = 8192) -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment")
    return ChatGroq(
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def get_fast_llm() -> ChatGroq:
    """llama-3.1-8b-instant: simple extraction, small input."""
    return get_llm(model="llama-3.1-8b-instant", temperature=0.0, max_tokens=2048)


def get_medium_llm() -> ChatGroq:
    """qwen/qwen3-32b: structured extraction (emits <think> blocks — use strip_llm_json)."""
    return get_llm(model="qwen/qwen3-32b", temperature=0.0, max_tokens=4096)


def get_extraction_llm() -> ChatGroq:
    """llama-3.3-70b-versatile: LC field extraction (12K TPM, 128K ctx, max_tokens=2048).

    Used for contract extraction: system_prompt ~900T + contract ~2K + output 2K = ~5K total,
    comfortably within 12K TPM limit. Avoids qwen3-32b's 6K TPM ceiling for this task.
    """
    return get_llm(model="llama-3.3-70b-versatile", temperature=0.0, max_tokens=2048)


def get_smart_llm() -> ChatGroq:
    """openai/gpt-oss-120b: complex reasoning, max_tokens=4096 to avoid 413."""
    return get_llm(model="openai/gpt-oss-120b", temperature=0.0, max_tokens=4096)


def get_judge_llm() -> ChatGroq:
    """qwen/qwen3-32b: independent judge (Alibaba, different vendor from Meta extraction).
    Emits <think> blocks — use strip_llm_json(). Input ~730T + max_tokens=2048 = ~2778T < 6K TPM.
    """
    return get_llm(model="qwen/qwen3-32b", temperature=0.0, max_tokens=2048)


_RETRY_AFTER_RE = re.compile(r"try again in ([\d.]+)s", re.IGNORECASE)
_RETRY_FALLBACK_S = 15


def _parse_retry_after(msg: str) -> int:
    m = _RETRY_AFTER_RE.search(msg)
    if m:
        return math.ceil(float(m.group(1))) + 2
    return _RETRY_FALLBACK_S


def invoke_with_retry(llm: ChatGroq, messages: list, *, retries: int = 2, sleep_s: int | None = None):
    """Invoke LLM with automatic retry on 429/413 rate-limit errors."""
    _log = logging.getLogger("llm.retry")
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return llm.invoke(messages)
        except Exception as exc:
            msg = str(exc)
            if "429" in msg or "413" in msg or "rate_limit" in msg.lower():
                last_exc = exc
                if attempt < retries:
                    wait = sleep_s if sleep_s is not None else _parse_retry_after(msg)
                    _log.warning(
                        f"Rate limit (attempt {attempt+1}/{retries+1}) — sleeping {wait}s: {msg[:120]}"
                    )
                    time.sleep(wait)
                    continue
            raise
    raise last_exc  # type: ignore[misc]


_THINK_BLOCK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_TRAILING_COMMA_RE = re.compile(r",\s*([\]}])")
_PYTHON_NONE_RE = re.compile(r"\bNone\b")
_PYTHON_TRUE_RE = re.compile(r"\bTrue\b")
_PYTHON_FALSE_RE = re.compile(r"\bFalse\b")


def strip_llm_json(raw: str) -> str:
    """Strip <think> blocks, markdown fences, trailing commas, Python literals."""
    raw = _THINK_BLOCK_RE.sub("", raw).strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        start = 1
        end = len(lines)
        if lines[-1].strip() == "```":
            end = len(lines) - 1
        raw = "\n".join(lines[start:end]).strip()
    raw = _TRAILING_COMMA_RE.sub(r"\1", raw)
    raw = _PYTHON_NONE_RE.sub("null", raw)
    raw = _PYTHON_TRUE_RE.sub("true", raw)
    raw = _PYTHON_FALSE_RE.sub("false", raw)
    return raw
