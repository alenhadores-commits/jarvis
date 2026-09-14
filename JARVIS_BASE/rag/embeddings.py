"""
JARVIS RAG
Embeddings locais compatíveis com ChromaDB 1.5.x.
"""

from chromadb.utils.embedding_functions import DefaultEmbeddingFunction


class EmbeddingsLocais:

    def __init__(self):
        self.funcao = DefaultEmbeddingFunction()

    def name(self):
        return "default"

    def __call__(self, input):
        return self.funcao(input)

    def embed_query(self, input):
        return self.funcao(input)

    def embed_documents(self, input):
        return self.funcao(input)

    def gerar(self, textos):
        if isinstance(textos, str):
            textos = [textos]

        return self.funcao(textos)
