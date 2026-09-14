class RAGRouter:

    def decidir(self, consulta):

        texto = consulta.lower().strip()

        colecoes = []

        if any(
            palavra in texto
            for palavra in [
                "eu",
                "meu",
                "minha",
                "preferência",
                "prefiro",
                "lembra"
            ]
        ):
            colecoes.append("memorias")

        if any(
            palavra in texto
            for palavra in [
                "erro",
                "falha",
                "exception",
                "traceback",
                "bug"
            ]
        ):
            colecoes.append("erros")

        if any(
            palavra in texto
            for palavra in [
                "como fazer",
                "como criar",
                "procedimento",
                "passo a passo"
            ]
        ):
            colecoes.append("procedimentos")

        if any(
            palavra in texto
            for palavra in [
                "código",
                "codigo",
                "arquivo",
                "função",
                "funcao",
                "classe",
                "módulo",
                "modulo"
            ]
        ):
            colecoes.append("codigo")

        if any(
            palavra in texto
            for palavra in [
                "projeto",
                "jarvis",
                "arquitetura"
            ]
        ):
            colecoes.extend([
                "projetos",
                "documentacao"
            ])

        colecoes.extend([
            "experiencias",
            "aprendizado",
            "conhecimento"
        ])

        resultado = []

        for item in colecoes:
            if item not in resultado:
                resultado.append(item)

        return resultado
