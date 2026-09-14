from __future__ import annotations

import os
import re
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ============================================================
# CONFIGURAÇÃO
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "router.db")

load_dotenv(os.path.join(BASE_DIR, ".env"))

REQUEST_TIMEOUT = int(os.getenv("ROUTER_TIMEOUT", "90"))
MAX_RETRIES = int(os.getenv("ROUTER_MAX_RETRIES", "1"))
DEFAULT_MAX_TOKENS = int(os.getenv("ROUTER_MAX_TOKENS", "128"))
COOLDOWN_SECONDS = int(os.getenv("ROUTER_COOLDOWN", "30"))

# MODO JARVIS: di?logo curto e econ?mico
DIALOGUE_MAX_MESSAGES = int(
    os.getenv("ROUTER_DIALOGUE_MAX_MESSAGES", "6")
)

DIALOGUE_MAX_CHARS = int(
    os.getenv("ROUTER_DIALOGUE_MAX_CHARS", "1200")
)

DIALOGUE_MAX_OUTPUT = int(
    os.getenv("ROUTER_DIALOGUE_MAX_OUTPUT", "96")
)

QUOTA_ALERT_PERCENT = float(
    os.getenv("ROUTER_QUOTA_ALERT_PERCENT", "10")
)

DIALOGUE_STYLE = (
    "Responda de forma direta e curta. "
    "Use no m?ximo 1 ou 2 frases. "
    "Evite introdu??es, repeti??es e explica??es desnecess?rias. "
    "Priorize a resposta ?til."
)

OUTBOUND_TIMEOUT = int(
    os.getenv("OUTBOUND_TIMEOUT", "30")
)

OUTBOUND_ALLOWLIST = [
    item.strip().lower()
    for item in os.getenv(
        "OUTBOUND_ALLOWLIST",
        ""
    ).split(",")
    if item.strip()
]


ROUTER_API_KEY = os.getenv("ROUTER_API_KEY", "").strip()


# ============================================================
# MODELOS DE PROVEDOR
# ============================================================

@dataclass
class ProviderConfig:
    name: str
    env_key: str
    base_url: str
    model_env: str
    style: str = "openai"

    rpm_env: str | None = None
    tpm_env: str | None = None
    rpd_env: str | None = None

    priority: int = 100
    enabled: bool = True
    enabled_env: str = ""

    def is_enabled(self) -> bool:
        if not self.enabled:
            return False

        if not self.enabled_env:
            return True

        valor = os.getenv(
            self.enabled_env,
            "true",
        ).strip().lower()

        return valor not in {
            "0",
            "false",
            "no",
            "off",
            "disabled",
        }

    def api_key(self) -> str:
        return os.getenv(self.env_key, "").strip()

    def model(self) -> str:
        return os.getenv(self.model_env, "").strip()

    def rpm(self) -> int | None:
        return env_int(self.rpm_env)

    def tpm(self) -> int | None:
        return env_int(self.tpm_env)

    def rpd(self) -> int | None:
        return env_int(self.rpd_env)


def env_int(name: str | None) -> int | None:
    if not name:
        return None

    value = os.getenv(name, "").strip()

    if not value:
        return None

    try:
        number = int(value)
        return number if number > 0 else None
    except ValueError:
        return None


PROVIDERS = [
    ProviderConfig(
        name="groq",
        env_key="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
        model_env="GROQ_MODEL",
        style="openai",
        priority=10,
    ),
    ProviderConfig(
        name="gemini",
        env_key="GEMINI_API_KEY",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        model_env="GEMINI_MODEL",
        style="gemini",
        priority=30,
    ),
    ProviderConfig(
        name="openrouter",
        env_key="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        model_env="OPENROUTER_MODEL",
        style="openai",
        priority=40,
    ),
    ProviderConfig(
        name="nvidia",
        env_key="NVIDIA_API_KEY",
        base_url="https://integrate.api.nvidia.com/v1",
        model_env="NVIDIA_MODEL",
        style="openai",
        priority=60,
    ),
    ProviderConfig(
        name="huggingface",
        env_key="HUGGINGFACE_API_KEY",
        base_url="https://router.huggingface.co/v1",
        model_env="HUGGINGFACE_MODEL",
        style="openai",
        priority=70,
    ),
    ProviderConfig(
        name="cohere",
        env_key="COHERE_API_KEY",
        base_url="https://api.cohere.com/compatibility/v1",
        model_env="COHERE_MODEL",
        style="openai",
        priority=90,
    ),
]


# ============================================================
# BANCO SQLITE
# ============================================================

