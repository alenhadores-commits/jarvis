# -*- coding: utf-8 -*-

"""
INVESTIGAÇÃO DIRECIONADA — FALHAS 12, 14, 17, 18, 19

Objetivo:
separar definitivamente:
1. erro real de produção
2. erro do teste anterior
3. erro de recuperação
4. erro de prompt/Qwen
5. erro de verificação de veracidade
"""

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
print("J.A.R.V.I.S — INVESTIGAÇÃO DIRECIONADA DAS FALHAS")
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
# LIMPA CONTAMINAÇÃO DA SINCRONIZAÇÃO AUTOMÁTICA
# ============================================================

print()
print("=" * 100)
print("LIMPANDO CHROMA TEMPORÁRIO")
print("=" * 100)

try:

    banco.colecao.delete(
        where={
            "origem": "memoria_permanente"
        }
    )

    print(
        "Memórias reais removidas do Chroma temporário."
    )

except Exception as erro:

    print(
        "Falha ao remover memórias reais:",
        erro
    )


# ============================================================
# MEMÓRIAS CONTROLADAS
# ============================================================

memorias = [

    {
        "id": "diag_nome",
        "conteudo": "O usuário fictício se chama Roberto.",
        "tipo": "NOME",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "diag_trabalho",
        "conteudo": "O usuário fictício trabalha como arquiteto.",
        "tipo": "TRABALHO",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "diag_esposa",
        "conteudo": "A esposa fictícia do usuário se chama Camila Torres.",
        "tipo": "FAMILIA",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "diag_projeto",
        "conteudo": "O principal projeto fictício do usuário é o sistema ORION.",
        "tipo": "PROJETO",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "diag_esporte",
        "conteudo": "O usuário fictício torce para o Palmeiras.",
        "tipo": "ESPORTE",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "diag_local",
        "conteudo": "O usuário fictício mora em Curitiba, Paraná.",
        "tipo": "LOCAL",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "diag_outro",
        "conteudo": "O usuário fictício gosta de tecnologia.",
        "tipo": "OUTRO",
        "duracao": "PERMANENTE",
        "importancia": 5,
    },
]


# ============================================================
# INCLUSÃO CONTROLADA
# ============================================================

print()
print("=" * 100)
print("INSERINDO SOMENTE MEMÓRIAS FICTÍCIAS")
print("=" * 100)

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
            "origem": "diagnostico_e2e",
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

print(
    f"Memórias fictícias inseridas: {len(ids)}"
)


# ============================================================
# GARANTIA DE ISOLAMENTO
# ============================================================

print()
print("=" * 100)
print("TESTE DE ISOLAMENTO DO CHROMA")
print("=" * 100)

todos = banco.buscar(
    "usuário",
    limite=50
)

reais = [
    item
    for item in todos
    if item.get("origem")
    == "memoria_permanente"
]

print(
    "Documentos encontrados:",
    len(todos)
)

print(
    "Documentos reais encontrados:",
    len(reais)
)

if reais:

    print(
        "ERRO: CHROMA TEMPORÁRIO AINDA ESTÁ CONTAMINADO."
    )

else:

    print(
        "OK: ambiente de teste está isolado."
    )


# ============================================================
# CATEGORIA LOCAL APENAS PARA INVESTIGAÇÃO
# ============================================================

def testar_com_local_category():

    original = dict(
        retriever.MAPA_TIPO
    )

    retriever.MAPA_TIPO["LOCAL"] = {

        "pergunta": [
            "onde eu moro",
            "qual cidade eu moro",
            "em que cidade eu moro",
            "onde eu moro atualmente",
            "qual e minha cidade",
            "qual é minha cidade",
        ],

        "marcadores": [
            "cidade",
            "moro",
            "moradia",
            "resido",
            "residencia",
            "residência",
        ],
    }

    return original


# ============================================================
# TESTE 01 — LOCAL SEM CATEGORIA
# ============================================================

