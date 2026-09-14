# -*- coding: utf-8 -*-

"""
J.A.R.V.I.S — TESTES END-TO-END
10 testes automáticos do pipeline de memória + Qwen + habilidades.

Resultado esperado:
PASSOU: 10/10
ou
FALHOU: X/10

Em caso de falha, mostra:
- teste
- etapa
- entrada
- resultado obtido
- motivo provável
"""

from __future__ import annotations

import json
import traceback
from dataclasses import dataclass
from typing import Any

from memoria_retriever import MemoriaRetriever
from ai.cerebro import perguntar, decidir_habilidade
from habilidades.gerenciador import GerenciadorHabilidades


@dataclass
class ResultadoTeste:
    numero: int
    nome: str
    passou: bool
    etapa: str
    detalhe: str
    esperado: str
    obtido: str


resultados: list[ResultadoTeste] = []


def registrar(
    numero: int,
    nome: str,
    passou: bool,
    etapa: str,
    detalhe: str,
    esperado: str,
    obtido: str,
) -> None:

    resultados.append(
        ResultadoTeste(
            numero=numero,
            nome=nome,
            passou=passou,
            etapa=etapa,
            detalhe=detalhe,
            esperado=esperado,
            obtido=obtido,
        )
    )

    status = "OK" if passou else "FALHA"

    print()
    print("=" * 78)
    print(f"[{status}] TESTE {numero:02d} - {nome}")
    print(f"ETAPA: {etapa}")
    print(f"ESPERADO: {esperado}")
    print(f"OBTIDO:   {obtido}")

    if detalhe:
        print(f"MOTIVO:   {detalhe}")


def texto_limpo(valor: Any) -> str:
    return " ".join(str(valor or "").strip().split())


def contem(texto: str, *termos: str) -> bool:
    texto = texto.lower()

    return all(
        termo.lower() in texto
        for termo in termos
    )


def executar_teste(
    numero: int,
    nome: str,
    funcao,
) -> None:

    try:
        funcao()

    except Exception as erro:

        registrar(
            numero,
            nome,
            False,
            "EXCEÇÃO",
            traceback.format_exc(),
            "Execução sem exceção",
            f"{type(erro).__name__}: {erro}",
        )


print()
print("=" * 78)
print("J.A.R.V.I.S — TESTE END-TO-END")
print("=" * 78)
print("Iniciando componentes reais...")
print()

# ------------------------------------------------------------------
# COMPONENTES REAIS
# ------------------------------------------------------------------

try:
    retriever = MemoriaRetriever()
    gerenciador = GerenciadorHabilidades()

    habilidades = gerenciador.listar()

    print(f"Memórias carregadas: OK")
    print(f"Habilidades carregadas: {len(habilidades)}")

except Exception as erro:

    print()
    print("FALHA CRÍTICA AO INICIALIZAR COMPONENTES")
    print(f"{type(erro).__name__}: {erro}")
    print()
    print(traceback.format_exc())
    raise SystemExit(1)


# ==================================================================
# TESTE 01
# ==================================================================

def teste_01_nome():

    consulta = "Qual é o meu nome?"
    contexto = retriever.contexto(consulta)

    ok = contem(
        contexto,
        "meu nome é alex"
    )

    registrar(
        1,
        "Memória - nome do usuário",
        ok,
        "MemoriaRetriever",
        "Verificação da memória permanente do nome.",
        "[NOME] Meu nome é Alex.",
        contexto,
    )


executar_teste(
    1,
    "Memória - nome do usuário",
    teste_01_nome,
)


# ==================================================================
# TESTE 02
# ==================================================================

def teste_02_esposa():

    consulta = "Qual é o nome da minha esposa?"
    contexto = retriever.contexto(consulta)

    ok = (
        "mariana praxedes" in contexto.lower()
        and "esposa" in contexto.lower()
    )

    registrar(
        2,
        "Memória - esposa",
        ok,
        "MemoriaRetriever",
        "Verifica classificação FAMILIA e recuperação da memória correta.",
        "Memória contendo Mariana Praxedes.",
        contexto,
    )


