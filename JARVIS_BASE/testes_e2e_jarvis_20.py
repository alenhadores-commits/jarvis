# -*- coding: utf-8 -*-

"""
J.A.R.V.I.S — SUITE E2E v20

20 testes reais:

1-4   = TRIAGEM
5-14  = MEMÓRIA + E5 + RANKING
15-19 = QWEN + VERACIDADE
20    = PIPELINE COMPLETO

As memórias usadas pelos testes são fictícias e ficam
somente em uma coleção Chroma temporária.
Nada é gravado na memória permanente do JARVIS.
"""

from __future__ import annotations

import json
import re
import tempfile
import traceback
from dataclasses import dataclass
from typing import Any

from ai.classificador_intencao import obter_classificador
from ai.cerebro import perguntar
from memoria_chroma import MemoriaChroma
from memoria_retriever import MemoriaRetriever


# ============================================================
# RESULTADO
# ============================================================

@dataclass
class Resultado:
    numero: int
    nome: str
    passou: bool
    etapa: str
    esperado: str
    obtido: str
    erro: str


resultados: list[Resultado] = []


def limpar_texto(valor: Any) -> str:
    return " ".join(
        str(valor or "").strip().split()
    )


def mostrar(
    numero: int,
    nome: str,
    passou: bool,
    etapa: str,
    esperado: str,
    obtido: str,
    erro: str = "",
) -> None:

    resultados.append(
        Resultado(
            numero=numero,
            nome=nome,
            passou=passou,
            etapa=etapa,
            esperado=esperado,
            obtido=obtido,
            erro=erro,
        )
    )

    status = "OK" if passou else "FALHA"

    print()
    print("=" * 90)
    print(f"[{status}] TESTE {numero:02d} - {nome}")
    print(f"ETAPA:    {etapa}")
    print(f"ESPERADO: {esperado}")
    print(f"OBTIDO:   {obtido}")

    if erro:
        print(f"ERRO:     {erro}")


def executar(
    numero: int,
    nome: str,
    funcao,
) -> None:

    try:
        funcao()

    except Exception as erro:

        mostrar(
            numero,
            nome,
            False,
            "EXCEÇÃO",
            "execução sem exceção",
            f"{type(erro).__name__}: {erro}",
            traceback.format_exc(),
        )


# ============================================================
# INICIALIZAÇÃO
# ============================================================

print()
print("=" * 90)
print("J.A.R.V.I.S — SUITE END-TO-END 20 TESTES")
print("=" * 90)
print()
print("Inicializando componentes reais...")

try:

    classificador = obter_classificador()

    temp_dir = tempfile.TemporaryDirectory()

    banco = MemoriaChroma(
        diretorio=temp_dir.name
    )

    retriever = MemoriaRetriever(
        memoria=banco
    )

    print("Triagem: OK")
    print("Chroma temporário: OK")
    print("E5: OK")
    print("Retriever: OK")

except Exception as erro:

    print()
    print("=" * 90)
    print("FALHA CRÍTICA DE INICIALIZAÇÃO")
    print("=" * 90)
    print(
        traceback.format_exc()
    )

    raise SystemExit(1)


# ============================================================
# MEMÓRIAS FICTÍCIAS
# ============================================================