class UsageDB:

    def __init__(self, path: str):
        self.path = path
        self.lock = threading.RLock()

        with self.lock:
            conn = sqlite3.connect(self.path)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS provider_usage (
                    provider TEXT PRIMARY KEY,
                    calls INTEGER DEFAULT 0,
                    errors INTEGER DEFAULT 0,
                    rate_limits INTEGER DEFAULT 0,
                    tokens INTEGER DEFAULT 0,
                    last_status INTEGER DEFAULT 0,
                    last_error TEXT DEFAULT '',
                    last_latency REAL DEFAULT 0,
                    remaining_requests INTEGER,
                    remaining_tokens INTEGER,
                    cooldown_until REAL DEFAULT 0,
                    updated_at REAL DEFAULT 0
                )
                """
            )
            conn.commit()
            conn.close()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_provider(self, name: str):
        with self.lock:
            conn = self._connect()

            conn.execute(
                """
                INSERT OR IGNORE INTO provider_usage(provider)
                VALUES (?)
                """,
                (name,),
            )

            conn.commit()
            conn.close()

    def record_quota(
        self,
        provider,
        remaining_requests=None,
        request_limit=None,
        remaining_tokens=None,
        token_limit=None,
        quota_period=None,
        quota_reset=None,
        quota_source=None,
    ):
        agora = datetime.now().isoformat()

        conn = sqlite3.connect(self.path)

        conn.execute(
            """
            INSERT INTO provider_usage (
                provider,
                remaining_requests,
                request_limit,
                remaining_tokens,
                token_limit,
                quota_period,
                quota_reset,
                quota_source,
                quota_checked_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(provider) DO UPDATE SET
                remaining_requests = COALESCE(
                    excluded.remaining_requests,
                    provider_usage.remaining_requests
                ),
                request_limit = COALESCE(
                    excluded.request_limit,
                    provider_usage.request_limit
                ),
                remaining_tokens = COALESCE(
                    excluded.remaining_tokens,
                    provider_usage.remaining_tokens
                ),
                token_limit = COALESCE(
                    excluded.token_limit,
                    provider_usage.token_limit
                ),
                quota_period = COALESCE(
                    excluded.quota_period,
                    provider_usage.quota_period
                ),
                quota_reset = COALESCE(
                    excluded.quota_reset,
                    provider_usage.quota_reset
                ),
                quota_source = COALESCE(
                    excluded.quota_source,
                    provider_usage.quota_source
                ),
                quota_checked_at = excluded.quota_checked_at,
                updated_at = excluded.updated_at
            """,
            (
                provider,
                remaining_requests,
                request_limit,
                remaining_tokens,
                token_limit,
                quota_period,
                quota_reset,
                quota_source,
                agora,
                agora,
            ),
        )

        conn.commit()
        conn.close()

    def record_success(
        self,
        name: str,
        status: int,
        tokens: int,
        latency: float,
        headers: dict[str, str],
    ):
        remaining_requests = extract_remaining_requests(headers)
        remaining_tokens = extract_remaining_tokens(headers)

        with self.lock:
            conn = self._connect()

            conn.execute(
                """
                UPDATE provider_usage
                SET
                    calls = calls + 1,
                    tokens = tokens + ?,
                    last_status = ?,
                    last_error = '',
                    last_latency = ?,
                    remaining_requests = COALESCE(?, remaining_requests),
                    remaining_tokens = COALESCE(?, remaining_tokens),
                    cooldown_until = 0,
                    updated_at = ?
                WHERE provider = ?
                """,
                (
                    tokens,
                    status,
                    latency,
                    remaining_requests,
                    remaining_tokens,
                    time.time(),
                    name,
                ),
            )

            conn.commit()
            conn.close()

    def record_error(
        self,
        name: str,
        status: int,
        error: str,
        latency: float,
        cooldown: int = 0,
    ):
        with self.lock:
            conn = self._connect()

            conn.execute(
                """
                UPDATE provider_usage
                SET
                    errors = errors + 1,
                    rate_limits = rate_limits + ?,
                    last_status = ?,
                    last_error = ?,
                    last_latency = ?,
                    cooldown_until = ?,
                    updated_at = ?
                WHERE provider = ?
                """,
                (
                    1 if status == 429 else 0,
                    status,
                    error[:1000],
                    latency,
                    time.time() + cooldown if cooldown else 0,
                    time.time(),
                    name,
                ),
            )

            conn.commit()
            conn.close()

    def get(self, name: str) -> dict[str, Any]:
        self.ensure_provider(name)

        with self.lock:
            conn = self._connect()
            row = conn.execute(
                """
                SELECT *
                FROM provider_usage
                WHERE provider = ?
                """,
                (name,),
            ).fetchone()
            conn.close()

        return dict(row) if row else {}

    def all(self) -> list[dict[str, Any]]:
        with self.lock:
            conn = self._connect()
            rows = conn.execute(
                """
                SELECT *
                FROM provider_usage
                ORDER BY provider
                """
            ).fetchall()
            conn.close()

        return [dict(row) for row in rows]


DB = UsageDB(DB_PATH)

for provider in PROVIDERS:
    DB.ensure_provider(provider.name)


# ============================================================
# RATE LIMIT HEADERS
# ============================================================

def extract_remaining_requests(headers: dict[str, str]) -> int | None:
    keys = (
        "x-ratelimit-remaining-requests",
        "x-ratelimit-remaining-request",
        "x-ratelimit-remaining-rpm",
        "ratelimit-remaining",
    )

    lowered = {
        str(k).lower(): str(v)
        for k, v in headers.items()
    }

    for key in keys:
        value = lowered.get(key)

        if value is None:
            continue

        match = re.search(r"\d+", value)

        if match:
            return int(match.group())

    return None


def extract_remaining_tokens(headers: dict[str, str]) -> int | None:
    keys = (
        "x-ratelimit-remaining-tokens",
        "x-ratelimit-remaining-tpm",
        "ratelimit-remaining-tokens",
    )

    lowered = {
        str(k).lower(): str(v)
        for k, v in headers.items()
    }

    for key in keys:
        value = lowered.get(key)

        if value is None:
            continue

        match = re.search(r"\d+", value)

        if match:
            return int(match.group())

    return None


_QUOTA_ALERTED = set()


def _header_number(
    headers: dict[str, str],
    names: tuple[str, ...],
) -> float | None:

    lowered = {
        str(k).lower(): str(v)
        for k, v in headers.items()
    }

    for name in names:
        value = lowered.get(name.lower())

        if value is None:
            continue

        match = re.search(r"[0-9]+(?:\\.[0-9]+)?", value)

        if not match:
            continue

        try:
            return float(match.group())
        except ValueError:
            continue

    return None


def check_quota_alert(
    cfg: ProviderConfig,
    headers: dict[str, str],
) -> None:

    remaining = _header_number(
        headers,
        (
            "x-ratelimit-remaining-tokens",
            "ratelimit-remaining-tokens",
            "x-rate-limit-remaining-tokens",
            "remaining-tokens",
        ),
    )

    limit = _header_number(
        headers,
        (
            "x-ratelimit-limit-tokens",
            "ratelimit-limit-tokens",
            "x-rate-limit-limit-tokens",
            "limit-tokens",
        ),
    )

    # Alguns provedores disponibilizam requests em vez de tokens.
    if remaining is None or limit is None or limit <= 0:
        return

    percent = (remaining / limit) * 100
    key = cfg.name

    if percent <= QUOTA_ALERT_PERCENT:

        if key not in _QUOTA_ALERTED:
            print(
                f"\n[ALERTA TOKEN] {cfg.name.upper()}: "
                f"{remaining:,.0f} de {limit:,.0f} tokens restantes "
                f"({percent:.1f}%)."
            )

            _QUOTA_ALERTED.add(key)

    elif percent > QUOTA_ALERT_PERCENT + 5:

        _QUOTA_ALERTED.discard(key)


def extract_retry_after(headers: dict[str, str]) -> int:
    value = headers.get("Retry-After") or headers.get("retry-after")

    if value:
        match = re.search(r"\d+", str(value))

        if match:
            return max(1, int(match.group()))

    return COOLDOWN_SECONDS


# ============================================================
# MODELOS DA API
# ============================================================

class ChatMessage(BaseModel):
    role: str
    content: Any


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int = Field(
        default=DEFAULT_MAX_TOKENS,
        ge=1,
        le=32768,
    )


# ============================================================
# RESPOSTA INTERNA
# ============================================================

class RouterResult:
    def __init__(
        self,
        provider: str,
        model: str,
        text: str,
        tokens: int = 0,
        raw: dict[str, Any] | None = None,
    ):
        self.provider = provider
        self.model = model
        self.text = text
        self.tokens = tokens
        self.raw = raw or {}


# ============================================================
# UTILIDADES
# ============================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def provider_available(cfg: ProviderConfig) -> bool:
    if not cfg.is_enabled():
        return False

    return bool(cfg.api_key() and cfg.model())


def cooldown_remaining(cfg: ProviderConfig) -> float:
    state = DB.get(cfg.name)

    until = float(state.get("cooldown_until") or 0)

    return max(0.0, until - time.time())


def provider_score(cfg: ProviderConfig) -> float:
    if not provider_available(cfg):
        return -100000.0

    cooldown = cooldown_remaining(cfg)

    if cooldown > 0:
        return -10000.0 - cooldown

    state = DB.get(cfg.name)

    score = 100.0

    remaining_requests = state.get("remaining_requests")
    remaining_tokens = state.get("remaining_tokens")

    if remaining_requests is not None:
        if remaining_requests <= 0:
            return -9000.0

        score += min(40.0, float(remaining_requests) / 10.0)

    elif cfg.rpm():
        score += 20.0

    if remaining_tokens is not None:
        if remaining_tokens <= 0:
            return -9000.0

        score += min(40.0, float(remaining_tokens) / 10000.0)

    elif cfg.tpm():
        score += 10.0

    calls = int(state.get("calls") or 0)
    errors = int(state.get("errors") or 0)
    rate_limits = int(state.get("rate_limits") or 0)
    latency = float(state.get("last_latency") or 0)

    score -= min(30.0, errors * 2.0)
    score -= min(40.0, rate_limits * 4.0)

    if calls > 0:
        score += min(10.0, calls / 20.0)

    if latency > 0:
        score -= min(20.0, latency / 5.0)

    score -= cfg.priority * 0.01

    return score


def ranked_providers() -> list[ProviderConfig]:
    return sorted(
        PROVIDERS,
        key=provider_score,
        reverse=True,
    )


def normalize_content(value: Any) -> str:
    if isinstance(value, str):
        return value

    if isinstance(value, list):
        parts = []

        for item in value:
            if isinstance(item, dict):
                text = item.get("text")

                if text:
                    parts.append(str(text))

        return "\n".join(parts)

    return str(value)


def compact_dialogue_text(value: Any, max_chars: int = DIALOGUE_MAX_CHARS) -> str:
    text = normalize_content(value)

    text = re.sub(r"\\s+", " ", text).strip()

    if len(text) <= max_chars:
        return text

    first = int(max_chars * 0.72)
    last = max_chars - first

    return (
        text[:first].rstrip()
        + " ... "
        + text[-last:].lstrip()
    )


def prepare_dialogue_messages(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    if not messages:
        return [
            {
                "role": "system",
                "content": DIALOGUE_STYLE,
            }
        ]

    system_messages = []
    dialogue_messages = []

    for message in messages:
        role = str(message.get("role", "user"))
        content = compact_dialogue_text(message.get("content", ""))

        if not content:
            continue

        item = {
            "role": role,
            "content": content,
        }

        if role == "system":
            system_messages.append(item)
        else:
            dialogue_messages.append(item)

    dialogue_messages = dialogue_messages[-DIALOGUE_MAX_MESSAGES:]

    if system_messages:
        system = compact_dialogue_text(
            system_messages[0].get("content", ""),
            max_chars=min(3000, DIALOGUE_MAX_CHARS * 2),
        )

        system = f"{system}\n\n{DIALOGUE_STYLE}"

        result = [
            {
                "role": "system",
                "content": system,
            }
        ]

        result.extend(dialogue_messages)
        return result

    return [
        {
            "role": "system",
            "content": DIALOGUE_STYLE,
        },
        *dialogue_messages,
    ]


def estimate_tokens(text: str) -> int:
    if not text:
        return 0

    return max(1, len(text) // 4)


def total_message_tokens(messages: list[dict[str, Any]]) -> int:
    text = "\n".join(
        normalize_content(m.get("content", ""))
        for m in messages
    )

    return estimate_tokens(text)


def economy_max_tokens(
    messages: list[dict[str, Any]],
    requested: int,
) -> int:

    requested = max(64, int(requested))
    requested = min(requested, DIALOGUE_MAX_OUTPUT)

    prompt_tokens = total_message_tokens(messages)

    if prompt_tokens <= 120:
        ceiling = 64
    elif prompt_tokens <= 500:
        ceiling = 96
    else:
        ceiling = 128

    return min(requested, ceiling)

def call_openai_provider(
    cfg: ProviderConfig,
    messages: list[dict[str, Any]],
    temperature: float,
    max_tokens: int,
) -> RouterResult:

    headers = {
        "Authorization": f"Bearer {cfg.api_key()}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": cfg.model(),
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # ========================================================
    # CONTROLE DE REASONING POR PROVEDOR
    # ========================================================
    #
    # Groq/GPT-OSS:
    #   reasoning fica fora do texto principal.
    #
    # Cohere:
    #   reasoning_effort="none" desativa thinking.
    #
    # OpenRouter:
    #   reasoning.effort="none" solicita resposta sem reasoning.
    #
    if cfg.name == "groq":
        payload["include_reasoning"] = False
        payload["reasoning_effort"] = "low"
        payload.pop("max_tokens", None)
        payload["max_completion_tokens"] = max(
            64,
            int(max_tokens),
        )

    elif cfg.name == "cohere":
        payload.pop("reasoning_effort", None)
        payload.pop("reasoning", None)
        payload.pop("include_reasoning", None)

    elif cfg.name == "openrouter":
        payload["reasoning"] = {
            "effort": "none",
            "exclude": True,
        }

        payload["max_tokens"] = max(
            64,
            int(max_tokens),
        )

    started = time.perf_counter()

    chat_url = cfg.base_url.rstrip("/") + "/chat/completions"

    response = requests.post(
        chat_url,
        headers=headers,
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    latency = time.perf_counter() - started

    response_headers = dict(response.headers)

    check_quota_alert(
        cfg,
        response_headers,
    )

    if response.status_code == 429:
        retry_after = extract_retry_after(response_headers)

        DB.record_error(
            cfg.name,
            429,
            response.text,
            latency,
            retry_after,
        )

        raise RuntimeError(
            f"{cfg.name}: rate limit; retry em {retry_after}s"
        )

    if response.status_code in (401, 403):
        DB.record_error(
            cfg.name,
            response.status_code,
            response.text,
            latency,
            300,
        )

        raise RuntimeError(
            f"{cfg.name}: autenticação recusada"
        )

    if response.status_code == 404:
        DB.record_error(
            cfg.name,
            404,
            response.text,
            latency,
            600,
        )

        raise RuntimeError(
            f"{cfg.name}: modelo/endereço indisponível"
        )

    if response.status_code >= 500:
        DB.record_error(
            cfg.name,
            response.status_code,
            response.text,
            latency,
            COOLDOWN_SECONDS,
        )

        raise RuntimeError(
            f"{cfg.name}: servidor indisponível"
        )

    if not response.ok:
        DB.record_error(
            cfg.name,
            response.status_code,
            response.text,
            latency,
            COOLDOWN_SECONDS,
        )

        raise RuntimeError(
            f"{cfg.name}: HTTP {response.status_code}"
        )

    try:
        data = response.json()
    except Exception:
        DB.record_error(
            cfg.name,
            500,
            "JSON inválido",
            latency,
            COOLDOWN_SECONDS,
        )

        raise RuntimeError(
            f"{cfg.name}: resposta JSON inválida"
        )

    choices = data.get("choices") or []

    if not choices:
        DB.record_error(
            cfg.name,
            500,
            "choices vazio",
            latency,
            COOLDOWN_SECONDS,
        )

        raise RuntimeError(
            f"{cfg.name}: resposta sem choices"
        )

    message = choices[0].get("message") or {}

    text = message.get("content", "")

    if not text and isinstance(message.get("content"), list):
        partes = []

        for item in message.get("content") or []:
            if isinstance(item, dict):
                texto_item = item.get("text")

                if texto_item:
                    partes.append(str(texto_item))

        text = "".join(partes)

    text = normalize_content(text)

    if not text.strip():
        DB.record_error(
            cfg.name,
            500,
            "conteúdo vazio",
            latency,
            COOLDOWN_SECONDS,
        )

        raise RuntimeError(
            f"{cfg.name}: resposta vazia"
        )

    usage = data.get("usage") or {}

    tokens = int(
        usage.get("total_tokens")
        or usage.get("completion_tokens")
        or estimate_tokens(text)
    )

    DB.record_success(
        cfg.name,
        response.status_code,
        tokens,
        latency,
        response_headers,
    )

    return RouterResult(
        provider=cfg.name,
        model=cfg.model(),
        text=text.strip(),
        tokens=tokens,
        raw=data,
    )


# ============================================================
# GEMINI
# ============================================================

def call_gemini(
    cfg: ProviderConfig,
    messages: list[dict[str, Any]],
    temperature: float,
    max_tokens: int,
) -> RouterResult:

    system_parts = []
    contents = []

    for message in messages:
        role = str(message.get("role", "user"))
        content = normalize_content(message.get("content", ""))

        if role == "system":
            system_parts.append(content)
            continue

        gemini_role = "model" if role == "assistant" else "user"

        contents.append(
            {
                "role": gemini_role,
                "parts": [
                    {
                        "text": content
                    }
                ],
            }
        )

    payload: dict[str, Any] = {
        "contents": contents,
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max(
                64,
                int(max_tokens),
            ),
            "thinkingConfig": {
                "thinkingLevel": "low",
            },
        },
    }

    if system_parts:
        payload["systemInstruction"] = {
            "parts": [
                {
                    "text": "\n".join(system_parts)
                }
            ]
        }

    url = (
        cfg.base_url.rstrip("/")
        + "/models/"
        + cfg.model()
        + ":generateContent"
    )

    headers = {
        "x-goog-api-key": cfg.api_key(),
        "Content-Type": "application/json",
    }

    started = time.perf_counter()

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )

    latency = time.perf_counter() - started

    response_headers = dict(response.headers)

    check_quota_alert(
        cfg,
        response_headers,
    )

    if response.status_code == 429:
        retry_after = extract_retry_after(response_headers)

        DB.record_error(
            cfg.name,
            429,
            response.text,
            latency,
            retry_after,
        )

        raise RuntimeError(
            f"{cfg.name}: rate limit; retry em {retry_after}s"
        )

    if response.status_code in (401, 403):
        DB.record_error(
            cfg.name,
            response.status_code,
            response.text,
            latency,
            300,
        )

        raise RuntimeError(
            f"{cfg.name}: autenticação recusada"
        )

    if response.status_code == 404:
        DB.record_error(
            cfg.name,
            404,
            response.text,
            latency,
            600,
        )

        raise RuntimeError(
            f"{cfg.name}: modelo indisponível"
        )

    if response.status_code >= 500:
        DB.record_error(
            cfg.name,
            response.status_code,
            response.text,
            latency,
            COOLDOWN_SECONDS,
        )

        raise RuntimeError(
            f"{cfg.name}: servidor indisponível"
        )

    if not response.ok:
        DB.record_error(
            cfg.name,
            response.status_code,
            response.text,
            latency,
            COOLDOWN_SECONDS,
        )

        raise RuntimeError(
            f"{cfg.name}: HTTP {response.status_code}"
        )

    try:
        data = response.json()
    except Exception:
        DB.record_error(
            cfg.name,
            500,
            "JSON inválido",
            latency,
            COOLDOWN_SECONDS,
        )

        raise RuntimeError(
            f"{cfg.name}: JSON inválido"
        )

    candidates = data.get("candidates") or []

    if not candidates:
        DB.record_error(
            cfg.name,
            500,
            "candidates vazio",
            latency,
            COOLDOWN_SECONDS,
        )

        raise RuntimeError(
            f"{cfg.name}: resposta sem candidates"
        )

    parts = (
        candidates[0]
        .get("content", {})
        .get("parts", [])
    )

    text_parts = []

    for part in parts:
        if isinstance(part, dict) and part.get("text"):
            text_parts.append(str(part["text"]))

    text = "\n".join(text_parts).strip()

    if not text:
        DB.record_error(
            cfg.name,
            500,
            "texto vazio",
            latency,
            COOLDOWN_SECONDS,
        )

        raise RuntimeError(
            f"{cfg.name}: resposta vazia"
        )

    usage_metadata = data.get("usageMetadata") or {}

    tokens = int(
        usage_metadata.get("totalTokenCount")
        or estimate_tokens(text)
    )

    DB.record_success(
        cfg.name,
        response.status_code,
        tokens,
        latency,
        response_headers,
    )

    return RouterResult(
        provider=cfg.name,
        model=cfg.model(),
        text=text,
        tokens=tokens,
        raw=data,
    )


# ============================================================
# ROUTER
# ============================================================

class AIRouter:

    def __init__(self):
        self.lock = threading.RLock()

    def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> RouterResult:

        last_error = None

        messages = prepare_dialogue_messages(
            messages,
        )

        max_tokens = economy_max_tokens(
            messages,
            max_tokens,
        )

        providers = ranked_providers()

        if not providers:
            raise RuntimeError(
                "Nenhum provedor configurado."
            )

        for cfg in providers:

            if not provider_available(cfg):
                continue

            if cooldown_remaining(cfg) > 0:
                continue

            for attempt in range(MAX_RETRIES + 1):

                try:

                    if cfg.style == "gemini":
                        return call_gemini(
                            cfg,
                            messages,
                            temperature,
                            max_tokens,
                        )

                    return call_openai_provider(
                        cfg,
                        messages,
                        temperature,
                        max_tokens,
                    )

                except Exception as exc:

                    last_error = str(exc)

                    if attempt < MAX_RETRIES:
                        time.sleep(0.5)
                        continue

                    break

        raise RuntimeError(
            "Todos os provedores disponíveis falharam. "
            f"Último erro: {last_error}"
        )


ROUTER = AIRouter()


# ============================================================
# FASTAPI
# ============================================================


def outbound_allowed(url: str) -> bool:
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        if not host:
            return False

        if not OUTBOUND_ALLOWLIST:
            return False

        return any(
            host == dominio
            or host.endswith("." + dominio)
            for dominio in OUTBOUND_ALLOWLIST
        )

    except Exception:
        return False


def outbound_request(
    url: str,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    payload: Any = None,
) -> dict[str, Any]:

    if not outbound_allowed(url):
        raise RuntimeError(
            "Outbound bloqueado: dominio nao esta "
            "na OUTBOUND_ALLOWLIST."
        )

    method = method.upper().strip()

    if method not in {
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
    }:
        raise RuntimeError(
            f"Metodo HTTP nao permitido: {method}"
        )

    response = requests.request(
        method=method,
        url=url,
        headers=headers or {},
        json=payload if method != "GET" else None,
        timeout=OUTBOUND_TIMEOUT,
    )

    content_type = (
        response.headers.get(
            "content-type",
            ""
        ).lower()
    )

    if "application/json" in content_type:
        try:
            data = response.json()
        except Exception:
            data = response.text
    else:
        data = response.text

    return {
        "ok": response.ok,
        "status_code": response.status_code,
        "url": url,
        "method": method,
        "data": data,
    }


app = FastAPI(
    title="JARVIS IA Router",
    version="1.0.0",
    description="Roteador unificado de APIs de IA para o JARVIS.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def check_router_key(authorization: str | None):
    if not ROUTER_API_KEY:
        return

    expected = f"Bearer {ROUTER_API_KEY}"

    if authorization != expected:
        raise HTTPException(
            status_code=401,
            detail="Router API key inválida.",
        )


# ============================================================
# ENDPOINTS
# ============================================================

@app.get("/")
def root():
    return {
        "service": "JARVIS IA Router",
        "version": "1.0.0",
        "status": "online",
        "time": now_iso(),
    }


@app.get("/status")
def status():
    providers = []

    for cfg in PROVIDERS:
        state = DB.get(cfg.name)

        providers.append(
            {
                "name": cfg.name,
                "configured": bool(
                    cfg.api_key()
                    and cfg.model()
                ),
                "model": cfg.model(),
                "cooldown": round(
                    cooldown_remaining(cfg),
                    2,
                ),
                "score": round(
                    provider_score(cfg),
                    2,
                ),
                "calls": state.get("calls", 0),
                "errors": state.get("errors", 0),
                "rate_limits": state.get("rate_limits", 0),
                "tokens": state.get("tokens", 0),
                "last_status": state.get(
                    "last_status",
                    0,
                ),
                "last_latency": state.get(
                    "last_latency",
                    0,
                ),
                "remaining_requests": state.get(
                    "remaining_requests"
                ),
                "remaining_tokens": state.get(
                    "remaining_tokens"
                ),
            }
        )

    return {
        "service": "JARVIS IA Router",
        "status": "online",
        "providers": providers,
        "selected_order": [
            p.name
            for p in ranked_providers()
            if provider_available(p)
        ],
        "time": now_iso(),
    }


@app.get("/providers")
def providers():
    result = []

    for cfg in ranked_providers():
        result.append(
            {
                "name": cfg.name,
                "configured": provider_available(cfg),
                "model": cfg.model(),
                "style": cfg.style,
                "score": round(
                    provider_score(cfg),
                    2,
                ),
                "cooldown": round(
                    cooldown_remaining(cfg),
                    2,
                ),
            }
        )

    return {
        "providers": result
    }


@app.get("/usage")
def usage():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT
            provider,
            calls,
            errors,
            rate_limits,
            tokens,
            prompt_tokens,
            output_tokens,
            last_status,
            last_error,
            last_latency,
            remaining_requests,
            request_limit,
            remaining_tokens,
            token_limit,
            quota_period,
            quota_reset,
            quota_source,
            quota_checked_at,
            cooldown_until,
            updated_at
        FROM provider_usage
        ORDER BY provider
        """
    ).fetchall()

    conn.close()

    resultado = []

    for row in rows:
        item = dict(row)

        remaining_tokens = item.get("remaining_tokens")
        token_limit = item.get("token_limit")

        remaining_requests = item.get("remaining_requests")
        request_limit = item.get("request_limit")

        if (
            remaining_tokens is not None
            and token_limit is not None
            and token_limit > 0
        ):
            item["token_percent_remaining"] = round(
                (remaining_tokens / token_limit) * 100,
                2,
            )
        else:
            item["token_percent_remaining"] = None

        if (
            remaining_requests is not None
            and request_limit is not None
            and request_limit > 0
        ):
            item["request_percent_remaining"] = round(
                (remaining_requests / request_limit) * 100,
                2,
            )
        else:
            item["request_percent_remaining"] = None

        resultado.append(item)

    return {
        "status": "online",
        "providers": resultado,
        "quota_policy": {
            "alert_percent": QUOTA_ALERT_PERCENT,
            "invented_limits": False,
        },
    }



