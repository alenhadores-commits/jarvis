from pathlib import Path

p = Path("teste_7_provedores.py")

conteudo = r'''
import time

from api_router import (
    PROVIDERS,
    provider_available,
    call_openai_provider,
    call_gemini,
)

# ============================================================
# PROVEDORES PENDENTES
# ============================================================
# APROVADOS E REMOVIDOS DOS TESTES:
#   groq
#   openrouter
#   cohere
#
# Somente estes continuam sendo testados:
# ============================================================

ALVOS = {
    "cerebras",
    "gemini",
    "mistral",
    "nvidia",
    "huggingface",
    "sambanova",
}

MENSAGENS = [
    {
        "role": "user",
        "content": "Responda somente: OK",
    }
]

resultados = []

print()
print("=" * 72)
print("IA ROUTER - TESTE DOS PROVEDORES PENDENTES")
print("=" * 72)
print()
print("APROVADOS E FORA DOS TESTES:")
print("  [OK] groq")
print("  [OK] openrouter")
print("  [OK] cohere")
print()

for cfg in PROVIDERS:

    if cfg.name not in ALVOS:
        continue

    print("-" * 72)
    print(f"PROVEDOR : {cfg.name}")
    print(f"MODELO   : {cfg.model()}")
    print(f"ENABLED  : {cfg.is_enabled()}")
    print(f"AVAILABLE: {provider_available(cfg)}")

    if not provider_available(cfg):
        print("RESULTADO: INDISPONIVEL")
        resultados.append(
            (cfg.name, "INDISPONIVEL", 0.0)
        )
        continue

    inicio = time.perf_counter()

    try:

        if cfg.style == "gemini":
            resultado = call_gemini(
                cfg,
                MENSAGENS,
                0.0,
                64,
            )
        else:
            resultado = call_openai_provider(
                cfg,
                MENSAGENS,
                0.0,
                64,
            )

        tempo = time.perf_counter() - inicio

        texto = str(
            resultado.text or ""
        ).strip()

        print(f"TEMPO    : {tempo:.2f}s")
        print(f"RESPOSTA : {texto[:200]}")
        print(f"TOKENS   : {resultado.tokens}")
        print("RESULTADO: OK")

        resultados.append(
            (cfg.name, "OK", tempo)
        )

    except Exception as exc:

        tempo = time.perf_counter() - inicio

        erro = (
            str(exc)
            .replace("\r", " ")
            .replace("\n", " ")
            .strip()
        )

        if len(erro) > 500:
            erro = erro[:500] + "..."

        print(f"TEMPO    : {tempo:.2f}s")
        print(f"ERRO     : {erro}")
        print("RESULTADO: FALHOU")

        resultados.append(
            (cfg.name, "FALHOU", tempo)
        )

print()
print("=" * 72)
print("RESUMO")
print("=" * 72)

for nome, status, tempo in resultados:
    print(
        f"{nome:<14} "
        f"{status:<14} "
        f"{tempo:>7.2f}s"
    )

aprovados = [
    nome
    for nome, status, tempo in resultados
    if status == "OK"
]

falharam = [
    nome
    for nome, status, tempo in resultados
    if status == "FALHOU"
]

print()
print(f"APROVADOS NESTE TESTE: {len(aprovados)}")
print(f"AINDA COM FALHA       : {len(falharam)}")

if aprovados:
    print()
    print("NOVOS APROVADOS:")
    for nome in aprovados:
        print(f"  [OK] {nome}")

if falharam:
    print()
    print("AINDA PENDENTES:")
    for nome in falharam:
        print(f"  [X] {nome}")

print()
print("=" * 72)
print("POOL ATUALMENTE APROVADO")
print("=" * 72)
print("[OK] groq")
print("[OK] openrouter")
print("[OK] cohere")

for nome in aprovados:
    print(f"[OK] {nome}")

print("=" * 72)
'''

p.write_text(conteudo, encoding="utf-8")

print("TESTE ATUALIZADO.")
print("Os aprovados foram retirados da lista de testes.")
print("Somente os provedores pendentes serão testados.")