memorias = [

    {
        "id": "fake_nome_001",
        "conteudo": "O nome fictício do usuário é Roberto.",
        "tipo": "NOME",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "fake_trabalho_001",
        "conteudo": "O usuário fictício trabalha como arquiteto.",
        "tipo": "TRABALHO",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "fake_familia_001",
        "conteudo": "A esposa fictícia do usuário se chama Camila Torres.",
        "tipo": "FAMILIA",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "fake_familia_002",
        "conteudo": "O filho fictício do usuário se chama Lucas.",
        "tipo": "FAMILIA",
        "duracao": "PERMANENTE",
        "importancia": 7,
    },

    {
        "id": "fake_comida_001",
        "conteudo": "A comida favorita do usuário fictício é lasanha.",
        "tipo": "COMIDA",
        "duracao": "PERMANENTE",
        "importancia": 7,
    },

    {
        "id": "fake_animal_001",
        "conteudo": "O animal favorito do usuário fictício é gato.",
        "tipo": "ANIMAL",
        "duracao": "PERMANENTE",
        "importancia": 7,
    },

    {
        "id": "fake_projeto_001",
        "conteudo": "O principal projeto fictício do usuário é o sistema ORION.",
        "tipo": "PROJETO",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "fake_esporte_001",
        "conteudo": "O usuário fictício torce para o Palmeiras.",
        "tipo": "ESPORTE",
        "duracao": "PERMANENTE",
        "importancia": 8,
    },

    {
        "id": "fake_esporte_002",
        "conteudo": "O jogador favorito fictício do usuário é Neymar.",
        "tipo": "ESPORTE",
        "duracao": "PERMANENTE",
        "importancia": 6,
    },

    {
        "id": "fake_local_001",
        "conteudo": "O usuário fictício mora em Curitiba, Paraná.",
        "tipo": "OUTRO",
        "duracao": "PERMANENTE",
        "importancia": 7,
    },

    {
        "id": "fake_carro_001",
        "conteudo": "O carro fictício do usuário é um Honda Civic azul.",
        "tipo": "OUTRO",
        "duracao": "PERMANENTE",
        "importancia": 6,
    },

    {
        "id": "fake_cor_001",
        "conteudo": "A cor favorita fictícia do usuário é verde.",
        "tipo": "PREFERENCIA",
        "duracao": "PERMANENTE",
        "importancia": 6,
    },
]


# ============================================================
# INDEXAÇÃO NO CHROMA TEMPORÁRIO
# ============================================================

print()
print("=" * 90)
print("INDEXANDO MEMÓRIAS FICTÍCIAS")
print("=" * 90)

try:

    ids = []
    documents = []
    metadatas = []
    embeddings = []

    for memoria in memorias:

        texto_passage = banco._texto_passage(
            memoria
        )

        try:

            embedding = banco.modelo.encode(
                texto_passage,
                normalize_embeddings=True
            )

        except TypeError:

            embedding = banco.modelo.encode(
                texto_passage
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
                "origem": "teste_e2e",
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
        f"Memórias fictícias indexadas: {len(ids)}"
    )

except Exception as erro:

    print(
        traceback.format_exc()
    )

    temp_dir.cleanup()

    raise SystemExit(1)


# ============================================================
# HELPERS
# ============================================================

def contexto_da(
    consulta: str,
) -> str:

    return retriever.contexto(
        consulta
    )


def buscar_da(
    consulta: str,
) -> list[dict[str, Any]]:

    return retriever.buscar(
        consulta
    )


def resposta_qwen(
    consulta: str,
    contexto: str,
) -> str:

    return limpar_texto(
        perguntar(
            consulta,
            contexto
        )
    )


def contem_todos(
    texto: str,
    termos: list[str],
) -> bool:

    texto_n = limpar_texto(
        texto
    ).lower()

    return all(
        termo.lower() in texto_n
        for termo in termos
    )


def contem_algum(
    texto: str,
    termos: list[str],
) -> bool:

    texto_n = limpar_texto(
        texto
    ).lower()

    return any(
        termo.lower() in texto_n
        for termo in termos
    )


def resposta_negativa(
    texto: str,
) -> bool:

    texto_n = limpar_texto(
        texto
    ).lower()

    negativos = [
        "não",
        "nao",
        "nunca",
        "incorreto",
        "incorreta",
        "não é",
        "nao e",
        "não,",
        "nao,",
    ]

    return any(
        marcador in texto_n
        for marcador in negativos
    )


# ============================================================
# 01 — TRIAGEM: CONVERSA
# ============================================================

def teste_01():

    entrada = "Olá JARVIS, tudo bem?"

    r = classificador.classificar(
        entrada
    )

    ok = (
        r.get("intencao")
        == "conversa_geral"
    )

    mostrar(
        1,
        "Triagem - conversa geral",
        ok,
        "TRIAGEM",
        "conversa_geral",
        json.dumps(
            r,
            ensure_ascii=False
        ),
        ""
        if ok
        else "A triagem roteou uma conversa simples para outra intenção.",
    )


executar(
    1,
    "Triagem - conversa geral",
    teste_01
)


# ============================================================
# 02 — TRIAGEM: PESQUISA
# ============================================================