@app.get("/v1/models")
def models(
    authorization: str | None = Header(default=None)
):
    check_router_key(authorization)

    data = []

    for cfg in PROVIDERS:

        if not provider_available(cfg):
            continue

        data.append(
            {
                "id": cfg.model(),
                "object": "model",
                "owned_by": cfg.name,
            }
        )

    return {
        "object": "list",
        "data": data,
    }



class OutboundRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: dict[str, str] = Field(
        default_factory=dict
    )
    payload: Any = None


@app.post("/quota")
def update_quota(payload: dict):
    provider = str(payload.get("provider", "")).strip()

    if not provider:
        raise HTTPException(
            status_code=400,
            detail="provider obrigatório",
        )

    DB.record_quota(
        provider=provider,
        remaining_requests=payload.get("remaining_requests"),
        request_limit=payload.get("limit_requests"),
        remaining_tokens=payload.get("remaining_tokens"),
        token_limit=payload.get("limit_tokens"),
        quota_period=payload.get("period"),
        quota_reset=payload.get("reset"),
        quota_source=payload.get("source"),
    )

    return {
        "status": "ok",
        "provider": provider,
        "quota_recorded": True,
    }


@app.post("/outbound")
def outbound(
    request: OutboundRequest,
):
    try:
        return outbound_request(
            url=request.url,
            method=request.method,
            headers=request.headers,
            payload=request.payload,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        )



