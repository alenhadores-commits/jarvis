import time
import traceback

from api_router import (
    PROVIDERS,
    DB,
    provider_available,
    call_openai_provider,
    call_gemini,
)

mensagens = [
    {
        "role": "user",
        "content": "Responda somente: OK",
    }
]

resultados = []

print()
print("=" * 72)
print("JARVIS IA ROUTER - AUDITORIA DOS PROVEDORES")
print("=" * 72)
print()

for cfg in PROVIDERS:

    print("-" * 72)
    print(f"PROVEDOR : {cfg.name}")
    print(f"MODELO   : {cfg.model()}")
    print(f"ENABLED  : {cfg.is_enabled()}")
    print(f"AVAILABLE: {provider_available(cfg)}")

    if not cfg.is_enabled():
        print("RESULTADO: IGNORADO - desabilitado")
        resultados.append({
            "provider": cfg.name,
            "status": "DESABILITADO",
            "tempo": 0,
            "resposta": "",
        })
        continue

    if not provider_available(cfg):
        print("RESULTADO: IGNORADO - sem chave/modelo disponível")
        resultados.append({
            "provider": cfg.name,
            "status": "INDISPONIVEL",
            "tempo": 0,
            "resposta": "",
        })
        continue

    inicio = time.perf_counter()

    try:
        if cfg.style == "gemini":
            resultado = call_gemini(
                cfg,
                mensagens,
                0.0,
                64,
            )
        else:
            resultado = call_openai_provider(
                cfg,
                mensagens,
                0.0,
                64,
            )

        tempo = time.perf_counter() - inicio

        texto = str(resultado.text or "").strip()

        print(f"TEMPO    : {tempo:.2f}s")
        print(f"RESPOSTA : {texto[:300]}")
        print(f"TOKENS   : {resultado.tokens}")
        print("RESULTADO: OK")

        resultados.append({
            "provider": cfg.name,
            "status": "OK",
            "tempo": tempo,
            "resposta": texto,
        })

    except Exception as exc:

        tempo = time.perf_counter() - inicio

        erro = str(exc).replace("\r", " ").replace("\n", " ").strip()

        if len(erro) > 500:
            erro = erro[:500] + "..."

        print(f"TEMPO    : {tempo:.2f}s")
        print(f"ERRO     : {erro}")
        print("RESULTADO: FALHOU")

        resultados.append({
            "provider": cfg.name,
            "status": "FALHOU",
            "tempo": tempo,
            "resposta": erro,
        })

print()
print()
print("=" * 72)
print("RESUMO FINAL")
print("=" * 72)
print()

for item in resultados:
    print(
        f"{item['provider']:<14} "
        f"{item['status']:<13} "
        f"{item['tempo']:>7.2f}s"
    )

print()
print("=" * 72)

ok = [
    item
    for item in resultados
    if item["status"] == "OK"
]

falhas = [
    item
    for item in resultados
    if item["status"] == "FALHOU"
]

print(f"FUNCIONANDO : {len(ok)}")
print(f"FALHANDO    : {len(falhas)}")
print(f"TOTAL       : {len(resultados)}")
print("=" * 72)

if ok:
    print()
    print("PROVEDORES FUNCIONANDO:")
    for item in ok:
        print(
            f"  - {item['provider']} "
            f"({item['tempo']:.2f}s)"
        )

if falhas:
    print()
    print("PROVEDORES COM FALHA:")
    for item in falhas:
        print(f"  - {item['provider']}")

print()
print("AUDITORIA CONCLUIDA.")
