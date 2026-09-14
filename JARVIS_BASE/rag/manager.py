from .chroma import BancoChroma
from .indexador import Indexador
from .recuperador import Recuperador
from .router import RAGRouter
from .contexto import ConstrutorContexto
from .aprendizagem import AprendizagemRAG


class RAGManager:

    def __init__(self):

        self.banco = BancoChroma()

        self.indexador = Indexador(
            self.banco
        )

        self.recuperador = Recuperador(
            self.banco
        )

        self.router = RAGRouter()

        self.contexto = ConstrutorContexto()

        self.aprendizagem = AprendizagemRAG(
            self.banco,
            self.indexador
        )

    def buscar(
        self,
        consulta,
        quantidade=5
    ):

        colecoes = self.router.decidir(
            consulta
        )

        resultados = self.recuperador.buscar_varias(
            consulta,
            colecoes=colecoes,
            quantidade=quantidade
        )

        contexto = self.contexto.construir(
            consulta,
            resultados
        )

        return {
            "consulta": consulta,
            "colecoes": colecoes,
            "resultados": resultados,
            "contexto": contexto,
        }

    def aprender(
        self,
        objetivo,
        acao,
        resultado,
        sucesso,
        erros=None,
        solucao=None
    ):

        return self.aprendizagem.registrar_experiencia(
            objetivo=objetivo,
            acao=acao,
            resultado=resultado,
            sucesso=sucesso,
            erros=erros,
            solucao=solucao
        )

    def indexar_arquivo(
        self,
        caminho,
        colecao="conhecimento"
    ):

        return self.indexador.indexar_arquivo(
            caminho,
            colecao
        )

    def indexar_projeto(
        self,
        raiz,
        colecao="codigo"
    ):

        return self.indexador.indexar_projeto(
            raiz,
            colecao
        )

    def estatisticas(self):

        return self.banco.estatisticas()
