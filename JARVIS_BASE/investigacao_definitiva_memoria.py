# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import re
import tempfile
import traceback

from ai.classificador_intencao import obter_classificador
from ai.cerebro import perguntar
from memoria_chroma import MemoriaChroma
from memoria_retriever import MemoriaRetriever


print()
print("=" * 100)
print("J.A.R.V.I.S — INVESTIGAÇÃO FINAL DOS PONTOS REAIS")
print("=" * 100)


# ============================================================
# COMPONENTES
# ============================================================

classificador = obter_classificador()

temp = tempfile.TemporaryDirectory()

banco = MemoriaChroma(
    diretorio=temp.name
)

retriever = MemoriaRetriever(
    memoria=banco
)


# ============================================================
# GARANTIR CHROMA LIMPO
# ============================================================

try:
    banco.colecao.delete(
        where={
            "origem": "memoria_permanente"
        }
    )
except Exception:
    pass


# ============================================================
# MEMÓRIAS FICTÍCIAS
# ============================================================

memorias = [

    {
        "id": "real_nome",
        "conteudo": "O usuário fictício se chama Roberto.",
        "tipo": "NOME",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "real_trabalho",
        "conteudo": "O usuário fictício trabalha como arquiteto.",
        "tipo": "TRABALHO",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "real_familia",
        "conteudo": "A esposa fictícia do usuário se chama Camila Torres.",
        "tipo": "FAMILIA",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "real_projeto",
        "conteudo": "O principal projeto fictício do usuário é o sistema ORION.",
        "tipo": "PROJETO",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "real_esporte",
        "conteudo": "O usuário fictício torce para o Palmeiras.",
        "tipo": "ESPORTE",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "real_local",
        "conteudo": "O usuário fictício mora em Curitiba, Paraná.",
        "tipo": "LOCAL",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "real_carro",
        "conteudo": "O carro fictício do usuário é um Honda Civic azul.",
        "tipo": "OUTRO",
        "duracao": "PERMANENTE",
        "importancia": 6,
    },
]


# ============================================================
# INDEXAR
# ============================================================

ids = []
documents = []
metadatas = []
embeddings = []

for memoria in memorias:

    texto = banco._texto_passage(
        memoria
    )

    try:
        embedding = banco.modelo.encode(
            texto,
            normalize_embeddings=True
        )
    except TypeError:
        embedding = banco.modelo.encode(
            texto
        )

    if hasattr(
        embedding,
        "tolist"
    ):
        embedding = embedding.tolist()

    ids.append(
        memoria["id"]
    )

    documents.append(
        memoria["conteudo"]
    )

    metadatas.append(
        {
            "tipo": memoria["tipo"],
            "duracao": memoria["duracao"],
            "importancia": int(
                memoria["importancia"]
            ),
            "criado_em": "2026-01-01T00:00:00",
            "atualizado_em": "2026-01-01T00:00:00",
            "origem": "diagnostico",
        }
    )

    embeddings.append(
        embedding
    )


banco.colecao.add(
    ids=ids,
    documents=documents,
    metadatas=metadatas,
    embeddings=embeddings,
)


# ============================================================
# FUNÇÃO DE RESULTADO
# ============================================================

def resultado(
    numero,
    nome,
    ok,
    etapa,
    esperado,
    obtido,
    diagnostico="",
):

    print()
    print("=" * 100)
    print(
        f"[{'OK' if ok else 'FALHA'}] "
        f"TESTE {numero:02d} — {nome}"
    )
    print(
        f"ETAPA:    {etapa}"
    )
    print(
        f"ESPERADO: {esperado}"
    )
    print(
        f"OBTIDO:   {obtido}"
    )

    if diagnostico:
        print(
            f"DIAGNÓSTICO: {diagnostico}"
        )


# ============================================================
# TESTE 01 — LOCAL REALMENTE SEM CATEGORIA
# ============================================================

try:

    consulta = "Onde eu moro?"

    original = dict(
        MemoriaRetriever.MAPA_TIPO
    )

    MemoriaRetriever.MAPA_TIPO.pop(
        "LOCAL",
        None
    )

    tipo = MemoriaRetriever.inferir_tipo(
        consulta
    )

    MemoriaRetriever.MAPA_TIPO = original

    resultado(
        1,
        "LOCAL sem categoria",
        tipo is None,
        "INFERÊNCIA",
        "None",
        repr(tipo),
        "Confirma o comportamento original.",
    )

