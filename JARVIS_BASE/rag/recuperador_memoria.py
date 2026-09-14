from rag.chroma import BancoChroma
import re
import unicodedata


class RecuperadorMemoria:

    def __init__(self):
        self.banco = BancoChroma()
        self.colecao = self.banco.obter("memorias")

    @staticmethod
    def normalizar(texto):
        texto = str(texto or "").lower()
        texto = unicodedata.normalize("NFKD", texto)
        texto = "".join(
            c for c in texto
            if not unicodedata.combining(c)
        )
        texto = re.sub(r"[^a-z0-9\s_-]", " ", texto)
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto

    def palavras_importantes(self, texto):
        stopwords = {
            "a", "o", "as", "os", "um", "uma",
            "de", "do", "da", "dos", "das",
            "e", "em", "no", "na", "nos", "nas",
            "que", "qual", "quais", "me", "minha",
            "meu", "minhas", "meus", "para",
            "por", "com", "sobre", "foi", "ser",
            "é", "sao", "são", "numero"
        }

        palavras = self.normalizar(texto).split()

        return [
            p for p in palavras
            if len(p) >= 2 and p not in stopwords
        ]

    def buscar(self, consulta, limite=5):

        consulta_normalizada = self.normalizar(consulta)

        if not consulta_normalizada:
            return []

        palavras = self.palavras_importantes(consulta)

        numeros_consulta = re.findall(
            r"\b\d+\b",
            consulta_normalizada
        )

        candidatos = {}

        # ==========================================================
        # 1. BUSCA EXATA POR METADATA
        # ==========================================================

        for numero in numeros_consulta:

            try:
                numero_int = int(numero)

                direto = self.colecao.get(
                    where={"numero": numero_int},
                    include=["documents", "metadatas"]
                )

                documentos = direto.get("documents", [])
                ids = direto.get("ids", [])
                metadatas = direto.get("metadatas", [])

                for i, documento in enumerate(documentos):

                    metadata = (
                        metadatas[i]
                        if i < len(metadatas) and metadatas[i]
                        else {}
                    )

                    if i >= len(ids):
                        continue

                    candidatos[ids[i]] = {
                        "id": ids[i],
                        "documento": documento,
                        "metadados": metadata,
                        "score": 1000.0
                    }

            except Exception:
                pass

        # ==========================================================
        # 2. BUSCA SEMÂNTICA
        # ==========================================================

        resultado = self.colecao.query(
            query_texts=[consulta],
            n_results=min(max(limite * 10, 50), 100)
        )

        documentos = resultado.get("documents", [[]])[0]
        ids = resultado.get("ids", [[]])[0]
        metadatas = resultado.get("metadatas", [[]])[0]

        for i, documento in enumerate(documentos):

            doc = str(documento or "")
            doc_normalizado = self.normalizar(doc)

            metadata = (
                metadatas[i]
                if i < len(metadatas) and metadatas[i]
                else {}
            )

            identificador = ids[i] if i < len(ids) else None

            if identificador is None:
                continue

            score = 0.0

            for palavra in palavras:
                if palavra in doc_normalizado:
                    score += 10.0

            if consulta_normalizada in doc_normalizado:
                score += 50.0

            numeros_documento = re.findall(
                r"\b\d+\b",
                doc_normalizado
            )

            for numero in numeros_consulta:
                if numero in numeros_documento:
                    score += 100.0

            numero_metadata = metadata.get("numero")

            if numero_metadata is not None:
                for numero in numeros_consulta:
                    if str(numero_metadata).zfill(3) == numero.zfill(3):
                        score += 500.0

            tokens_consulta = re.findall(
                r"[a-z]+[_-]\d+",
                consulta_normalizada
            )

            for token in tokens_consulta:
                if token in doc_normalizado:
                    score += 150.0

            if identificador in candidatos:
                candidatos[identificador]["score"] = max(
                    candidatos[identificador]["score"],
                    score
                )
            else:
                candidatos[identificador] = {
                    "id": identificador,
                    "documento": doc,
                    "metadados": metadata,
                    "score": score
                }

        resultado_final = list(candidatos.values())

        resultado_final.sort(
            key=lambda x: x["score"],
            reverse=True
        )

        return resultado_final[:limite]


if __name__ == "__main__":

    recuperador = RecuperadorMemoria()

    perguntas = [
        "qual é a memoria de teste 001?",
        "me mostre a informação da memoria 050",
        "qual informação foi registrada na memoria 099?",
        "procure a memoria número 073"
    ]

    print("=== TESTE DO RECUPERADOR HIBRIDO ===")

    for pergunta in perguntas:

        print(f"\nPERGUNTA: {pergunta}")

        resultados = recuperador.buscar(
            pergunta,
            limite=3
        )

        if not resultados:
            print("Nenhum resultado encontrado.")
            continue

        for posicao, resultado in enumerate(resultados, 1):

            print(
                f"{posicao}. "
                f"[score={resultado['score']:.1f}] "
                f"{resultado['documento']}"
            )