executar_teste(
    2,
    "Memória - esposa",
    teste_02_esposa,
)


# ==================================================================
# TESTE 03
# ==================================================================

def teste_03_cidade():

    consulta = "Qual cidade eu moro?"
    contexto = retriever.contexto(consulta)

    ok = (
        "maribondo" in contexto.lower()
        and "alagoas" in contexto.lower()
    )

    registrar(
        3,
        "Memória - cidade",
        ok,
        "MemoriaRetriever",
        "Verifica recuperação da informação geográfica conhecida.",
        "Maribondo / Alagoas.",
        contexto,
    )


executar_teste(
    3,
    "Memória - cidade",
    teste_03_cidade,
)


# ==================================================================
# TESTE 04
# ==================================================================

def teste_04_time():

    consulta = "Qual é o meu time?"
    contexto = retriever.contexto(consulta)

    ok = (
        "palmeiras" in contexto.lower()
    )

    registrar(
        4,
        "Memória - time",
        ok,
        "MemoriaRetriever",
        "Verifica se uma pergunta esportiva não recupera a memória do nome.",
        "Memória contendo Palmeiras.",
        contexto,
    )


executar_teste(
    4,
    "Memória - time",
    teste_04_time,
)


# ==================================================================
# TESTE 05
# ==================================================================

def teste_05_alimento():

    consulta = "Qual é minha comida favorita?"
    contexto = retriever.contexto(consulta)

    ok = (
        "pizza" in contexto.lower()
    )

    registrar(
        5,
        "Memória - preferência",
        ok,
        "MemoriaRetriever",
        "Verifica recuperação de preferência pessoal.",
        "Memória contendo pizza.",
        contexto,
    )


executar_teste(
    5,
    "Memória - preferência",
    teste_05_alimento,
)


# ==================================================================
# TESTE 06
# ==================================================================

def teste_06_qwen_esposa():

    consulta = "Qual é o nome da minha esposa?"
    contexto = retriever.contexto(consulta)

    resposta = texto_limpo(
        perguntar(
            consulta,
            contexto
        )
    )

    ok = (
        "mariana praxedes" in resposta.lower()
    )

    registrar(
        6,
        "Qwen - resposta usando memória da esposa",
        ok,
        "Qwen",
        "O modelo deve responder usando o contexto recuperado.",
        "Resposta mencionando Mariana Praxedes.",
        resposta,
    )


executar_teste(
    6,
    "Qwen - resposta usando memória da esposa",
    teste_06_qwen_esposa,
)


# ==================================================================
# TESTE 07
# ==================================================================

def teste_07_qwen_cidade():

    consulta = "Qual cidade eu moro?"
    contexto = retriever.contexto(consulta)

    resposta = texto_limpo(
        perguntar(
            consulta,
            contexto
        )
    )

    ok = (
        "maribondo" in resposta.lower()
        and "alagoas" in resposta.lower()
    )

    registrar(
        7,
        "Qwen - resposta usando memória da cidade",
        ok,
        "Qwen",
        "O modelo deve usar a memória correta da localização.",
        "Resposta mencionando Maribondo e Alagoas.",
        resposta,
    )


executar_teste(
    7,
    "Qwen - resposta usando memória da cidade",
    teste_07_qwen_cidade,
)


# ==================================================================
# TESTE 08
# ==================================================================

def teste_08_qwen_time():

    consulta = "Qual é o meu time?"
    contexto = retriever.contexto(consulta)

    resposta = texto_limpo(
        perguntar(
            consulta,
            contexto
        )
    )

    ok = (
        "palmeiras" in resposta.lower()
        and "alex" not in resposta.lower()
    )

    registrar(
        8,
        "Qwen - seleção da memória correta",
        ok,
        "Qwen + Memória",
        "Este teste detecta o problema anterior em que a pergunta do time recebia a memória do nome.",
        "Resposta contendo Palmeiras e sem responder com o nome Alex.",
        resposta,
    )


