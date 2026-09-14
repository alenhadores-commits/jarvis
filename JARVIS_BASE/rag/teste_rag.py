from rag import RAGManager


def main():

    print()
    print("=" * 60)
    print(" JARVIS - TESTE DO RAG LOCAL")
    print("=" * 60)
    print()

    rag = RAGManager()

    print("[1] Banco ChromaDB")
    print()

    estatisticas = rag.estatisticas()

    for nome, quantidade in estatisticas.items():
        print(
            f"  {nome:20} {quantidade}"
        )

    print()
    print("[2] Inserindo conhecimento de teste...")

    rag.indexador.indexar_texto(
        texto="""
O JARVIS possui um sistema cognitivo composto por
planejamento, execução, avaliação, autocorreção e
aprendizagem. O executor pode executar missões,
testar resultados e registrar experiências para uso
posterior.
""".strip(),
        colecao="conhecimento",
        origem="teste_rag",
        metadata={
            "tipo": "teste",
            "projeto": "JARVIS",
        }
    )

    print("[OK] Conhecimento inserido.")
    print()

    print("[3] Buscando semanticamente...")
    print()

    resultado = rag.buscar(
        "Como o JARVIS aprende com erros de execução?"
    )

    print(
        "Coleções consultadas:",
        resultado["colecoes"]
    )

    print()

    for numero, item in enumerate(
        resultado["resultados"],
        start=1
    ):

        print(
            f"--- RESULTADO {numero} ---"
        )

        print(
            "Coleção:",
            item.get("colecao")
        )

        print(
            "Distância:",
            item.get("distancia")
        )

        print(
            item.get("documento")
        )

        print()

    print("[4] CONTEXTO FINAL")
    print()
    print(resultado["contexto"])

    print()
    print("=" * 60)
    print(" RAG LOCAL FUNCIONANDO")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
