# -*- coding: utf-8 -*-

from memoria import (
    salvar_usuario,
    salvar_memoria,
    buscar_usuario,
    consultar_memoria,
)


class GerenciadorMemoria:

    def __init__(self, user_id):
        self.user_id = user_id

    # ==========================================================
    # USUÁRIO
    # ==========================================================

    def registrar_usuario(self, nome=None):
        salvar_usuario(
            self.user_id,
            nome
        )

    def obter_usuario(self):
        return buscar_usuario(
            self.user_id
        )

    # ==========================================================
    # MEMÓRIA
    # ==========================================================

    def lembrar(
        self,
        tipo,
        duracao,
        conteudo,
        importancia=0
    ):
        return salvar_memoria(
            user_id=self.user_id,
            tipo=tipo,
            duracao=duracao,
            conteudo=conteudo,
            importancia=importancia
        )

    def lembrar_preferencia(
        self,
        conteudo,
        importancia=5
    ):
        return self.lembrar(
            tipo="PREFERENCIA",
            duracao="PERMANENTE",
            conteudo=conteudo,
            importancia=importancia
        )

    def lembrar_projeto(
        self,
        conteudo,
        importancia=5
    ):
        return self.lembrar(
            tipo="PROJETO",
            duracao="PERMANENTE",
            conteudo=conteudo,
            importancia=importancia
        )

    def lembrar_rotina(
        self,
        conteudo,
        importancia=3
    ):
        return self.lembrar(
            tipo="ROTINA",
            duracao="PERMANENTE",
            conteudo=conteudo,
            importancia=importancia
        )

    # ==========================================================
    # CONSULTA
    # ==========================================================

    def todas(self, limite=50):
        return consultar_memoria(
            self.user_id,
            limite
        )

    def contexto_textual(self, limite=20):
        """
        Converte as memórias do usuário em texto para
        serem usadas como contexto pelo JARVIS.
        """

        memorias = self.todas(limite)

        if not memorias:
            return ""

        linhas = []

        for memoria in memorias:

            tipo = memoria["tipo"]
            duracao = memoria["duracao"]
            conteudo = memoria["conteudo"]

            linhas.append(
                f"[{tipo} | {duracao}] {conteudo}"
            )

        return "\n".join(
            linhas
        )