def teste_01_local_original():

    consulta = "Onde eu moro?"

    # Remove temporariamente a categoria LOCAL.
    original = retriever.MAPA_TIPO.copy()

    retriever.MAPA_TIPO.pop(
        "LOCAL",
        None
    )

    tipo = retriever.inferir_tipo(
        consulta
    )

    retriever.MAPA_TIPO = original

    esperado = "None"

    ok = tipo is None

    print()
    print("=" * 100)
    print("TESTE 01 — CAUSA ORIGINAL DA LOCALIZAÇÃO")
    print("=" * 100)
    print("Pergunta :", consulta)
    print("Esperado :", esperado)
    print("Obtido   :", tipo)
    print(
        "RESULTADO:",
        "OK — confirmou causa" if ok
        else "FALHA — hipótese não confirmada"
    )

    if not ok:
        print(
            "Diagnóstico: alguma outra categoria está capturando a pergunta."
        )


# ============================================================
# TESTE 02 — LOCAL COM CATEGORIA
# ============================================================

def teste_02_local_com_categoria():

    original = testar_com_local_category()

    consulta = "Onde eu moro?"

    tipo = retriever.inferir_tipo(
        consulta
    )

    resultados = retriever.buscar(
        consulta
    )

    contexto = retriever.contexto(
        consulta
    )

    retriever.MAPA_TIPO = original

    topo = (
        resultados[0]
        if resultados
        else {}
    )

    ok = (
        tipo == "LOCAL"
        and
        topo.get("tipo") == "LOCAL"
        and
        "curitiba"
        in str(
            topo.get(
                "conteudo",
                ""
            )
        ).lower()
    )

    print()
    print("=" * 100)
    print("TESTE 02 — LOCAL COM CATEGORIA")
    print("=" * 100)
    print("Tipo     :", tipo)
    print("Topo     :", json.dumps(
        topo,
        ensure_ascii=False
    ))
    print("Contexto :", contexto)
    print(
        "RESULTADO:",
        "OK — categoria resolve o problema"
        if ok
        else
        "FALHA — categoria sozinha não resolveu"
    )


# ============================================================
# TESTE 03 — ISOLAMENTO FAMÍLIA
# ============================================================

def teste_03_familia():

    consulta = "Quem é minha esposa?"

    resultados = retriever.buscar(
        consulta
    )

    topo = (
        resultados[0]
        if resultados
        else {}
    )

    contexto = retriever.contexto(
        consulta
    )

    ok = (
        topo.get("tipo")
        == "FAMILIA"
        and
        "camila torres"
        in str(
            topo.get(
                "conteudo",
                ""
            )
        ).lower()
    )

    print()
    print("=" * 100)
    print("TESTE 03 — FAMÍLIA SEM CONTAMINAÇÃO")
    print("=" * 100)
    print("Topo     :", json.dumps(
        topo,
        ensure_ascii=False
    ))
    print("Contexto :", contexto)
    print(
        "RESULTADO:",
        "OK"
        if ok
        else
        "FALHA"
    )

    if "mariana" in contexto.lower():
        print(
            "ERRO CRÍTICO: memória real contaminou o teste."
        )


# ============================================================
# TESTE 04 — PROJETO SEM CONTAMINAÇÃO
# ============================================================

def teste_04_projeto():

    consulta = "Qual é meu principal projeto?"

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

    ok = (
        "orion"
        in contexto.lower()
        and
        "jarvis"
        not in contexto.lower()
        and
        topo.get("tipo")
        == "PROJETO"
    )

    print()
    print("=" * 100)
    print("TESTE 04 — PROJETO SEM CONTAMINAÇÃO")
    print("=" * 100)
    print("Topo     :", json.dumps(
        topo,
        ensure_ascii=False
    ))
    print("Contexto :", contexto)
    print(
        "RESULTADO:",
        "OK"
        if ok
        else
        "FALHA"
    )


# ============================================================
# TESTE 05 — ESPORTE
# ============================================================