executar_teste(
    8,
    "Qwen - seleção da memória correta",
    teste_08_qwen_time,
)


# ==================================================================
# TESTE 09
# ==================================================================

def teste_09_decisao_habilidade():

    comando = "abra o bloco de notas"

    decisao = decidir_habilidade(
        comando,
        habilidades,
        ""
    )

    tipo = str(
        decisao.get("tipo", "")
    ).lower()

    nome = str(
        decisao.get("nome", "")
    )

    ok = (
        isinstance(decisao, dict)
        and tipo in {
            "habilidade",
            "resposta",
        }
    )

    registrar(
        9,
        "Qwen - decisão operacional",
        ok,
        "decidir_habilidade",
        "Testa o cérebro operacional sem executar a ação.",
        "JSON válido com tipo habilidade ou resposta.",
        json.dumps(
            decisao,
            ensure_ascii=False
        ),
    )


executar_teste(
    9,
    "Qwen - decisão operacional",
    teste_09_decisao_habilidade,
)


# ==================================================================
# TESTE 10
# ==================================================================

def teste_10_memoria_nao_contamina_comando():

    comando = "abra o bloco de notas"

    decisao = decidir_habilidade(
        comando,
        habilidades,
        contexto_memoria=""
    )

    texto_decisao = json.dumps(
        decisao,
        ensure_ascii=False
    ).lower()

    memoria_indesejada = any(
        termo in texto_decisao
        for termo in [
            "mariana praxedes",
            "palmeiras",
            "maribondo",
            "pizza",
            "meu nome é alex",
        ]
    )

    tipo = str(
        decisao.get("tipo", "")
    ).lower()

    ok = (
        not memoria_indesejada
        and tipo in {
            "habilidade",
            "resposta",
        }
    )

    registrar(
        10,
        "Separação - memória não contamina comando",
        ok,
        "Orquestrador",
        "Comando operacional não deve receber memória pessoal sem necessidade.",
        "Decisão operacional sem memórias pessoais.",
        json.dumps(
            decisao,
            ensure_ascii=False
        ),
    )


executar_teste(
    10,
    "Separação - memória não contamina comando",
    teste_10_memoria_nao_contamina_comando,
)


# ==================================================================
# RELATÓRIO FINAL
# ==================================================================

passou = sum(
    1 for resultado in resultados
    if resultado.passou
)

falhou = len(resultados) - passou

print()
print()
print("=" * 78)
print("RELATÓRIO FINAL")
print("=" * 78)

for resultado in resultados:

    status = "OK" if resultado.passou else "ERRO"

    print(
        f"{resultado.numero:02d} | "
        f"{status:5} | "
        f"{resultado.nome}"
    )

print()
print(f"PASSOU : {passou}/10")
print(f"FALHOU : {falhou}/10")
print()

if falhou == 0:

    print("=" * 78)
    print("RESULTADO FINAL: OK")
    print("PIPELINE END-TO-END APROVADO")
    print("=" * 78)

else:

    print("=" * 78)
    print("RESULTADO FINAL: FALHA")
    print("=" * 78)
    print()

    print("DIAGNÓSTICO DOS TESTES QUE FALHARAM:")
    print()

    for resultado in resultados:

        if resultado.passou:
            continue

        print("-" * 78)
        print(
            f"TESTE {resultado.numero:02d}: "
            f"{resultado.nome}"
        )
        print(f"ETAPA: {resultado.etapa}")
        print(f"ESPERADO: {resultado.esperado}")
        print(f"OBTIDO: {resultado.obtido}")
        print(f"MOTIVO: {resultado.detalhe}")

    print()
    print("RESULTADO FINAL: FALHA")
