from rag import RAGManager


def main():

    print()
    print("=" * 70)
    print(" JARVIS - TESTE COMPLETO DO RAG LOCAL V1.1")
    print("=" * 70)
    print()

    rag = RAGManager()

    print("[1] ESTATÍSTICAS INICIAIS")
    print()

    estatisticas = rag.estatisticas()

    for nome, quantidade in estatisticas.items():
        print(
            f"  {nome:20} {quantidade}"
        )

    print()
    print("[2] INSERINDO CONHECIMENTO")
    print()

    texto = """
O JARVIS possui um sistema cognitivo.
O sistema pode planejar objetivos, executar tarefas,
avaliar resultados, detectar erros, corrigir problemas
e registrar experiências para utilização futura.

O RAG local permite recuperar semanticamente conhecimentos,
experiências, procedimentos, código e erros anteriores.
A memória semântica permite que a IA local utilize
conhecimentos acumulados pelo próprio JARVIS.
""".strip()

    quantidade = rag.indexador.indexar_texto(
        texto=texto,
        colecao="conhecimento",
        origem="teste_v11_conhecimento",
        metadata={
            "tipo": "teste",
            "projeto": "JARVIS",
            "versao": "1.1",
        }
    )

    print(
        f"[OK] {quantidade} chunks inseridos."
    )

    print()
    print("[3] INSERINDO EXPERIÊNCIA")
    print()

    aprendizagem = rag.aprender(
        objetivo="Criar executor automático",
        acao="Implementar executor e executar testes",
        resultado=(
            "Primeira tentativa falhou. "
            "Segunda tentativa funcionou."
        ),
        sucesso=True,
        erros=[
            "AttributeError no método de execução"
        ],
        solucao=(
            "Corrigir a assinatura do método "
            "e executar novamente."
        )
    )

    print(
        "[OK]",
        aprendizagem
    )

    print()
    print("[4] BUSCA SEMÂNTICA")
    print()

    consulta = (
        "Como o JARVIS pode aprender com "
        "erros de execução?"
    )

    resultado = rag.buscar(
        consulta,
        quantidade=8
    )

    print(
        "Coleções:",
        resultado["colecoes"]
    )

    print()

    if not resultado["resultados"]:
        raise RuntimeError(
            "RAG não retornou nenhum resultado."
        )

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
            "Origem:",
            item.get("metadata", {}).get(
                "origem"
            )
        )

        print(
            item.get("documento")
        )

        print()

    print("[5] TESTE DE RECUPERAÇÃO DE ERRO")
    print()

    erro = rag.buscar(
        "O JARVIS já teve AttributeError no executor?",
        quantidade=5
    )

    encontrou_erro = any(
        item.get("colecao") == "erros"
        for item in erro["resultados"]
    )

    if not encontrou_erro:
        print(
            "[AVISO] Erro não apareceu no top-k."
        )
    else:
        print(
            "[OK] Experiência de erro recuperada."
        )

    print()
    print("[6] ESTATÍSTICAS FINAIS")
    print()

    finais = rag.estatisticas()

    total = 0

    for nome, quantidade in finais.items():

        print(
            f"  {nome:20} {quantidade}"
        )

        if quantidade > 0:
            total += quantidade

    print()
    print(
        f"Total de registros/chunks: {total}"
    )

    if total <= 0:
        raise RuntimeError(
            "Nenhum dado persistido no ChromaDB."
        )

    print()
    print("=" * 70)
    print(" RAG LOCAL V1.1 FUNCIONANDO")
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