def teste_05_esporte():

    consulta = "Qual é o meu time?"

    tipo = retriever.inferir_tipo(
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

    ok = (
        tipo == "ESPORTE"
        and
        topo.get("tipo")
        == "ESPORTE"
        and
        "palmeiras"
        in contexto.lower()
    )

    print()
    print("=" * 100)
    print("TESTE 05 — ESPORTE")
    print("=" * 100)
    print("Tipo     :", tipo)
    print("Topo     :", json.dumps(
        topo,
        ensure_ascii=False
    ))
    print("Contexto :", contexto)
    print(
        "RESULTADO:",
        "OK"
        if ok
        else
        "FALHA"
    )


# ============================================================
# HELPERS DE VERACIDADE
# ============================================================

def verificar_afirmacao_verdadeira(
    resposta: str,
    fato_correto: str,
) -> bool:

    texto = resposta.lower()

    return fato_correto.lower() in texto


def verificar_contradicao(
    resposta: str,
    fato_falso: str,
) -> bool:

    texto = resposta.lower()

    falso = fato_falso.lower()

    padroes_negacao = [

        rf"não[^.?!]{{0,80}}{re.escape(falso)}",
        rf"nao[^.?!]{{0,80}}{re.escape(falso)}",

        rf"{re.escape(falso)}[^.?!]{{0,50}}não",
        rf"{re.escape(falso)}[^.?!]{{0,50}}nao",

        rf"não é[^.?!]{{0,50}}{re.escape(falso)}",
        rf"nao e[^.?!]{{0,50}}{re.escape(falso)}",

    ]

    return any(
        re.search(
            padrao,
            texto
        )
        for padrao in padroes_negacao
    )


# ============================================================
# TESTE 06 — QWEN ESPOSA
# ============================================================

def teste_06_qwen_esposa():

    consulta = "Qual é o nome da minha esposa?"

    contexto = retriever.contexto(
        consulta
    )

    resposta = perguntar(
        consulta,
        contexto
    )

    ok = (
        verificar_afirmacao_verdadeira(
            resposta,
            "Camila Torres"
        )
        and
        "Mariana Praxedes".lower()
        not in resposta.lower()
    )

    print()
    print("=" * 100)
    print("TESTE 06 — QWEN + FAMÍLIA")
    print("=" * 100)
    print("Contexto :", contexto)
    print("Resposta :", resposta)
    print(
        "RESULTADO:",
        "OK"
        if ok
        else
        "FALHA"
    )


# ============================================================
# TESTE 07 — QWEN PROJETO
# ============================================================

def teste_07_qwen_projeto():

    consulta = "Qual é meu principal projeto?"

    contexto = retriever.contexto(
        consulta
    )

    resposta = perguntar(
        consulta,
        contexto
    )

    ok = (
        "orion"
        in resposta.lower()
        and
        "jarvis"
        not in resposta.lower()
    )

    print()
    print("=" * 100)
    print("TESTE 07 — QWEN + PROJETO")
    print("=" * 100)
    print("Contexto :", contexto)
    print("Resposta :", resposta)
    print(
        "RESULTADO:",
        "OK"
        if ok
        else
        "FALHA"
    )


# ============================================================
# TESTE 08 — QWEN ESPORTE
# ============================================================

def teste_08_qwen_esporte():

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
        and
        "roberto"
        not in resposta.lower()
    )

    print()
    print("=" * 100)
    print("TESTE 08 — QWEN + ESPORTE")
    print("=" * 100)
    print("Contexto :", contexto)
    print("Resposta :", resposta)
    print(
        "RESULTADO:",
        "OK"
        if ok
        else
        "FALHA"
    )


# ============================================================
# TESTE 09 — AFIRMAÇÃO FALSA TIME
# ============================================================

def teste_09_falso_time():

    consulta = "É verdade que meu time é o Flamengo?"

    contexto = retriever.contexto(
        "Qual é o meu time?"
    )

    resposta = perguntar(
        consulta,
        contexto
    )

    correto = "palmeiras" in resposta.lower()

    negou_falso = verificar_contradicao(
        resposta,
        "Flamengo"
    )

    ok = (
        correto
        and
        negou_falso
    )

    print()
    print("=" * 100)
    print("TESTE 09 — QWEN + CONTRADIÇÃO ESPORTIVA")
    print("=" * 100)
    print("Contexto :", contexto)
    print("Resposta :", resposta)
    print("Correto  :", correto)
    print("Negou falso:", negou_falso)
    print(
        "RESULTADO:",
        "OK"
        if ok
        else
        "FALHA"
    )