def teste_02():

    entrada = "Pesquise na internet a cotação do dólar."

    r = classificador.classificar(
        entrada
    )

    ok = (
        r.get("intencao")
        == "pesquisa_geral"
    )

    mostrar(
        2,
        "Triagem - pesquisa geral",
        ok,
        "TRIAGEM",
        "pesquisa_geral",
        json.dumps(
            r,
            ensure_ascii=False
        ),
        ""
        if ok
        else "A regra de pesquisa não foi acionada.",
    )


executar(
    2,
    "Triagem - pesquisa geral",
    teste_02
)


# ============================================================
# 03 — TRIAGEM: MEMÓRIA
# ============================================================

def teste_03():

    entrada = "Meu nome é Roberto."

    r = classificador.classificar(
        entrada
    )

    ok = (
        r.get("intencao")
        == "memoria"
    )

    mostrar(
        3,
        "Triagem - pedido de memória",
        ok,
        "TRIAGEM",
        "memoria",
        json.dumps(
            r,
            ensure_ascii=False
        ),
        ""
        if ok
        else "A identificação pessoal não foi roteada para memória.",
    )


executar(
    3,
    "Triagem - pedido de memória",
    teste_03
)


# ============================================================
# 04 — TRIAGEM: ATUALIDADE
# ============================================================

def teste_04():

    entrada = "Quem venceu o jogo ontem?"

    r = classificador.classificar(
        entrada
    )

    ok = (
        r.get("intencao")
        == "pesquisa_atualidade"
    )

    mostrar(
        4,
        "Triagem - informação atual",
        ok,
        "TRIAGEM",
        "pesquisa_atualidade",
        json.dumps(
            r,
            ensure_ascii=False
        ),
        ""
        if ok
        else "Uma pergunta temporal foi roteada incorretamente.",
    )


executar(
    4,
    "Triagem - informação atual",
    teste_04
)


# ============================================================
# 05 — MEMÓRIA: NOME
# ============================================================

def teste_05():

    consulta = "Qual é meu nome?"
    contexto = contexto_da(
        consulta
    )

    ok = contem_todos(
        contexto,
        ["Roberto"]
    )

    mostrar(
        5,
        "Memória - nome",
        ok,
        "MEMÓRIA",
        "Roberto",
        contexto,
        ""
        if ok
        else "Memória NOME não foi recuperada.",
    )


executar(
    5,
    "Memória - nome",
    teste_05
)


# ============================================================
# 06 — MEMÓRIA: ESPOSA
# ============================================================

def teste_06():

    consulta = "Qual é o nome da minha esposa?"
    contexto = contexto_da(
        consulta
    )

    ok = contem_todos(
        contexto,
        ["Camila Torres"]
    )

    mostrar(
        6,
        "Memória - esposa",
        ok,
        "MEMÓRIA",
        "Camila Torres",
        contexto,
        ""
        if ok
        else "Memória FAMILIA incorreta ou ausente.",
    )


executar(
    6,
    "Memória - esposa",
    teste_06
)


# ============================================================
# 07 — MEMÓRIA: TRABALHO
# ============================================================

def teste_07():

    consulta = "Com o que eu trabalho?"
    contexto = contexto_da(
        consulta
    )

    ok = contem_todos(
        contexto,
        ["arquiteto"]
    )

    mostrar(
        7,
        "Memória - trabalho",
        ok,
        "MEMÓRIA",
        "arquiteto",
        contexto,
        ""
        if ok
        else "Memória TRABALHO não foi recuperada.",
    )


executar(
    7,
    "Memória - trabalho",
    teste_07
)


# ============================================================
# 08 — MEMÓRIA: ESPORTE
# ============================================================

def teste_08():

    consulta = "Qual é o meu time?"
    tipo = retriever.inferir_tipo(
        consulta
    )

    contexto = contexto_da(
        consulta
    )

    ok = (
        str(tipo).upper()
        == "ESPORTE"
        and
        "palmeiras" in contexto.lower()
    )

    mostrar(
        8,
        "Memória - time",
        ok,
        "MEMÓRIA + TIPO",
        "tipo ESPORTE + Palmeiras",
        f"TIPO={tipo} | CONTEXTO={contexto}",
        ""
        if ok
        else "O tipo ESPORTE ou a memória Palmeiras não foi selecionado.",
    )


