from __future__ import annotations

import json
import traceback

from ai.classificador_intencao import obter_classificador


classificador = obter_classificador()

testes = [

    ("01", "Qual é o meu time?",
     "conversa_geral"),

    ("02", "Qual é o meu nome?",
     "conversa_geral"),

    ("03", "Qual é o nome da minha esposa?",
     "conversa_geral"),

    ("04", "Onde eu moro?",
     "conversa_geral"),

    ("05", "Com o que eu trabalho?",
     "conversa_geral"),

    ("06", "Qual é minha comida favorita?",
     "conversa_geral"),

    ("07", "Olá JARVIS, tudo bem?",
     "conversa_geral"),

    ("08", "Me diga uma piada.",
     "conversa_geral"),

    ("09", "Abra o bloco de notas.",
     "operacional"),

    ("10", "Pesquise na internet o preço da GTX 1650.",
     "pesquisa_geral"),
]


print()
print("=" * 100)
print("J.A.R.V.I.S — INVESTIGAÇÃO DO CONTRATO DA TRIAGEM")
print("=" * 100)

falhas = []

for numero, entrada, esperado in testes:

    try:

        resultado = classificador.classificar(
            entrada
        )

        intencao = str(
            resultado.get(
                "intencao",
                ""
            )
        ).strip()

        aceita = resultado.get(
            "aceita"
        )

        confianca = resultado.get(
            "confianca"
        )

        referencia = resultado.get(
            "referencia",
            ""
        )

        ok_intencao = (
            intencao == esperado
        )

        # Para conversa_geral, aceita=False pode ser perfeitamente
        # válido se ela for o fallback de baixa confiança.
        if esperado == "conversa_geral":

            ok_contrato = (
                intencao
                == "conversa_geral"
            )

        else:

            ok_contrato = (
                intencao
                == esperado
                and
                aceita is True
            )

        ok = (
            ok_intencao
            and
            ok_contrato
        )

        print()
        print("-" * 100)
        print(
            f"[{'OK' if ok else 'FALHA'}] TESTE {numero}"
        )
        print(
            f"ENTRADA   : {entrada}"
        )
        print(
            f"ESPERADO  : {esperado}"
        )
        print(
            f"INTENÇÃO  : {intencao}"
        )
        print(
            f"ACEITA    : {aceita}"
        )
        print(
            f"CONFIANÇA : {confianca}"
        )
        print(
            f"REFERÊNCIA: {referencia}"
        )
        print(
            f"JSON      : {json.dumps(resultado, ensure_ascii=False)}"
        )

        if not ok:
            falhas.append(
                {
                    "numero": numero,
                    "entrada": entrada,
                    "esperado": esperado,
                    "resultado": resultado,
                }
            )

    except Exception as erro:

        falhas.append(
            {
                "numero": numero,
                "entrada": entrada,
                "erro": traceback.format_exc(),
            }
        )

        print()
        print("-" * 100)
        print(
            f"[EXCEÇÃO] TESTE {numero}"
        )
        print(
            traceback.format_exc()
        )


print()
print("=" * 100)
print("ANÁLISE")
print("=" * 100)

if not falhas:

    print()
    print("OK — o contrato atual da triagem está consistente.")
    print(
        "conversa_geral pode ser fallback mesmo quando aceita=False."
    )

else:

    print()
    print(
        f"FALHAS: {len(falhas)}"
    )

    for falha in falhas:

        print()
        print("-" * 100)
        print(
            f"TESTE {falha.get('numero')}"
        )
        print(
            f"ENTRADA: {falha.get('entrada')}"
        )

        if "erro" in falha:
            print(
                falha["erro"]
            )
        else:
            print(
                "ESPERADO:",
                falha["esperado"]
            )
            print(
                "OBTIDO:",
                json.dumps(
                    falha["resultado"],
                    ensure_ascii=False
                )
            )

print()
print("=" * 100)
print("CONCLUSÃO")
print("=" * 100)

print()
print(
    "Regra importante:"
)
print(
    "Para conversa_geral, o campo 'aceita' NÃO deve ser usado como"
)
print(
    "condição obrigatória para permitir resposta normal."
)
print(
    "A triagem deve usar 'intencao' para rotear e 'aceita' para"
)
print(
    "medir confiança da classificação específica."
)
print()