# ============================================================
# TESTE 10 — AFIRMAÇÃO FALSA PROFISSÃO
# ============================================================

def teste_10_falso_trabalho():

    consulta = "É verdade que eu sou médico?"

    contexto = retriever.contexto(
        "Com o que eu trabalho?"
    )

    resposta = perguntar(
        consulta,
        contexto
    )

    correto = "arquiteto" in resposta.lower()

    negou_falso = verificar_contradicao(
        resposta,
        "médico"
    )

    if not negou_falso:

        negou_falso = verificar_contradicao(
            resposta,
            "medico"
        )

    ok = (
        correto
        and
        negou_falso
    )

    print()
    print("=" * 100)
    print("TESTE 10 — QWEN + CONTRADIÇÃO PROFISSIONAL")
    print("=" * 100)
    print("Contexto :", contexto)
    print("Resposta :", resposta)
    print("Correto  :", correto)
    print("Negou falso:", negou_falso)
    print(
        "RESULTADO:",
        "OK"
        if ok
        else
        "FALHA"
    )


# ============================================================
# TESTE 11 — VERDADE LOCAL COM CATEGORIA
# ============================================================

def teste_11_qwen_local():

    original = testar_com_local_category()

    consulta = "Onde eu moro?"

    contexto = retriever.contexto(
        consulta
    )

    resposta = perguntar(
        consulta,
        contexto
    )

    retriever.MAPA_TIPO = original

    ok = (
        "curitiba"
        in resposta.lower()
        and
        "paraná"
        in resposta.lower()
    )

    print()
    print("=" * 100)
    print("TESTE 11 — QWEN + LOCALIZAÇÃO")
    print("=" * 100)
    print("Contexto :", contexto)
    print("Resposta :", resposta)
    print(
        "RESULTADO:",
        "OK"
        if ok
        else
        "FALHA"
    )


# ============================================================
# TESTE 12 — PIPELINE COMPLETO
# ============================================================

def teste_12_pipeline():

    consulta = "Qual é o meu time?"

    triagem = classificador.classificar(
        consulta
    )

    tipo = retriever.inferir_tipo(
        consulta
    )

    contexto = retriever.contexto(
        consulta
    )

    resposta = perguntar(
        consulta,
        contexto
    )

    ok = (
        triagem.get("intencao")
        == "conversa_geral"
        and
        tipo == "ESPORTE"
        and
        "palmeiras"
        in contexto.lower()
        and
        "palmeiras"
        in resposta.lower()
    )

    print()
    print("=" * 100)
    print("TESTE 12 — PIPELINE COMPLETO")
    print("=" * 100)
    print("Triagem  :", triagem)
    print("Tipo     :", tipo)
    print("Contexto :", contexto)
    print("Resposta :", resposta)
    print(
        "RESULTADO:",
        "OK"
        if ok
        else
        "FALHA"
    )


# ============================================================
# EXECUÇÃO
# ============================================================

testes = [

    (1, teste_01_local_original),
    (2, teste_02_local_com_categoria),
    (3, teste_03_familia),
    (4, teste_04_projeto),
    (5, teste_05_esporte),
    (6, teste_06_qwen_esposa),
    (7, teste_07_qwen_projeto),
    (8, teste_08_qwen_esporte),
    (9, teste_09_falso_time),
    (10, teste_10_falso_trabalho),
    (11, teste_11_qwen_local),
    (12, teste_12_pipeline),
]


for numero, funcao in testes:

    try:
        funcao()

    except Exception as erro:

        print()
        print("=" * 100)
        print(
            f"[EXCEÇÃO] TESTE {numero:02d}"
        )
        print("=" * 100)
        print(
            traceback.format_exc()
        )


# ============================================================
# FINAL
# ============================================================

print()
print("=" * 100)
print("INVESTIGAÇÃO CONCLUÍDA")
print("=" * 100)

temp.cleanup()