executar(
    8,
    "Memória - time",
    teste_08
)


# ============================================================
# 09 — MEMÓRIA: COMIDA
# ============================================================

def teste_09():

    consulta = "Qual é minha comida favorita?"
    contexto = contexto_da(
        consulta
    )

    ok = "lasanha" in contexto.lower()

    mostrar(
        9,
        "Memória - comida",
        ok,
        "MEMÓRIA",
        "lasanha",
        contexto,
        ""
        if ok
        else "Memória COMIDA não foi recuperada.",
    )


executar(
    9,
    "Memória - comida",
    teste_09
)


# ============================================================
# 10 — MEMÓRIA: ANIMAL
# ============================================================

def teste_10():

    consulta = "Qual é meu animal favorito?"
    contexto = contexto_da(
        consulta
    )

    ok = "gato" in contexto.lower()

    mostrar(
        10,
        "Memória - animal",
        ok,
        "MEMÓRIA",
        "gato",
        contexto,
        ""
        if ok
        else "Memória ANIMAL não foi recuperada.",
    )


executar(
    10,
    "Memória - animal",
    teste_10
)


# ============================================================
# 11 — MEMÓRIA: PROJETO
# ============================================================

def teste_11():

    consulta = "Qual é meu principal projeto?"
    contexto = contexto_da(
        consulta
    )

    ok = "orion" in contexto.lower()

    mostrar(
        11,
        "Memória - projeto",
        ok,
        "MEMÓRIA",
        "ORION",
        contexto,
        ""
        if ok
        else "Memória PROJETO não foi recuperada.",
    )


executar(
    11,
    "Memória - projeto",
    teste_11
)


# ============================================================
# 12 — MEMÓRIA: LOCALIZAÇÃO
# ============================================================

def teste_12():

    consulta = "Onde eu moro?"
    contexto = contexto_da(
        consulta
    )

    ok = (
        "curitiba" in contexto.lower()
        and
        "paraná" in contexto.lower()
    )

    mostrar(
        12,
        "Memória - localização",
        ok,
        "MEMÓRIA",
        "Curitiba / Paraná",
        contexto,
        ""
        if ok
        else "Memória de localização não foi recuperada.",
    )


executar(
    12,
    "Memória - localização",
    teste_12
)


# ============================================================
# 13 — ISOLAMENTO ESPORTE x NOME
# ============================================================

def teste_13():

    consulta = "Qual é o meu time?"

    resultados_busca = buscar_da(
        consulta
    )

    topo = (
        resultados_busca[0]
        if resultados_busca
        else {}
    )

    ok = (
        topo.get("tipo") == "ESPORTE"
        and
        "palmeiras"
        in str(
            topo.get(
                "conteudo",
                ""
            )
        ).lower()
    )

    mostrar(
        13,
        "Isolamento - esporte contra memória de nome",
        ok,
        "RANKING",
        "primeiro resultado = ESPORTE / Palmeiras",
        json.dumps(
            topo,
            ensure_ascii=False,
        ),
        ""
        if ok
        else "O ranking ainda está permitindo que NOME supere ESPORTE.",
    )


executar(
    13,
    "Isolamento - esporte contra memória de nome",
    teste_13
)


# ============================================================
# 14 — ISOLAMENTO FAMÍLIA x ESPORTE
# ============================================================

def teste_14():

    consulta = "Quem é minha esposa?"

    resultados_busca = buscar_da(
        consulta
    )

    topo = (
        resultados_busca[0]
        if resultados_busca
        else {}
    )

    ok = (
        topo.get("tipo") == "FAMILIA"
        and
        "camila torres"
        in str(
            topo.get(
                "conteudo",
                ""
            )
        ).lower()
    )

    mostrar(
        14,
        "Isolamento - família contra esporte",
        ok,
        "RANKING",
        "primeiro resultado = FAMILIA / Camila Torres",
        json.dumps(
            topo,
            ensure_ascii=False,
        ),
        ""
        if ok
        else "O ranking selecionou uma memória de outra categoria.",
    )


executar(
    14,
    "Isolamento - família contra esporte",
    teste_14
)


# ============================================================
# 15 — QWEN: VERDADE ESPOSA
# ============================================================

