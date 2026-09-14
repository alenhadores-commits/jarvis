from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import StateGraph, END


class EstadoJarvis(TypedDict, total=False):
    texto: str
    analise_spacy: dict[str, Any]
    memoria: Any
    plano: Any
    resultado: Any
    erro: str
    resposta: str
    sucesso: bool
    tentativa: int
    max_tentativas: int
    recuperacao: Any


def criar_grafo_jarvis(
    compreender,
    consultar_memoria,
    planejar,
    executar,
    observar,
):
    """
    Grafo principal de decisão do JARVIS.

    Fluxo:

        COMPREENDER
             ↓
          MEMÓRIA
             ↓
          PLANEJAR
             ↓
          EXECUTAR
             ↓
          OBSERVAR
          ↙      ↘
      sucesso    erro
        ↓          ↓
       fim     RECUPERAR
                   ↓
               PLANEJAR
                   ↓
               EXECUTAR

    O executor existente continua sendo responsável
    pela execução real das ações.
    """

    def no_compreender(
        estado: EstadoJarvis,
    ) -> EstadoJarvis:

        texto = estado.get(
            "texto",
            "",
        )

        analise = compreender(
            texto
        )

        return {
            **estado,
            "analise_spacy": analise,
            "tentativa": 0,
            "max_tentativas": estado.get(
                "max_tentativas",
                2,
            ),
            "erro": "",
            "sucesso": False,
        }

    def no_memoria(
        estado: EstadoJarvis,
    ) -> EstadoJarvis:

        try:

            resultado = consultar_memoria(
                estado
            )

            return {
                **estado,
                "memoria": resultado,
            }

        except Exception as erro:

            return {
                **estado,
                "memoria": None,
                "erro": str(erro),
            }

    def no_planejar(
        estado: EstadoJarvis,
    ) -> EstadoJarvis:

        plano = planejar(
            estado
        )

        return {
            **estado,
            "plano": plano,
        }

    def no_executar(
        estado: EstadoJarvis,
    ) -> EstadoJarvis:

        tentativa = int(
            estado.get(
                "tentativa",
                0,
            )
        ) + 1

        try:

            resultado = executar(
                estado
            )

            return {
                **estado,
                "resultado": resultado,
                "erro": "",
                "tentativa": tentativa,
            }

        except Exception as erro:

            return {
                **estado,
                "resultado": None,
                "erro": str(erro),
                "tentativa": tentativa,
            }

    def no_observar(
        estado: EstadoJarvis,
    ) -> EstadoJarvis:

        try:

            sucesso = observar(
                estado
            )

        except Exception:

            sucesso = not bool(
                estado.get(
                    "erro"
                )
            )

        return {
            **estado,
            "sucesso": bool(
                sucesso
            ),
        }

    def no_recuperar_erro(
        estado: EstadoJarvis,
    ) -> EstadoJarvis:

        erro = str(
            estado.get(
                "erro",
                "",
            )
        ).strip()

        tentativa = int(
            estado.get(
                "tentativa",
                0,
            )
        )

        recuperacao = {
            "erro": erro,
            "tentativa": tentativa,
            "acao": "replanejar",
        }

        return {
            **estado,
            "recuperacao": recuperacao,
        }

    def decidir_observacao(
        estado: EstadoJarvis,
    ) -> str:

        if estado.get(
            "sucesso",
            False,
        ):
            return "fim"

        tentativa = int(
            estado.get(
                "tentativa",
                0,
            )
        )

        max_tentativas = int(
            estado.get(
                "max_tentativas",
                2,
            )
        )

        if tentativa < max_tentativas:
            return "recuperar"

        return "fim"

    grafo = StateGraph(
        EstadoJarvis
    )

    grafo.add_node(
        "compreender",
        no_compreender,
    )

    grafo.add_node(
        "memoria",
        no_memoria,
    )

    grafo.add_node(
        "planejar",
        no_planejar,
    )

    grafo.add_node(
        "executar",
        no_executar,
    )

    grafo.add_node(
        "observar",
        no_observar,
    )

    grafo.add_node(
        "recuperar_erro",
        no_recuperar_erro,
    )

    grafo.set_entry_point(
        "compreender"
    )

    grafo.add_edge(
        "compreender",
        "memoria",
    )

    grafo.add_edge(
        "memoria",
        "planejar",
    )

    grafo.add_edge(
        "planejar",
        "executar",
    )

    grafo.add_edge(
        "executar",
        "observar",
    )

    grafo.add_conditional_edges(
        "observar",
        decidir_observacao,
        {
            "recuperar": "recuperar_erro",
            "fim": END,
        },
    )

    grafo.add_edge(
        "recuperar_erro",
        "planejar",
    )

    return grafo.compile()
