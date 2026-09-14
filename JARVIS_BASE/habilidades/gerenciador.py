# -*- coding: utf-8 -*-

"""
J.A.R.V.I.S — GERENCIADOR DE HABILIDADES
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from typing import Any


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

ARQUIVO_HABILIDADES = os.path.join(
    BASE_DIR,
    "habilidades",
    "habilidades.json"
)


class GerenciadorHabilidades:

    def __init__(self):

        self.arquivo = ARQUIVO_HABILIDADES

        self._garantir_arquivo()

        self.habilidades = self.carregar()


    @staticmethod
    def normalizar(texto: str) -> str:

        texto = texto.lower().strip()

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


    def _garantir_arquivo(self) -> None:

        pasta = os.path.dirname(
            self.arquivo
        )

        os.makedirs(
            pasta,
            exist_ok=True
        )

        if not os.path.exists(
            self.arquivo
        ):
            with open(
                self.arquivo,
                "w",
                encoding="utf-8"
            ) as arquivo:

                json.dump(
                    [],
                    arquivo,
                    ensure_ascii=False,
                    indent=4
                )


    def carregar(
        self
    ) -> list[dict[str, Any]]:

        try:

            with open(
                self.arquivo,
                "r",
                encoding="utf-8"
            ) as arquivo:

                dados = json.load(
                    arquivo
                )

                if isinstance(
                    dados,
                    list
                ):
                    return dados

        except Exception as erro:

            print(
                "JARVIS: Erro ao carregar habilidades."
            )

            print(
                f"ERRO: {erro}"
            )

        return []


    def salvar(self) -> None:

        with open(
            self.arquivo,
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                self.habilidades,
                arquivo,
                ensure_ascii=False,
                indent=4
            )

        self._sincronizar_chroma()


    def _sincronizar_chroma(self) -> None:

        try:

            from rag.indexador_v2 import IndexadorV2

            raiz_projeto = os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )

            indexador = IndexadorV2(
                raiz_projeto=raiz_projeto
            )

            resultado = indexador.indexar_arquivo(
                self.arquivo,
                forcar=True
            )

            print(
                "JARVIS: Chroma sincronizado."
            )

            print(
                f"JARVIS: RAG={resultado.get('status')} "
                f"chunks={resultado.get('chunks', 0)}"
            )

        except Exception as erro:

            print(
                f"JARVIS: Aviso: nao foi possivel sincronizar o Chroma: {erro}"
            )


    def adicionar(
        self,
        nome: str,
        gatilhos: list[str],
        acoes: list[dict[str, Any]]
    ) -> dict[str, Any]:

        nome_limpo = str(nome).strip()

        gatilhos_limpos = [
            str(gatilho).strip()
            for gatilho in gatilhos
            if str(gatilho).strip()
        ]

        nome_normalizado = self.normalizar(
            nome_limpo
        )

        gatilhos_normalizados = {
            self.normalizar(gatilho)
            for gatilho in gatilhos_limpos
        }

        for indice, existente in enumerate(
            self.habilidades
        ):

            nome_existente = self.normalizar(
                existente.get("nome", "")
            )

            gatilhos_existentes = {
                self.normalizar(gatilho)
                for gatilho in existente.get(
                    "gatilhos",
                    []
                )
            }

            mesmo_nome = (
                bool(nome_normalizado)
                and nome_existente == nome_normalizado
            )

            mesmo_gatilho = bool(
                gatilhos_normalizados.intersection(
                    gatilhos_existentes
                )
            )

            if mesmo_nome or mesmo_gatilho:

                habilidade = {
                    "nome": nome_limpo,
                    "gatilhos": gatilhos_limpos,
                    "acoes": acoes,
                    "ativa": existente.get(
                        "ativa",
                        True
                    ),
                }

                self.habilidades[indice] = habilidade

                self.salvar()

                print(
                    "JARVIS: Habilidade existente atualizada."
                )

                return habilidade

        habilidade = {
            "nome": nome_limpo,
            "gatilhos": gatilhos_limpos,
            "acoes": acoes,
            "ativa": True,
        }

        self.habilidades.append(
            habilidade
        )

        self.salvar()

        return habilidade

    def encontrar(
        self,
        comando: str
    ) -> dict[str, Any] | None:

        comando = str(comando).strip()

        # Remove prefixos usados pelo JARVIS
        prefixos = (
            "jarvis,",
            "jarvis:",
        )

        comando_lower = comando.lower()

        for prefixo in prefixos:

            if comando_lower.startswith(prefixo):

                comando = comando[len(prefixo):].strip()
                break

        comando_normalizado = self.normalizar(
            comando
        )

        if not comando_normalizado:
            return None


        # ======================================================
        # 1. CORRESPONDENCIA EXATA
        # ======================================================

        for habilidade in self.habilidades:

            if not habilidade.get(
                "ativa",
                True
            ):
                continue

            for gatilho in habilidade.get(
                "gatilhos",
                []
            ):

                gatilho_normalizado = self.normalizar(
                    gatilho
                )

                if comando_normalizado == gatilho_normalizado:
                    return habilidade


        # ======================================================
        # 2. NORMALIZACAO DE VERBOS
        # ======================================================

        equivalencias = {

            "abra": "abrir",
            "abre": "abrir",
            "abrir": "abrir",

            "inicie": "iniciar",
            "inicia": "iniciar",
            "iniciar": "iniciar",

            "mostre": "mostrar",
            "mostra": "mostrar",
            "mostrar": "mostrar",

            "faca": "fazer",
            "fazer": "fazer",

            "execute": "executar",
            "executa": "executar",
            "executar": "executar",
        }


        palavras_ignoradas = {

            "o",
            "a",
            "os",
            "as",
            "um",
            "uma",

            "por",
            "favor",

            "quero",
            "pode",
            "poderia",
            "gostaria",

            "me",
            "minha",
            "meu",
        }


        def preparar(
            texto: str
        ) -> list[str]:

            palavras = self.normalizar(
                texto
            ).split()

            resultado = []

            for palavra in palavras:

                palavra = equivalencias.get(
                    palavra,
                    palavra
                )

                if palavra in palavras_ignoradas:
                    continue

                resultado.append(
                    palavra
                )

            return resultado


        palavras_comando = preparar(
            comando_normalizado
        )

        if not palavras_comando:
            return None


        # ======================================================
        # 3. COMPARACAO FLEXIVEL
        # ======================================================

        comando_set = set(
            palavras_comando
        )


        for habilidade in self.habilidades:

            if not habilidade.get(
                "ativa",
                True
            ):
                continue

            for gatilho in habilidade.get(
                "gatilhos",
                []
            ):

                palavras_gatilho = preparar(
                    gatilho
                )

                if not palavras_gatilho:
                    continue

                gatilho_set = set(
                    palavras_gatilho
                )

                if gatilho_set.issubset(
                    comando_set
                ):
                    return habilidade


        return None


    def listar(
        self
    ) -> list[dict[str, Any]]:

        return self.habilidades


    def encontrar_cadastrada(
        self,
        comando: str
    ) -> dict[str, Any] | None:

        comando = str(comando).strip()

        prefixos = (
            "jarvis,",
            "jarvis:",
        )

        comando_lower = comando.lower()

        for prefixo in prefixos:

            if comando_lower.startswith(prefixo):

                comando = comando[len(prefixo):].strip()
                break

        comando_normalizado = self.normalizar(
            comando
        )

        if not comando_normalizado:
            return None

        equivalencias = {
            "abra": "abrir",
            "abre": "abrir",
            "abrir": "abrir",
            "inicie": "iniciar",
            "inicia": "iniciar",
            "iniciar": "iniciar",
            "mostre": "mostrar",
            "mostra": "mostrar",
            "mostrar": "mostrar",
            "faca": "fazer",
            "fazer": "fazer",
            "execute": "executar",
            "executa": "executar",
            "executar": "executar",
        }

        palavras_ignoradas = {
            "o", "a", "os", "as",
            "um", "uma",
            "por", "favor",
            "quero", "pode", "poderia", "gostaria",
            "me", "minha", "meu",
        }

        def preparar(texto: str) -> list[str]:

            palavras = self.normalizar(
                texto
            ).split()

            resultado = []

            for palavra in palavras:

                palavra = equivalencias.get(
                    palavra,
                    palavra
                )

                if palavra in palavras_ignoradas:
                    continue

                resultado.append(
                    palavra
                )

            return resultado

        palavras_comando = preparar(
            comando
        )

        if not palavras_comando:
            return None

        comando_set = set(
            palavras_comando
        )

        for habilidade in self.habilidades:

            for gatilho in habilidade.get(
                "gatilhos",
                []
            ):

                palavras_gatilho = preparar(
                    gatilho
                )

                if not palavras_gatilho:
                    continue

                gatilho_set = set(
                    palavras_gatilho
                )

                if gatilho_set.issubset(
                    comando_set
                ):
                    return habilidade

        return None


    def adicionar_gatilho(
        self,
        nome: str,
        gatilho: str
    ) -> bool:

        nome_normalizado = self.normalizar(
            nome
        )

        gatilho_limpo = str(
            gatilho
        ).strip()

        if not gatilho_limpo:
            return False

        gatilho_normalizado = self.normalizar(
            gatilho_limpo
        )

        for habilidade in self.habilidades:

            if self.normalizar(
                habilidade.get(
                    "nome",
                    ""
                )
            ) != nome_normalizado:
                continue

            gatilhos = habilidade.setdefault(
                "gatilhos",
                []
            )

            existentes = {
                self.normalizar(
                    item
                )
                for item in gatilhos
            }

            if gatilho_normalizado in existentes:
                return False

            gatilhos.append(
                gatilho_limpo
            )

            self.salvar()

            return True

        return False


    def atualizar(
        self,
        nome_antigo: str,
        habilidade_nova: dict[str, Any]
    ) -> bool:

        nome_normalizado = self.normalizar(
            nome_antigo
        )

        for indice, habilidade in enumerate(
            self.habilidades
        ):

            nome_atual = self.normalizar(
                habilidade.get(
                    "nome",
                    ""
                )
            )

            if nome_atual == nome_normalizado:

                self.habilidades[indice] = habilidade_nova

                self.salvar()

                return True

        return False


    def remover(
        self,
        nome: str
    ) -> bool:

        nome_normalizado = self.normalizar(
            nome
        )

        antigas = len(
            self.habilidades
        )

        self.habilidades = [
            habilidade
            for habilidade in self.habilidades
            if self.normalizar(
                habilidade.get(
                    "nome",
                    ""
                )
            ) != nome_normalizado
        ]

        removida = len(
            self.habilidades
        ) < antigas

        if removida:
            self.salvar()

        return removida

    def menu(self) -> None:

        while True:

            print()
            print("=" * 50)
            print(" JARVIS - GERENCIADOR DE COMANDOS")
            print("=" * 50)
            print("[1] Listar comandos")
            print("[2] Ensinar novo comando")
            print("[3] Remover comando")
            print("[4] Ativar/desativar comando")
            print("[5] Voltar")
            print()

            opcao = input("Escolha: ").strip()

            if opcao == "1":

                habilidades = self.listar()

                print()
                print("COMANDOS CADASTRADOS")
                print("-" * 50)

                if not habilidades:
                    print("Nenhum comando cadastrado.")
                    input("\nPressione ENTER para continuar...")
                    continue

                for indice, habilidade in enumerate(
                    habilidades,
                    start=1
                ):

                    estado = (
                        "ATIVO"
                        if habilidade.get("ativa", True)
                        else "INATIVO"
                    )

                    nome = habilidade.get(
                        "nome",
                        "Sem nome"
                    )

                    gatilhos = habilidade.get(
                        "gatilhos",
                        []
                    )

                    print(
                        f"[{indice}] {nome} — {estado}"
                    )

                    if gatilhos:
                        print(
                            f"    Gatilhos: {', '.join(gatilhos)}"
                        )

                    acoes = habilidade.get(
                        "acoes",
                        []
                    )

                    for numero, acao in enumerate(
                        acoes,
                        start=1
                    ):

                        print(
                            f"    Acao {numero}: "
                            f"{acao.get('tipo', '')} -> "
                            f"{acao.get('valor', '')}"
                        )

                input("\nPressione ENTER para continuar...")

            elif opcao == "2":

                try:

                    from jarvis import ensinar_comando

                    ensinar_comando(
                        self
                    )

                except Exception as erro:

                    print()
                    print(
                        "JARVIS: Falha ao abrir o Centro de Ensino."
                    )

                    print(
                        f"ERRO: {erro}"
                    )

                input(
                    "\nPressione ENTER para continuar..."
                )

            elif opcao == "3":

                print()
                print("REMOVER COMANDO")
                print("-" * 50)

                nome = input(
                    "Nome do comando para remover: "
                ).strip()

                if self.remover(nome):

                    print(
                        f"JARVIS: Comando '{nome}' removido."
                    )

                else:

                    print(
                        "JARVIS: Comando não encontrado."
                    )

            elif opcao == "4":

                print()
                print("ATIVAR / DESATIVAR COMANDO")
                print("-" * 50)

                nome = input(
                    "Nome do comando: "
                ).strip()

                encontrado = None

                for habilidade in self.habilidades:

                    if self.normalizar(
                        habilidade.get(
                            "nome",
                            ""
                        )
                    ) == self.normalizar(nome):

                        encontrado = habilidade
                        break

                if encontrado is None:

                    print(
                        "JARVIS: Comando não encontrado."
                    )

                    continue

                encontrado["ativa"] = not encontrado.get(
                    "ativa",
                    True
                )

                self.salvar()

                estado = (
                    "ATIVADO"
                    if encontrado["ativa"]
                    else "DESATIVADO"
                )

                print(
                    f"JARVIS: Comando "
                    f"'{encontrado['nome']}' {estado}."
                )

            elif opcao == "5":

                print(
                    "JARVIS: Voltando ao menu principal."
                )

                return

            else:

                print(
                    "JARVIS: Opção inválida."
                )


