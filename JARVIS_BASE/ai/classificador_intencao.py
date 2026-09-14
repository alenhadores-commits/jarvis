# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import unicodedata
from typing import Any


LIMIAR_CONFIANCA = 0.65


INTENCOES: dict[str, list[str]] = {

    "pesquisa_atualidade": [
        "atual",
        "atualmente",
        "agora",
        "hoje",
        "ontem",
        "amanha",
        "esta semana",
        "essa semana",
        "este ano",
        "esse ano",
        "ultima",
        "ultimo",
        "mais recente",
        "recentemente",
        "recentes",
        "resultado",
        "noticia",
        "noticias",
        "quem venceu",
        "quem ganhou",
        "quem ocupa atualmente",
        "presidente atual",
        "preco atual",
        "quanto custa atualmente",
    ],

    "pesquisa_geral": [
        "pesquise",
        "pesquisar",
        "pesquisa",
        "procure",
        "procurar",
        "busque",
        "buscar",
        "na internet",
        "no google",
        "faca uma pesquisa",
        "quero pesquisar",
        "quero uma pesquisa",
    ],

    "configuracoes": [
        "abrir configuracoes",
        "abrir minhas configuracoes",
        "mostrar configuracoes",
        "quero configurar o jarvis",
        "configurar o jarvis",
        "painel de configuracoes",
        "entrar nas configuracoes",
        "ir para configuracoes",
    ],

    "ensino": [
        "ensinar uma habilidade",
        "ensinar um comando",
        "quero ensinar",
        "ensine o jarvis",
        "aprender um comando",
        "criar uma habilidade",
        "ensino por frase",
    ],

    "gerenciamento": [
        "gerenciar comandos",
        "gerenciar habilidades",
        "listar meus comandos",
        "listar habilidades",
        "meus comandos",
        "ativar comando",
        "desativar comando",
        "editar comando",
        "remover comando",
    ],

    "memoria": [
        "lembre disso",
        "guarde isso",
        "memorize isso",
        "salve isso na memoria",
        "lembre que",
        "guarde que",
        "nao esqueca",
        "minha memoria",
        "o que voce lembra",
        "o que lembra de mim",
    ],

    "abrir_programa": [
        "abra a calculadora",
        "abrir a calculadora",
        "inicie a calculadora",
        "abra o bloco de notas",
        "abrir o bloco de notas",
        "abra o notepad",
        "abra o chrome",
        "abrir o chrome",
        "inicie o chrome",
        "abra o navegador",
        "abrir o navegador",
        "inicie o navegador",
    ],

    "abrir_site": [
        "abra o google",
        "abrir o google",
        "abra o youtube",
        "abrir o youtube",
        "abra o facebook",
        "abrir um site",
        "abra um site",
        "acesse o google",
        "acesse o youtube",
    ],

    "controlar_mouse": [
        "mova o mouse",
        "mover o mouse",
        "clique na tela",
        "clicar na tela",
        "clique com o botao direito",
        "botao direito",
        "duplo clique",
        "dar duplo clique",
        "arraste o mouse",
        "arrastar o mouse",
    ],

    "teclado": [
        "digite isso",
        "digitar isso",
        "pressione enter",
        "pressione uma tecla",
        "pressionar uma tecla",
        "use o teclado",
        "use o atalho",
        "pressione control c",
        "pressione control v",
        "pressione ctrl c",
        "pressione ctrl v",
    ],

    "ler_tela": [
        "leia a tela",
        "ler a tela",
        "o que aparece na tela",
        "o que esta na tela",
        "leia o que esta escrito",
        "o que esta escrito na tela",
    ],

    "navegador": [
        "volte uma pagina",
        "avance uma pagina",
        "recarregue a pagina",
        "volte no navegador",
        "avance no navegador",
        "recarregue o navegador",
        "feche a aba",
        "abra uma nova aba",
    ],

    "encerrar_conversa": [
        "encerrar conversa",
        "encerrar o chat",
        "terminar conversa",
        "finalizar conversa",
        "sair da conversa",
        "sair do chat",
        "fim da conversa",
    ],

    "conversa_geral": [
        "ola jarvis",
        "oi jarvis",
        "bom dia",
        "boa tarde",
        "boa noite",
        "como voce esta",
        "converse comigo",
        "me explique isso",
        "o que voce acha",
        "tenho uma duvida",
        "me conte uma coisa",
        "o que e fotossintese",
        "como funciona um motor",
        "explique inteligencia artificial",
        "o que significa isso",
    ],
}


