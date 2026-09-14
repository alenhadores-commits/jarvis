class ConstrutorContexto:

    def construir(
        self,
        consulta,
        resultados,
        limite=10000
    ):

        partes = []

        partes.append(
            "CONTEXTO RECUPERADO PELO JARVIS:"
        )

        partes.append(
            f"CONSULTA: {consulta}"
        )

        for numero, item in enumerate(
            resultados,
            start=1
        ):

            colecao = item.get(
                "colecao",
                "desconhecida"
            )

            documento = item.get(
                "documento",
                ""
            )

            metadata = item.get(
                "metadata",
                {}
            )

            origem = metadata.get(
                "origem",
                ""
            )

            bloco = (
                f"\n--- RESULTADO {numero} ---\n"
                f"COLEÇÃO: {colecao}\n"
                f"ORIGEM: {origem}\n"
                f"CONTEÚDO:\n{documento}\n"
            )

            partes.append(bloco)

        contexto = "\n".join(partes)

        if len(contexto) > limite:
            contexto = contexto[:limite]

        return contexto
