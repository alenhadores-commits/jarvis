class Recuperador:

    def __init__(self, banco):
        self.banco = banco

    def buscar(
        self,
        consulta,
        colecao="conhecimento",
        quantidade=5,
        where=None
    ):

        collection = self.banco.obter(
            colecao
        )

        kwargs = {
            "query_texts": [consulta],
            "n_results": quantidade,
        }

        if where:
            kwargs["where"] = where

        resultado = collection.query(
            **kwargs
        )

        documentos = (
            resultado.get("documents") or [[]]
        )[0]

        metadados = (
            resultado.get("metadatas") or [[]]
        )[0]

        ids = (
            resultado.get("ids") or [[]]
        )[0]

        distancias = (
            resultado.get("distances") or [[]]
        )[0]

        saida = []

        for i, documento in enumerate(documentos):

            saida.append({
                "id": ids[i] if i < len(ids) else None,
                "documento": documento,
                "metadata": (
                    metadados[i]
                    if i < len(metadados)
                    else {}
                ),
                "distancia": (
                    distancias[i]
                    if i < len(distancias)
                    else None
                ),
            })

        return saida

    def buscar_varias(
        self,
        consulta,
        colecoes=None,
        quantidade=5
    ):

        if colecoes is None:
            colecoes = [
                "memorias",
                "experiencias",
                "conhecimento",
                "codigo",
                "documentacao",
                "erros",
                "procedimentos",
                "projetos",
                "aprendizado",
            ]

        resultados = []

        for colecao in colecoes:

            try:

                encontrados = self.buscar(
                    consulta,
                    colecao,
                    quantidade
                )

                for item in encontrados:
                    item["colecao"] = colecao
                    resultados.append(item)

            except Exception as erro:
                print(
                    f"[RAG] Busca ignorada em {colecao}: {erro}"
                )

        resultados.sort(
            key=lambda item: (
                item["distancia"]
                if item["distancia"] is not None
                else 999999
            )
        )

        return resultados[:quantidade]
