# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import statistics
import time
import traceback
from collections import Counter, defaultdict

from ai.classificador_intencao import obter_classificador
from ai.cerebro import perguntar
from memoria_retriever import MemoriaRetriever


print()
print("=" * 110)
print("J.A.R.V.I.S — TESTE DE ESTRESSE REAL")
print("=" * 110)
print()

classificador = obter_classificador()
retriever = MemoriaRetriever()

# ------------------------------------------------------------
# CENÁRIOS REAIS BASEADOS NAS MEMÓRIAS ATUAIS
# ------------------------------------------------------------

casos = [
    {
        "nome": "nome",
        "pergunta": "Qual é o meu nome?",
        "esperado": ["alex"],
        "tipo": "NOME",
    },
    {
        "nome": "esposa",
        "pergunta": "Qual é o nome da minha esposa?",
        "esperado": ["mariana praxedes"],
        "tipo": "FAMILIA",
    },
    {
        "nome": "cidade",
        "pergunta": "Qual cidade eu moro?",
        "esperado": ["maribondo", "alagoas"],
        "tipo": None,
    },
    {
        "nome": "time",
        "pergunta": "Qual é o meu time?",
        "esperado": ["palmeiras"],
        "tipo": "ESPORTE",
    },
    {
        "nome": "trabalho",
        "pergunta": "Com o que eu trabalho?",
        "esperado": ["dentista"],
        "tipo": "TRABALHO",
    },
    {
        "nome": "comida",
        "pergunta": "Qual é minha comida favorita?",
        "esperado": ["pizza"],
        "tipo": "COMIDA",
    },
    {
        "nome": "animal",
        "pergunta": "Qual é meu animal favorito?",
        "esperado": ["cachorro"],
        "tipo": "ANIMAL",
    },
    {
        "nome": "projeto",
        "pergunta": "Qual é meu principal projeto?",
        "esperado": ["jarvis"],
        "tipo": "PROJETO",
    },
]

# ------------------------------------------------------------
# REPETIÇÕES
# ------------------------------------------------------------

REPETICOES_RETRIEVER = 15
REPETICOES_QWEN = 3

print(
    f"Consultas: {len(casos)}"
)
print(
    f"Repetições Retriever por consulta: {REPETICOES_RETRIEVER}"
)
print(
    f"Repetições Qwen por consulta: {REPETICOES_QWEN}"
)
print()

falhas = []
tempos_retriever = []
tempos_qwen = []

contagem_tipo = Counter()
consistencia = defaultdict(list)

inicio_total = time.perf_counter()

# ------------------------------------------------------------
# FASE 1 — RETRIEVER
# ------------------------------------------------------------

print("=" * 110)
print("FASE 1 — ESTRESSE DO RETRIEVER")
print("=" * 110)

for caso in casos:

    print()
    print(
        f"[{caso['nome'].upper()}] {caso['pergunta']}"
    )

    tipos = []
    top_ids = []
    sucessos = 0

    for rodada in range(
        1,
        REPETICOES_RETRIEVER + 1
    ):

        try:

            inicio = time.perf_counter()

            tipo = retriever.inferir_tipo(
                caso["pergunta"]
            )

            resultados = retriever.buscar(
                caso["pergunta"]
            )

            contexto = retriever.contexto(
                caso["pergunta"]
            )

            tempo = time.perf_counter() - inicio

            tempos_retriever.append(
                tempo
            )

            tipos.append(
                str(tipo)
            )

            top = (
                resultados[0]
                if resultados
                else {}
            )

            top_id = str(
                top.get(
                    "id",
                    ""
                )
            )

            top_ids.append(
                top_id
            )

            texto = contexto.lower()

            conteudo_ok = all(
                termo.lower() in texto
                for termo in caso["esperado"]
            )

            tipo_ok = (
                caso["tipo"] is None
                or
                tipo == caso["tipo"]
            )

            sucesso = (
                conteudo_ok
                and tipo_ok
            )

            if sucesso:
                sucessos += 1

            else:

                falhas.append(
                    {
                        "fase": "RETRIEVER",
                        "caso": caso["nome"],
                        "rodada": rodada,
                        "pergunta": caso["pergunta"],
                        "tipo": tipo,
                        "top": top,
                        "contexto": contexto,
                    }
                )

        except Exception as erro:

            falhas.append(
                {
                    "fase": "RETRIEVER",
                    "caso": caso["nome"],
                    "rodada": rodada,
                    "pergunta": caso["pergunta"],
                    "erro": traceback.format_exc(),
                }
            )

    tipo_unico = set(
        tipos
    )

    top_unico = set(
        top_ids
    )

    consistente = (
        len(tipo_unico) <= 1
        and
        len(top_unico) <= 1
    )

    print(
        f"  Acertos: {sucessos}/{REPETICOES_RETRIEVER}"
    )

    print(
        f"  Tipos: {sorted(tipo_unico)}"
    )

    print(
        f"  Top IDs diferentes: {len(top_unico)}"
    )

    print(
        f"  Consistência: {'OK' if consistente else 'FALHA'}"
    )


