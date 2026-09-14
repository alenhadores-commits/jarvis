from pathlib import Path
import hashlib

from .config import (
    EXTENSOES_CODIGO,
    IGNORAR_DIRETORIOS
)

from .chunker import Chunker


class Indexador:

    def __init__(self, banco):
        self.banco = banco
        self.chunker = Chunker()

    def _id(self, origem, indice, conteudo):
        bruto = (
            f"{origem}|"
            f"{indice}|"
            f"{conteudo}"
        )

        return hashlib.sha256(
            bruto.encode("utf-8")
        ).hexdigest()

    def indexar_texto(
        self,
        texto,
        colecao="conhecimento",
        origem="manual",
        metadata=None
    ):

        if not texto or not texto.strip():
            return 0

        collection = self.banco.obter(colecao)

        chunks = self.chunker.dividir(texto)

        ids = []
        documentos = []
        metadados = []

        base_metadata = dict(metadata or {})

        for indice, chunk in enumerate(chunks):

            doc_id = self._id(
                origem,
                indice,
                chunk
            )

            dados = dict(base_metadata)

            dados.update({
                "origem": str(origem),
                "indice_chunk": indice,
                "tipo": str(colecao),
            })

            ids.append(doc_id)
            documentos.append(chunk)
            metadados.append(dados)

        collection.upsert(
            ids=ids,
            documents=documentos,
            metadatas=metadados
        )

        return len(chunks)

    def indexar_arquivo(
        self,
        caminho,
        colecao="conhecimento"
    ):

        caminho = Path(caminho)

        if not caminho.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {caminho}"
            )

        texto = caminho.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        if not texto.strip():
            return 0

        metadata = {
            "arquivo": str(caminho),
            "extensao": caminho.suffix.lower(),
            "nome": caminho.name,
        }

        return self.indexar_texto(
            texto=texto,
            colecao=colecao,
            origem=str(caminho),
            metadata=metadata
        )

    def indexar_projeto(
        self,
        raiz,
        colecao="codigo"
    ):

        raiz = Path(raiz)

        if not raiz.exists():
            raise FileNotFoundError(
                f"Projeto não encontrado: {raiz}"
            )

        total_arquivos = 0
        total_chunks = 0

        for arquivo in raiz.rglob("*"):

            if not arquivo.is_file():
                continue

            if arquivo.suffix.lower() not in EXTENSOES_CODIGO:
                continue

            if any(
                parte in IGNORAR_DIRETORIOS
                for parte in arquivo.parts
            ):
                continue

            try:

                quantidade = self.indexar_arquivo(
                    arquivo,
                    colecao
                )

                if quantidade > 0:
                    total_arquivos += 1
                    total_chunks += quantidade

            except Exception as erro:

                print(
                    f"[RAG] Falha ao indexar "
                    f"{arquivo}: {erro}"
                )

        return {
            "arquivos": total_arquivos,
            "chunks": total_chunks,
        }
