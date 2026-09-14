from pathlib import Path

p = Path("api_router.py")
s = p.read_text(encoding="utf-8")

# ============================================================
# 1. MODELOS DOS PROVEDORES QUE FALHARAM
# ============================================================

s = s.replace(
    'GEMINI_MODEL", "gemini-3.7-flash"',
    'GEMINI_MODEL", "gemini-3.8-flash"'
)

s = s.replace(
    'NVIDIA_MODEL", "meta/llama-3.1-8b-instruct"',
    'NVIDIA_MODEL", "meta/llama-3.3-70b-instruct"'
)

s = s.replace(
    'HUGGINGFACE_MODEL", "openai/gpt-oss-120b:fastest"',
    'HUGGINGFACE_MODEL", "deepseek-ai/DeepSeek-V3-0324"'
)

# ============================================================
# 2. GEMINI
# ============================================================

s = s.replace(
    'if cfg.name == "gemini":',
    'if cfg.name == "gemini":'
)

# ============================================================
# 3. COHERE
# ============================================================
# reasoning_effort="none" é oficialmente suportado.
# Mantemos o modelo atual e apenas garantimos que não sejam
# enviados parâmetros específicos de outros provedores.

s = s.replace(
'''    elif cfg.name == "cohere":
        payload["reasoning_effort"] = "none"
''',
'''    elif cfg.name == "cohere":
        payload["reasoning_effort"] = "none"
        payload.pop("reasoning", None)
        payload.pop("include_reasoning", None)
''',
)

# ============================================================
# 4. MELHORAR DIAGNÓSTICO DOS 7 PROVEDORES
# ============================================================
# Não altera Groq/OpenRouter.
# Mantém o erro limpo, mas captura o corpo retornado pela API
# para sabermos se é quota, autenticação, modelo ou payload.

old = '''    if response.status_code >= 400:

        if response.status_code == 429:
            retry_after = extract_retry_after(response_headers)

            DB.record_error(
                cfg.name,
                response.status_code,
                "rate limit",
                latency,
                response_headers,
                rate_limit=True,
            )

            raise RuntimeError(
                f"{cfg.name}: rate limit; "
                f"retry em {retry_after}s"
            )

        DB.record_error(
            cfg.name,
            response.status_code,
            f"HTTP {response.status_code}",
            latency,
            response_headers,
        )

        raise RuntimeError(
            f"{cfg.name}: HTTP {response.status_code}"
        )
'''

new = '''    if response.status_code >= 400:

        corpo = ""

        try:
            erro_json = response.json()

            if isinstance(erro_json, dict):
                erro_obj = erro_json.get("error")

                if isinstance(erro_obj, dict):
                    corpo = (
                        erro_obj.get("message")
                        or erro_obj.get("detail")
                        or erro_obj.get("code")
                        or ""
                    )
                else:
                    corpo = (
                        erro_json.get("message")
                        or erro_json.get("detail")
                        or ""
                    )

        except Exception:
            corpo = ""

        if not corpo:
            corpo = response.text.strip()

        corpo = str(corpo).replace("\\r", " ").replace("\\n", " ")

        if len(corpo) > 400:
            corpo = corpo[:400] + "..."

        if response.status_code == 429:

            retry_after = extract_retry_after(response_headers)

            DB.record_error(
                cfg.name,
                response.status_code,
                corpo or "rate limit",
                latency,
                response_headers,
                rate_limit=True,
            )

            raise RuntimeError(
                f"{cfg.name}: rate limit; "
                f"retry em {retry_after}s"
            )

        DB.record_error(
            cfg.name,
            response.status_code,
            corpo or f"HTTP {response.status_code}",
            latency,
            response_headers,
        )

        raise RuntimeError(
            f"{cfg.name}: HTTP {response.status_code}"
            + (f" - {corpo}" if corpo else "")
        )
'''

if old not in s:
    raise RuntimeError(
        "Bloco de tratamento HTTP esperado não foi encontrado. "
        "Nenhuma alteração foi salva."
    )

s = s.replace(old, new)

p.write_text(s, encoding="utf-8")

print("PATCH APLICADO")
print("Backup:", Path(r"$backup"))