# ------------------------------------------------------------
# FASE 2 — TRIAGEM
# ------------------------------------------------------------

print()
print("=" * 110)
print("FASE 2 — ESTRESSE DA TRIAGEM")
print("=" * 110)

triagem_casos = [
    "Qual é o meu nome?",
    "Qual é o nome da minha esposa?",
    "Qual é o meu time?",
    "Onde eu moro?",
    "Com o que eu trabalho?",
    "Qual é minha comida favorita?",
    "Qual é meu animal favorito?",
    "Qual é meu principal projeto?",
    "Olá JARVIS, tudo bem?",
    "Me diga uma piada.",
    "Abra o bloco de notas.",
    "Pesquise na internet o preço da GTX 1650.",
]

for pergunta in triagem_casos:

    try:

        resultado = classificador.classificar(
            pergunta
        )

        print(
            f"OK | {pergunta} | "
            f"{resultado.get('intencao')} | "
            f"conf={resultado.get('confianca')}"
        )

    except Exception as erro:

        falhas.append(
            {
                "fase": "TRIAGEM",
                "pergunta": pergunta,
                "erro": traceback.format_exc(),
            }
        )

        print(
            f"FALHA | {pergunta} | {erro}"
        )


# ------------------------------------------------------------
# FASE 3 — QWEN
# ------------------------------------------------------------

print()
print("=" * 110)
print("FASE 3 — ESTRESSE DO QWEN")
print("=" * 110)

for caso in casos:

    print()
    print(
        f"[{caso['nome'].upper()}] {caso['pergunta']}"
    )

    respostas = []

    for rodada in range(
        1,
        REPETICOES_QWEN + 1
    ):

        try:

            contexto = retriever.contexto(
                caso["pergunta"]
            )

            inicio = time.perf_counter()

            resposta = perguntar(
                caso["pergunta"],
                contexto
            )

            tempo = time.perf_counter() - inicio

            tempos_qwen.append(
                tempo
            )

            resposta_texto = str(
                resposta
            ).strip()

            respostas.append(
                resposta_texto
            )

            texto = resposta_texto.lower()

            ok = all(
                termo.lower() in texto
                for termo in caso["esperado"]
            )

            print(
                f"  {'OK' if ok else 'FALHA'} "
                f"rodada {rodada}: "
                f"{resposta_texto}"
            )

            if not ok:

                falhas.append(
                    {
                        "fase": "QWEN",
                        "caso": caso["nome"],
                        "rodada": rodada,
                        "pergunta": caso["pergunta"],
                        "esperado": caso["esperado"],
                        "contexto": contexto,
                        "resposta": resposta_texto,
                    }
                )

        except Exception as erro:

            falhas.append(
                {
                    "fase": "QWEN",
                    "caso": caso["nome"],
                    "rodada": rodada,
                    "pergunta": caso["pergunta"],
                    "erro": traceback.format_exc(),
                }
            )


# ------------------------------------------------------------
# FASE 4 — VERDADE / MENTIRA
# ------------------------------------------------------------

print()
print("=" * 110)
print("FASE 4 — VERDADE / MENTIRA")
print("=" * 110)

contradicoes = [

    {
        "pergunta": "É verdade que meu time é o Flamengo?",
        "contexto": "Qual é o meu time?",
        "esperados": ["palmeiras"],
        "negacoes": ["não", "nao"],
    },

    {
        "pergunta": "É verdade que eu sou médico?",
        "contexto": "Com o que eu trabalho?",
        "esperados": ["dentista"],
        "negacoes": ["não", "nao"],
    },

    {
        "pergunta": "É verdade que meu principal projeto é o Windows?",
        "contexto": "Qual é meu principal projeto?",
        "esperados": ["jarvis"],
        "negacoes": ["não", "nao"],
    },
]