def teste_15():

    consulta = "Qual é o nome da minha esposa?"
    contexto = contexto_da(
        consulta
    )

    resposta = resposta_qwen(
        consulta,
        contexto
    )

    ok = contem_todos(
        resposta,
        ["Camila Torres"]
    )

    mostrar(
        15,
        "Qwen - verdade sobre esposa",
        ok,
        "QWEN + VERACIDADE",
        "Camila Torres",
        resposta,
        ""
        if ok
        else "Qwen não utilizou a memória correta da esposa.",
    )


executar(
    15,
    "Qwen - verdade sobre esposa",
    teste_15
)


# ============================================================
# 16 — QWEN: VERDADE TIME
# ============================================================

def teste_16():

    consulta = "Qual é o meu time?"
    contexto = contexto_da(
        consulta
    )

    resposta = resposta_qwen(
        consulta,
        contexto
    )

    ok = (
        "palmeiras" in resposta.lower()
        and
        "roberto" not in resposta.lower()
    )

    mostrar(
        16,
        "Qwen - verdade sobre time",
        ok,
        "QWEN + VERACIDADE",
        "Palmeiras e nenhuma resposta desviada para Roberto",
        resposta,
        ""
        if ok
        else "Qwen recebeu contexto inadequado ou respondeu com informação errada.",
    )


executar(
    16,
    "Qwen - verdade sobre time",
    teste_16
)


# ============================================================
# 17 — QWEN: VERDADE PROJETO
# ============================================================

def teste_17():

    consulta = "Qual é meu principal projeto?"
    contexto = contexto_da(
        consulta
    )

    resposta = resposta_qwen(
        consulta,
        contexto
    )

    ok = "orion" in resposta.lower()

    mostrar(
        17,
        "Qwen - verdade sobre projeto",
        ok,
        "QWEN + VERACIDADE",
        "ORION",
        resposta,
        ""
        if ok
        else "Qwen não utilizou a memória correta do projeto.",
    )


executar(
    17,
    "Qwen - verdade sobre projeto",
    teste_17
)


# ============================================================
# 18 — QWEN: MENTIRA SOBRE TIME
# ============================================================

def teste_18():

    consulta = "Meu time é o Flamengo?"

    contexto = contexto_da(
        "Qual é o meu time?"
    )

    resposta = resposta_qwen(
        consulta,
        contexto
    )

    ok = (
        resposta_negativa(
            resposta
        )
        and
        "flamengo" not in resposta.lower()
    )

    mostrar(
        18,
        "Qwen - detecção de afirmação falsa sobre time",
        ok,
        "QWEN + VERACIDADE",
        "deve negar que o time seja Flamengo",
        resposta,
        ""
        if ok
        else "Qwen não negou corretamente a afirmação falsa.",
    )


executar(
    18,
    "Qwen - detecção de afirmação falsa sobre time",
    teste_18
)


# ============================================================
# 19 — QWEN: MENTIRA SOBRE PROFISSÃO
# ============================================================

def teste_19():

    consulta = "Eu sou médico?"

    contexto = contexto_da(
        "Com o que eu trabalho?"
    )

    resposta = resposta_qwen(
        consulta,
        contexto
    )

    ok = (
        resposta_negativa(
            resposta
        )
        and
        "médico" not in resposta.lower()
        and
        "medico" not in resposta.lower()
    )

    mostrar(
        19,
        "Qwen - detecção de afirmação falsa sobre profissão",
        ok,
        "QWEN + VERACIDADE",
        "deve negar que o usuário seja médico",
        resposta,
        ""
        if ok
        else "Qwen não negou corretamente a afirmação falsa.",
    )


executar(
    19,
    "Qwen - detecção de afirmação falsa sobre profissão",
    teste_19
)


# ============================================================
# 20 — E2E COMPLETO
# ============================================================

