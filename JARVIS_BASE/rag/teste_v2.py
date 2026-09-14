from rag.chroma import BancoChroma
from rag.indexador_v2 import IndexadorV2
from rag.recuperador import Recuperador


def main():

    print()
    print("=" * 70)
    print(" JARVIS - TESTE RAG V2")
    print("=" * 70)
    print()

    banco = BancoChroma()

    indexador = IndexadorV2(
        banco=banco
    )

    recuperador = Recuperador(
        banco=banco
    )

    print("[1] INDEXANDO PROJETO JARVIS")
    print()

    resultado = indexador.indexar_projeto()

    print(
        "Arquivos indexados:",
        resultado["arquivos_indexados"]
    )

    print(
        "Arquivos inalterados:",
        resultado["arquivos_inalterados"]
    )

    print(
        "Chunks de código:",
        resultado["chunks_codigo"]
    )

    print(
        "Chunks de documentação:",
        resultado["chunks_documentacao"]
    )

    print(
        "Arquivos ignorados:",
        resultado["arquivos_ignorados"]
    )

    print(
        "Erros:",
        resultado["erros"]
    )

    if resultado["erros"] > 0:
        raise RuntimeError(
            "A indexação terminou com erros."
        )

    print()
    print("[2] TESTANDO BUSCA NO CÓDIGO")
    print()

    resultados_codigo = recuperador.buscar(
        "como o JARVIS executa tarefas e comandos",
        colecoes=["codigo"],
        quantidade=5
    )

    if not resultados_codigo:
        raise RuntimeError(
            "Busca no código não retornou resultados."
        )

    for item in resultados_codigo:

        print(
            "Arquivo:",
            item.get(
                "metadata",
                {}
            ).get(
                "arquivo"
            )
        )

        print(
            "Distância:",
            item.get(
                "distancia"
            )
        )

        print(
            item.get(
                "documento",
                ""
            )[:500]
        )

        print("-" * 60)

    print()
    print("[3] TESTANDO BUSCA NA DOCUMENTAÇÃO")
    print()

    resultados_docs = recuperador.buscar(
        "arquitetura e funcionamento do JARVIS",
        colecoes=["documentacao"],
        quantidade=5
    )

    if not resultados_docs:
        print(
            "[AVISO] Nenhuma documentação encontrada."
        )
    else:

        for item in resultados_docs:

            print(
                "Arquivo:",
                item.get(
                    "metadata",
                    {}
                ).get(
                    "arquivo"
                )
            )

            print(
                "Distância:",
                item.get(
                    "distancia"
                )
            )

            print(
                item.get(
                    "documento",
                    ""
                )[:500]
            )

            print("-" * 60)

    print()
    print("[4] TESTANDO SEGUNDA EXECUÇÃO")
    print()

    segunda = indexador.indexar_projeto()

    print(
        "Novos arquivos indexados:",
        segunda["arquivos_indexados"]
    )

    print(
        "Arquivos reconhecidos como inalterados:",
        segunda["arquivos_inalterados"]
    )

    if segunda["erros"] > 0:
        raise RuntimeError(
            "A segunda indexação apresentou erros."
        )

    print()
    print("=" * 70)
    print(" RAG V2 APROVADO")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