# ============================================================
# EXPRESSOES FORTES
# ============================================================

REGRAS_FORTES: dict[str, tuple[str, ...]] = {

    "encerrar_conversa": (
        "encerrar conversa",
        "encerrar o chat",
        "terminar conversa",
        "finalizar conversa",
        "sair da conversa",
        "sair do chat",
    ),

    "configuracoes": (
        "abrir minhas configuracoes",
        "abrir configuracoes",
        "mostrar configuracoes",
        "abrir painel de configuracoes",
        "quero configurar o jarvis",
    ),

    "ensino": (
        "quero ensinar uma habilidade",
        "ensinar uma habilidade",
        "ensinar um comando",
        "quero ensinar o jarvis",
    ),

    "gerenciamento": (
        "gerenciar comandos",
        "gerenciar habilidades",
        "listar meus comandos",
        "listar habilidades",
    ),

    "abrir_programa": (
        "abra a calculadora",
        "abrir a calculadora",
        "abra o bloco de notas",
        "abrir o bloco de notas",
        "abra o chrome",
        "abrir o chrome",
        "abra o navegador",
        "abrir o navegador",
    ),

    "abrir_site": (
        "abra o google",
        "abrir o google",
        "abra o youtube",
        "abrir o youtube",
    ),
}


# ============================================================
# NORMALIZACAO
# ============================================================