@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):
    await websocket.accept()

    try:

        await websocket.send_json({
            "type": "connected",
            "service": "IA_ROUTER",
            "status": "online",
        })

        while True:

            mensagem = await websocket.receive_json()

            tipo = mensagem.get("type", "")

            if tipo == "ping":

                await websocket.send_json({
                    "type": "pong",
                    "status": "online",
                })

                continue

            if tipo == "status":

                estados = []

                for cfg in PROVIDERS:
                    estados.append({
                        "provider": cfg.name,
                        "enabled": cfg.is_enabled(),
                        "available": provider_available(cfg),
                        "model": cfg.model(),
                    })

                await websocket.send_json({
                    "type": "status",
                    "providers": estados,
                })

                continue

            await websocket.send_json({
                "type": "error",
                "error": "Tipo de mensagem desconhecido.",
            })

    except WebSocketDisconnect:
        pass


@app.post("/v1/chat/completions")
def chat_completions(
    request: ChatRequest,
    authorization: str | None = Header(default=None),
):
    check_router_key(authorization)

    if not request.messages:
        raise HTTPException(
            status_code=400,
            detail="messages não pode ser vazio.",
        )

    messages = [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in request.messages
    ]

    try:

        result = ROUTER.chat(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    created = int(time.time())

    return {
        "id": f"jarvis-router-{created}",
        "object": "chat.completion",
        "created": created,
        "model": result.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": result.text,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": total_message_tokens(
                messages
            ),
            "completion_tokens": result.tokens,
            "total_tokens": (
                total_message_tokens(messages)
                + result.tokens
            ),
        },
        "router": {
            "provider": result.provider,
        },
    }


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    import uvicorn

    print("")
    print("=" * 60)
    print("JARVIS IA ROUTER")
    print("=" * 60)
    print(f"Diretório: {BASE_DIR}")
    print(f"Banco:     {DB_PATH}")
    print("Endpoint:  http://127.0.0.1:8765")
    print("")

    configured = [
        cfg
        for cfg in PROVIDERS
        if provider_available(cfg)
    ]

    if configured:
        print("PROVEDORES CONFIGURADOS:")

        for cfg in configured:
            print(
                f"  [OK] {cfg.name:<12} "
                f"{cfg.model()}"
            )
    else:
        print(
            "ATENÇÃO: nenhuma API configurada."
        )
        print(
            "Copie .env.example para .env "
            "e adicione pelo menos uma chave."
        )

    print("")
    print("Iniciando servidor...")
    print("")

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8765,
    )