def teste_20():

    consulta = "Qual é o meu time?"

    # --------------------------------------------------------
    # A — TRIAGEM
    # --------------------------------------------------------

    triagem = classificador.classificar(
        consulta
    )

    intencao = str(
        triagem.get(
            "intencao",
            ""
        )
    ).strip()

    if intencao != "conversa_geral":

        mostrar(
            20,
            "Pipeline completo - esporte",
            False,
            "TRIAGEM",
            "conversa_geral",
            json.dumps(
                triagem,
                ensure_ascii=False,
            ),
            "A pergunta deveria seguir para conversa geral.",
        )

        return

    # --------------------------------------------------------
    # B — TIPO DE MEMÓRIA
    # --------------------------------------------------------

    tipo = retriever.inferir_tipo(
        consulta
    )

    if str(tipo).upper() != "ESPORTE":

        mostrar(
            20,
            "Pipeline completo - esporte",
            False,
            "TIPO DE MEMÓRIA",
            "ESPORTE",
            str(tipo),
            "O retriever não identificou a intenção esportiva.",
        )

        return

    # --------------------------------------------------------
    # C — RECUPERAÇÃO
    # --------------------------------------------------------

    contexto = contexto_da(
        consulta
    )

    if "palmeiras" not in contexto.lower():

        mostrar(
            20,
            "Pipeline completo - esporte",
            False,
            "RECUPERAÇÃO",
            "contexto contendo Palmeiras",
            contexto,
            "A memória correta não entrou no contexto.",
        )

        return

    # --------------------------------------------------------
    # D — QWEN
    # --------------------------------------------------------

    resposta = resposta_qwen(
        consulta,
        contexto
    )

    # --------------------------------------------------------
    # E — VERACIDADE
    # --------------------------------------------------------

    ok = (
        "palmeiras" in resposta.lower()
        and
        "flamengo" not in resposta.lower()
    )

    mostrar(
        20,
        "Pipeline completo - esporte",
        ok,
        "TRIAGEM → MEMÓRIA → QWEN → VERACIDADE",
        "Triagem conversa_geral + ESPORTE + Palmeiras + resposta correta",
        f"TRIAGEM={intencao} | TIPO={tipo} | "
        f"CONTEXTO={contexto} | RESPOSTA={resposta}",
        ""
        if ok
        else "Falha em uma das etapas do pipeline completo.",
    )


executar(
    20,
    "Pipeline completo - esporte",
    teste_20
)


# ============================================================
# RELATÓRIO FINAL
# ============================================================

passou = sum(
    1
    for resultado in resultados
    if resultado.passou
)

falhou = len(resultados) - passou


print()
print()
print("=" * 90)
print("RELATÓRIO FINAL — 20 TESTES")
print("=" * 90)

for resultado in resultados:

    status = (
        "OK"
        if resultado.passou
        else "ERRO"
    )

    print(
        f"{resultado.numero:02d} | "
        f"{status:5} | "
        f"{resultado.etapa:28} | "
        f"{resultado.nome}"
    )


print()
print(f"PASSOU : {passou}/20")
print(f"FALHOU : {falhou}/20")
print()


# ============================================================
# DIAGNÓSTICO POR ETAPA
# ============================================================

etapas = {}

for resultado in resultados:

    if resultado.passou:
        continue

    etapas.setdefault(
        resultado.etapa,
        []
    ).append(
        resultado.numero
    )


if etapas:

    print("=" * 90)
    print("DIAGNÓSTICO DAS FALHAS")
    print("=" * 90)

    for etapa, numeros in etapas.items():

        print()
        print(
            f"ETAPA: {etapa}"
        )

        print(
            "TESTES:",
            ", ".join(
                str(numero)
                for numero in numeros
            )
        )

    print()

    for resultado in resultados:

        if resultado.passou:
            continue

        print("-" * 90)
        print(
            f"TESTE {resultado.numero:02d} — "
            f"{resultado.nome}"
        )
        print(
            f"ETAPA: {resultado.etapa}"
        )
        print(
            f"ESPERADO: {resultado.esperado}"
        )
        print(
            f"OBTIDO: {resultado.obtido}"
        )
        print(
            f"ERRO: {resultado.erro}"
        )


print()
print("=" * 90)

if falhou == 0:

    print("RESULTADO FINAL: OK")
    print("20/20 TESTES PASSARAM")
    print("PIPELINE J.A.R.V.I.S APROVADO")

else:

    print("RESULTADO FINAL: FALHA")
    print(
        f"{falhou} TESTE(S) FALHARAM"
    )
    print(
        "VERIFIQUE O DIAGNÓSTICO ACIMA"
    )

print("=" * 90)


# ============================================================
# LIMPEZA
# ============================================================

try:
    temp_dir.cleanup()
except Exception:
    pass