def normalizar(texto: str) -> str:
    texto = str(texto or "").strip().lower()

    texto = unicodedata.normalize(
        "NFD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto


def tokens(texto: str) -> set[str]:
    return set(
        re.findall(
            r"[a-z0-9]+",
            texto
        )
    )


# ============================================================
# CLASSIFICADOR
# ============================================================

class ClassificadorIntencao:

    def __init__(self) -> None:

        print(
            "JARVIS: Centro de triagem leve carregado."
        )

    # --------------------------------------------------------
    # REGRAS DIRETAS
    # --------------------------------------------------------

    def _regra_direta(
        self,
        texto: str,
    ) -> dict[str, Any] | None:

        texto_n = normalizar(
            texto
        )

        # ----------------------------------------------------
        # CONSULTAS DIRETAS A MEMORIA DO USUARIO
        # ----------------------------------------------------
        #
        # Perguntas como "qual e meu nome" nao devem depender
        # da pontuacao por similaridade.
        #
        # A funcao da triagem aqui e decidir se vale consultar
        # a memoria. A resposta sera responsabilidade do Core.
        #

        marcadores_consulta_memoria = (
            "qual e meu ",
            "qual e minha ",
            "qual e o meu ",
            "qual e a minha ",
            "qual foi meu ",
            "qual foi minha ",
            "quem eu sou",
            "onde eu trabalho",
            "onde eu moro",
            "o que voce lembra de mim",
            "o que voce sabe sobre mim",
            "voce lembra de mim",
            "voce lembra que",
            "voce lembra ",
            "lembra de mim",
            "lembra que",
            "lembra ",
            "voce sabe meu ",
            "voce sabe minha ",
            "voce sabe sobre mim",
            "meu nome",
            "minha comida favorita",
            "meu principal projeto",
            "meu projeto",
            "meu time",
            "minha preferencia",
            "minhas preferencias",
        )

        if any(
            marcador in texto_n
            for marcador in marcadores_consulta_memoria
        ):
            return {
                "intencao": "memoria",
                "tipo": "MEMORIA",
                "confianca": 1.0,
                "aceita": True,
                "relevante": True,
                "consultar_memoria": True,
                "salvar_memoria": False,
                "metodo": "regra_consulta_memoria",
            }

        # Pesquisa explicita sempre vence.
        termos_pesquisa = (
            "pesquise",
            "pesquisar",
            "pesquisa",
            "procure",
            "procurar",
            "busque",
            "buscar",
        )

        if (
            texto_n.startswith(
                termos_pesquisa
            )
            or "na internet" in texto_n
            or "no google" in texto_n
            or "faca uma pesquisa" in texto_n
            or "quero pesquisar" in texto_n
            or "quero uma pesquisa" in texto_n
        ):
            return {
                "intencao": "pesquisa_geral",
                "confianca": 1.0,
                "aceita": True,
                "metodo": "regra_pesquisa",
            }

        # ----------------------------------------------------
        # MEMORIA / PREFERENCIA
        # ----------------------------------------------------
        #
        # Frases sobre como o JARVIS deve tratar o usuario
        # possuem prioridade sobre marcadores temporais.
        #

        marcadores_memoria = (
            "me chame",
            "me chama",
            "quero que me chame",
            "quero ser chamado",
            "quero ser tratado",
            "trate me",
            "trate-me",
            "me trate",
            "meu nome e",
            "meu nome é",
            "eu sou",
            "sou o",
            "sou a",
            "guarde isso",
            "lembre disso",
            "memorize isso",
            "lembre que",
            "guarde que",
            "nao esqueca",
        )

        if any(
            marcador in texto_n
            for marcador in marcadores_memoria
        ):
            return {
                "intencao": "memoria",
                "confianca": 1.0,
                "aceita": True,
                "metodo": "regra_memoria",
            }

        # ----------------------------------------------------
        # ATUALIDADE / INFORMACAO TEMPORAL
        # ----------------------------------------------------
        #
        # Nao usar palavras isoladas como "agora" ou "atual",
        # pois elas podem aparecer em preferencias e conversa.
        #

        frases_atualidade = (
            "presidente atual",
            "presidente de hoje",
            "governo atual",
            "preco atual",
            "quanto custa atualmente",
            "resultado de ontem",
            "resultado do jogo de ontem",
            "resultado de hoje",
            "resultado mais recente",
            "noticia de hoje",
            "noticias de hoje",
            "noticias mais recentes",
            "o que aconteceu hoje",
            "o que aconteceu ontem",
            "o que aconteceu esta semana",
            "o que aconteceu essa semana",
            "o que esta acontecendo agora",
            "quem venceu ontem",
            "quem ganhou ontem",
            "quem venceu hoje",
            "quem ganhou hoje",
            "quem ganhou a ultima",
            "quem venceu a ultima",
            "quem e o atual",
            "quem ocupa atualmente",
            "mais recente",
            "recentemente",
        )

        if any(
            frase in texto_n
            for frase in frases_atualidade
        ):
            return {
                "intencao": "pesquisa_atualidade",
                "confianca": 1.0,
                "aceita": True,
                "metodo": "regra_temporal",
            }

        # Palavras temporais isoladas só valem como pesquisa
        # quando aparecem junto de um contexto informativo.
        tem_tempo = any(
            marcador in texto_n
            for marcador in (
                "hoje",
                "ontem",
                "amanha",
                "atualmente",
                "ultima",
                "ultimo",
                "recentes",
                "recente",
            )
        )

        tem_contexto_pesquisa = any(
            termo in texto_n
            for termo in (
                "resultado",
                "noticia",
                "preco",
                "presidente",
                "governo",
                "eleicao",
                "jogo",
                "copa",
                "campeonato",
                "vencedor",
                "vencedora",
                "quem ganhou",
                "quem venceu",
                "o que aconteceu",
            )
        )

        if tem_tempo and tem_contexto_pesquisa:
            return {
                "intencao": "pesquisa_atualidade",
                "confianca": 1.0,
                "aceita": True,
                "metodo": "regra_temporal",
            }

        # Comandos críticos.
        for intencao, frases in REGRAS_FORTES.items():

            for frase in frases:

                frase_n = normalizar(
                    frase
                )

                if texto_n == frase_n:
                    return {
                        "intencao": intencao,
                        "confianca": 1.0,
                        "aceita": True,
                        "metodo": "regra_direta",
                    }

        return None

    # --------------------------------------------------------
    # PONTUACAO
    # --------------------------------------------------------

    def _pontuar(
        self,
        texto: str,
    ) -> dict[str, Any]:

        texto_n = normalizar(
            texto
        )

        tokens_texto = tokens(
            texto_n
        )

        resultados = []

        for intencao, exemplos in INTENCOES.items():

            melhor = 0.0
            melhor_exemplo = ""

            for exemplo in exemplos:

                exemplo_n = normalizar(
                    exemplo
                )

                tokens_exemplo = tokens(
                    exemplo_n
                )

                if not tokens_exemplo:
                    continue

                intersecao = (
                    tokens_texto
                    & tokens_exemplo
                )

                cobertura = (
                    len(intersecao)
                    / len(tokens_exemplo)
                )

                precisao = (
                    len(intersecao)
                    / max(
                        len(tokens_texto),
                        1
                    )
                )

                # Palavra de comando pesa mais.
                score = (
                    cobertura * 0.75
                    + precisao * 0.25
                )

                if exemplo_n in texto_n:
                    score += 0.20

                if score > melhor:
                    melhor = score
                    melhor_exemplo = exemplo_n

            if melhor > 0:
                resultados.append(
                    (
                        melhor,
                        intencao,
                        melhor_exemplo,
                    )
                )

        resultados.sort(
            reverse=True
        )

        if not resultados:

            return {
                "intencao": "conversa_geral",
                "confianca": 0.0,
                "aceita": False,
                "metodo": "sem_correspondencia",
            }

        melhor_score, melhor_intencao, melhor_exemplo = resultados[0]

        segundo_score = (
            resultados[1][0]
            if len(resultados) > 1
            else 0.0
        )

        # Evita empate perigoso entre intenções.
        margem = melhor_score - segundo_score

        confianca = min(
            round(
                melhor_score,
                4
            ),
            1.0
        )

        aceita = (
            confianca >= LIMIAR_CONFIANCA
            and margem >= 0.05
        )

        if not aceita:
            return {
                "intencao": "conversa_geral",
                "confianca": confianca,
                "aceita": False,
                "metodo": "pontuacao_baixa",
                "referencia": melhor_exemplo,
            }

        return {
            "intencao": melhor_intencao,
            "confianca": confianca,
            "aceita": True,
            "metodo": "pontuacao",
            "referencia": melhor_exemplo,
        }

    # --------------------------------------------------------
    # CLASSIFICAR
    # --------------------------------------------------------

    def classificar(
        self,
        texto: str,
    ) -> dict[str, Any]:

        texto = str(texto or "").strip()

        if not texto:
            return {
                "intencao": "conversa_geral",
                "confianca": 0.0,
                "aceita": False,
                "metodo": "vazio",
            }

        direto = self._regra_direta(
            texto
        )

        if direto is not None:
            return direto

        return self._pontuar(
            texto
        )


# ============================================================
# SINGLETON
# ============================================================

_classificador: ClassificadorIntencao | None = None


def obter_classificador() -> ClassificadorIntencao:

    global _classificador

    if _classificador is None:
        _classificador = ClassificadorIntencao()

    return _classificador


def classificar_intencao(
    texto: str,
) -> dict[str, Any]:

    return obter_classificador().classificar(
        texto
    )