except Exception as erro:

    resultado(
        1,
        "LOCAL sem categoria",
        False,
        "EXCEÇÃO",
        "nenhuma exceção",
        repr(erro),
        traceback.format_exc(),
    )


# ============================================================
# TESTE 02 — LOCAL COM CATEGORIA REAL
# ============================================================

try:

    consulta = "Onde eu moro?"

    original = dict(
        MemoriaRetriever.MAPA_TIPO
    )

    MemoriaRetriever.MAPA_TIPO["LOCAL"] = {

        "pergunta": [
            "onde eu moro",
            "qual cidade eu moro",
            "em que cidade eu moro",
            "qual e minha cidade",
            "qual é minha cidade",
        ],

        "marcadores": [
            "moro",
            "cidade",
            "resido",
            "residencia",
            "residência",
        ],
    }

    tipo = MemoriaRetriever.inferir_tipo(
        consulta
    )

    resultados = retriever.buscar(
        consulta
    )

    contexto = retriever.contexto(
        consulta
    )

    topo = (
        resultados[0]
        if resultados
        else {}
    )

    MemoriaRetriever.MAPA_TIPO = original

    ok = (
        tipo == "LOCAL"
        and topo.get("tipo") == "LOCAL"
        and "curitiba"
        in str(
            topo.get(
                "conteudo",
                ""
            )
        ).lower()
    )

    resultado(
        2,
        "LOCAL com categoria real",
        ok,
        "CLASSIFICAÇÃO + RANKING",
        "LOCAL / Curitiba / Paraná",
        f"TIPO={tipo} | TOPO={json.dumps(topo, ensure_ascii=False)} | CONTEXTO={contexto}",
        ""
        if ok
        else
        "Mesmo com categoria correta, a memória LOCAL não venceu o ranking.",
    )

except Exception as erro:

    resultado(
        2,
        "LOCAL com categoria real",
        False,
        "EXCEÇÃO",
        "execução sem exceção",
        repr(erro),
        traceback.format_exc(),
    )


# ============================================================
# TESTE 03 — ESPORTE ISOLADO
# ============================================================

try:

    consulta = "Qual é o meu time?"

    resultados = retriever.buscar(
        consulta
    )

    topo = (
        resultados[0]
        if resultados
        else {}
    )

    ok = (
        retriever.inferir_tipo(
            consulta
        )
        == "ESPORTE"
        and
        topo.get("tipo")
        == "ESPORTE"
    )

    resultado(
        3,
        "ESPORTE contra memórias genéricas",
        ok,
        "RANKING",
        "ESPORTE / Palmeiras",
        json.dumps(
            topo,
            ensure_ascii=False
        ),
        ""
        if ok
        else
        "ESPORTE ainda não está isolando corretamente a memória.",
    )

except Exception as erro:

    resultado(
        3,
        "ESPORTE contra memórias genéricas",
        False,
        "EXCEÇÃO",
        "execução sem exceção",
        repr(erro),
        traceback.format_exc(),
    )


# ============================================================
# TESTE 04 — QWEN VERDADE
# ============================================================

try:

    consulta = "Qual é o meu time?"

    contexto = retriever.contexto(
        consulta
    )

    resposta = perguntar(
        consulta,
        contexto
    )

    ok = (
        "palmeiras"
        in resposta.lower()
    )

    resultado(
        4,
        "Qwen responde fato verdadeiro",
        ok,
        "QWEN",
        "Palmeiras",
        resposta,
        ""
        if ok
        else
        "Qwen não utilizou o fato fornecido.",
    )

except Exception as erro:

    resultado(
        4,
        "Qwen responde fato verdadeiro",
        False,
        "EXCEÇÃO",
        "execução sem exceção",
        repr(erro),
        traceback.format_exc(),
    )


# ============================================================
# TESTE 05 — QWEN CONTRADIÇÃO
# ============================================================

try:

    consulta = (
        "É verdade que meu time é o Flamengo?"
    )

    contexto = retriever.contexto(
        "Qual é o meu time?"
    )

    resposta = perguntar(
        consulta,
        contexto
    )

    texto = resposta.lower()

    correto = (
        "palmeiras"
        in texto
    )

    negacao = any(
        expressao in texto
        for expressao in [
            "não",
            "nao",
            "incorreto",
            "incorreta",
        ]
    )

    ok = (
        correto
        and negacao
    )

    resultado(
        5,
        "Qwen identifica afirmação falsa",
        ok,
        "QWEN + VERACIDADE",
        "Negar Flamengo e afirmar Palmeiras",
        resposta,
        ""
        if ok
        else
        "A resposta não apresentou uma negação explícita da afirmação falsa.",
    )