for caso in contradicoes:

    try:

        contexto = retriever.contexto(
            caso["contexto"]
        )

        resposta = perguntar(
            caso["pergunta"],
            contexto
        )

        texto = resposta.lower()

        fato_correto = any(
            termo in texto
            for termo in caso["esperados"]
        )

        negou = any(
            termo in texto
            for termo in caso["negacoes"]
        )

        ok = (
            fato_correto
            and
            negou
        )

        print()
        print(
            f"{'OK' if ok else 'FALHA'} | "
            f"{caso['pergunta']}"
        )

        print(
            f"  Resposta: {resposta}"
        )

        if not ok:

            falhas.append(
                {
                    "fase": "VERACIDADE",
                    "pergunta": caso["pergunta"],
                    "contexto": contexto,
                    "resposta": resposta,
                }
            )

    except Exception as erro:

        falhas.append(
            {
                "fase": "VERACIDADE",
                "pergunta": caso["pergunta"],
                "erro": traceback.format_exc(),
            }
        )


# ------------------------------------------------------------
# FASE 5 — CONSISTÊNCIA
# ------------------------------------------------------------

print()
print("=" * 110)
print("FASE 5 — CONSISTÊNCIA GLOBAL")
print("=" * 110)

for caso in casos:

    try:

        respostas = []

        for _ in range(3):

            contexto = retriever.contexto(
                caso["pergunta"]
            )

            respostas.append(
                str(
                    perguntar(
                        caso["pergunta"],
                        contexto
                    )
                ).strip().lower()
            )

        respostas_unicas = set(
            respostas
        )

        fato_presente = all(
            all(
                termo.lower()
                in resposta
                for termo in caso["esperado"]
            )
            for resposta in respostas
        )

        print()
        print(
            f"{caso['nome']}: "
            f"{'OK' if fato_presente else 'FALHA'}"
        )

        print(
            f"  Respostas diferentes: "
            f"{len(respostas_unicas)}"
        )

        if not fato_presente:

            falhas.append(
                {
                    "fase": "CONSISTENCIA",
                    "caso": caso["nome"],
                    "respostas": respostas,
                }
            )

    except Exception as erro:

        falhas.append(
            {
                "fase": "CONSISTENCIA",
                "caso": caso["nome"],
                "erro": traceback.format_exc(),
            }
        )


# ------------------------------------------------------------
# ESTATÍSTICAS
# ------------------------------------------------------------

duracao_total = (
    time.perf_counter()
    - inicio_total
)

print()
print("=" * 110)
print("ESTATÍSTICAS")
print("=" * 110)

print()

if tempos_retriever:

    print(
        "RETRIEVER:"
    )

    print(
        f"  média   : {statistics.mean(tempos_retriever):.4f}s"
    )

    print(
        f"  mediana : {statistics.median(tempos_retriever):.4f}s"
    )

    print(
        f"  máximo  : {max(tempos_retriever):.4f}s"
    )

if tempos_qwen:

    print()
    print(
        "QWEN:"
    )

    print(
        f"  média   : {statistics.mean(tempos_qwen):.4f}s"
    )

    print(
        f"  mediana : {statistics.median(tempos_qwen):.4f}s"
    )

    print(
        f"  máximo  : {max(tempos_qwen):.4f}s"
    )

print()
print(
    f"TEMPO TOTAL: {duracao_total:.2f}s"
)

print()
print(
    f"FALHAS TOTAIS: {len(falhas)}"
)


# ------------------------------------------------------------
# DIAGNÓSTICO
# ------------------------------------------------------------

if falhas:

    contador = Counter(
        falha.get(
            "fase",
            "DESCONHECIDA"
        )
        for falha in falhas
    )

    print()
    print("=" * 110)
    print("DIAGNÓSTICO DAS FALHAS")
    print("=" * 110)

    print()

    for fase, quantidade in contador.items():

        print(
            f"{fase}: {quantidade}"
        )

    print()

    for indice, falha in enumerate(
        falhas[:30],
        1
    ):

        print(
            "-" * 110
        )

        print(
            f"FALHA {indice}"
        )

        print(
            json.dumps(
                falha,
                ensure_ascii=False,
                indent=2,
                default=str
            )
        )

    if len(falhas) > 30:

        print()
        print(
            f"... e mais {len(falhas) - 30} falhas."
        )

else:

    print()
    print("=" * 110)
    print("RESULTADO FINAL: OK")
    print("TESTE DE ESTRESSE APROVADO")
    print("=" * 110)


print()
print("=" * 110)
print("FIM DO TESTE")
print("=" * 110)
