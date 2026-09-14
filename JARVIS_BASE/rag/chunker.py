from .config import CHUNK_SIZE, CHUNK_OVERLAP


class Chunker:

    def __init__(
        self,
        tamanho=CHUNK_SIZE,
        sobreposicao=CHUNK_OVERLAP
    ):
        self.tamanho = tamanho
        self.sobreposicao = sobreposicao

    def dividir(self, texto):

        if not texto:
            return []

        texto = texto.replace("\r\n", "\n")

        if len(texto) <= self.tamanho:
            return [texto]

        chunks = []

        inicio = 0
        total = len(texto)

        while inicio < total:

            fim = min(
                inicio + self.tamanho,
                total
            )

            trecho = texto[inicio:fim]

            if fim < total:
                ultimo_ponto = max(
                    trecho.rfind("\n\n"),
                    trecho.rfind("\n"),
                    trecho.rfind(". ")
                )

                if ultimo_ponto > self.tamanho * 0.55:
                    fim = inicio + ultimo_ponto + 1
                    trecho = texto[inicio:fim]

            trecho = trecho.strip()

            if trecho:
                chunks.append(trecho)

            novo_inicio = fim - self.sobreposicao

            if novo_inicio <= inicio:
                novo_inicio = fim

            inicio = novo_inicio

        return chunks