except Exception as erro:

    resultado(
        5,
        "Qwen identifica afirmação falsa",
        False,
        "EXCEÇÃO",
        "execução sem exceção",
        repr(erro),
        traceback.format_exc(),
    )


# ============================================================
# TESTE 06 — QWEN PROFISSÃO FALSA
# ============================================================

try:

    consulta = (
        "É verdade que eu sou médico?"
    )

    contexto = retriever.contexto(
        "Com o que eu trabalho?"
    )

    resposta = perguntar(
        consulta,
        contexto
    )

    texto = resposta.lower()

    ok = (
        "arquiteto"
        in texto
        and
        any(
            expressao in texto
            for expressao in [
                "não",
                "nao",
            ]
        )
    )

    resultado(
        6,
        "Qwen identifica profissão falsa",
        ok,
        "QWEN + VERACIDADE",
        "Não médico / arquiteto",
        resposta,
        ""
        if ok
        else
        "Qwen não contradisse explicitamente o fato falso.",
    )

except Exception as erro:

    resultado(
        6,
        "Qwen identifica profissão falsa",
        False,
        "EXCEÇÃO",
        "execução sem exceção",
        repr(erro),
        traceback.format_exc(),
    )


# ============================================================
# TESTE 07 — TRIAGEM ACEITA
# ============================================================

try:

    consulta = "Qual é o meu time?"

    triagem = classificador.classificar(
        consulta
    )

    ok = (
        triagem.get("intencao")
        == "conversa_geral"
        and
        triagem.get("aceita") is True
    )

    resultado(
        7,
        "Triagem aceita pergunta pessoal",
        ok,
        "TRIAGEM",
        "conversa_geral + aceita=True",
        json.dumps(
            triagem,
            ensure_ascii=False
        ),
        ""
        if ok
        else
        "A triagem classificou como conversa_geral, mas marcou aceita=False.",
    )

except Exception as erro:

    resultado(
        7,
        "Triagem aceita pergunta pessoal",
        False,
        "EXCEÇÃO",
        "execução sem exceção",
        repr(erro),
        traceback.format_exc(),
    )


# ============================================================
# TESTE 08 — PIPELINE LOCAL
# ============================================================

try:

    original = dict(
        MemoriaRetriever.MAPA_TIPO
    )

    MemoriaRetriever.MAPA_TIPO["LOCAL"] = {

        "pergunta": [
            "onde eu moro",
            "qual cidade eu moro",
            "qual e minha cidade",
            "qual é minha cidade",
        ],

        "marcadores": [
            "moro",
            "cidade",
            "resido",
        ],
    }

    consulta = "Onde eu moro?"

    triagem = classificador.classificar(
        consulta
    )

    tipo = MemoriaRetriever.inferir_tipo(
        consulta
    )

    contexto = retriever.contexto(
        consulta
    )

    resposta = perguntar(
        consulta,
        contexto
    )

    MemoriaRetriever.MAPA_TIPO = original

    ok = (
        triagem.get("intencao")
        == "conversa_geral"
        and
        tipo == "LOCAL"
        and
        "curitiba"
        in contexto.lower()
        and
        "paraná"
        in resposta.lower()
    )

    resultado(
        8,
        "Pipeline completo LOCAL",
        ok,
        "TRIAGEM → TIPO → RETRIEVER → QWEN",
        "conversa_geral → LOCAL → Curitiba/Paraná → resposta correta",
        f"TRIAGEM={triagem} | TIPO={tipo} | CONTEXTO={contexto} | RESPOSTA={resposta}",
        ""
        if ok
        else
        "Alguma etapa do pipeline LOCAL falhou.",
    )

except Exception as erro:

    resultado(
        8,
        "Pipeline completo LOCAL",
        False,
        "EXCEÇÃO",
        "execução sem exceção",
        repr(erro),
        traceback.format_exc(),
    )


# ============================================================
# RESUMO
# ============================================================

print()
print("=" * 100)
print("CONCLUSÃO DA INVESTIGAÇÃO")
print("=" * 100)
print()
print("Os testes 01 e 02 determinam se LOCAL é realmente a causa.")
print("Os testes 03-06 determinam se ranking/Qwen possuem problema real.")
print("O teste 07 determina se existe inconsistência no contrato da triagem.")
print("O teste 08 valida o pipeline completo.")
print()

temp.cleanup()
