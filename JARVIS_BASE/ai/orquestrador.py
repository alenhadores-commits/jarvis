# -*- coding: utf-8 -*-

import json
import re

from rag.chroma import BancoChroma


class Orquestrador:

    def __init__(self):
        self.banco_chroma = BancoChroma()
        self.colecao_procedimentos = self.banco_chroma.obter("procedimentos")

    def buscar_habilidade(self, texto):

        try:
            resultado = self.colecao_procedimentos.query(
                query_texts=[texto],
                n_results=1
            )

            documentos = resultado.get("documents", [[]])

            if not documentos or not documentos[0]:
                return None

            documento = documentos[0][0]

            if not isinstance(documento, str):
                return None

            documento = documento.strip()

            if not documento:
                return None

            try:
                habilidade = json.loads(documento)
            except (json.JSONDecodeError, TypeError, ValueError):
                return None

            if not isinstance(habilidade, dict):
                return None

            if not habilidade.get("ativa", True):
                return None

            return habilidade

        except Exception as erro:
            print(f"JARVIS: Erro interno ao consultar Chroma: {erro}")
            return None

    @staticmethod
    def eh_comando_clima(texto):

        texto = str(texto or "").lower().strip()

        padroes = [
            r"\btemperatura\b",
            r"\bclima\b",
            r"\btempo\b",
            r"\bchovendo\b",
            r"\bchuva\b",
            r"\bumidade\b",
            r"\bvento\b",
            r"\bsensação térmica\b",
            r"\bsensacao termica\b",
            r"\bprevisão do tempo\b",
            r"\bprevisao do tempo\b",
            r"\bprevisão\b",
            r"\bprevisao\b",
        ]

        return any(
            re.search(padrao, texto)
            for padrao in padroes
        )

    def interpretar(self, comando):

        original = comando.strip()
        texto = original.lower().strip()

        texto = re.sub(
            r"^\s*jarvis\s*[,;:]\s*",
            "",
            texto,
            flags=re.IGNORECASE
        ).strip()

        if not texto:
            return {
                "acao": "ia",
                "texto": ""
            }

        # ==========================================================
        # CLIMA
        # ==========================================================

        if self.eh_comando_clima(texto):
            return {
                "acao": "clima",
                "texto": original
            }

        # ==========================================================
        # CHROMA — HABILIDADES PROCEDURAIS
        # ==========================================================

        habilidade = self.buscar_habilidade(texto)

        if habilidade:

            acoes = habilidade.get("acoes", [])

            if acoes:

                print()
                print(
                    f"JARVIS: Habilidade encontrada: "
                    f"{habilidade.get('nome', 'sem nome')}"
                )

                return {
                    "acao": "habilidade",
                    "nome": habilidade.get("nome", ""),
                    "acoes": acoes
                }

        # ==========================================================
        # PROGRAMAS
        # ==========================================================

        programas = {
            "calculadora": "calculadora",
            "calcula": "calculadora",
            "bloco de notas": "notepad",
            "notepad": "notepad",
            "chrome": "chrome",
            "google chrome": "chrome",
            "google": "chrome",
            "edge": "msedge",
            "microsoft edge": "msedge",
            "explorador": "explorer",
            "explorador de arquivos": "explorer",
            "gerenciador de tarefas": "taskmgr",
            "prompt": "cmd",
            "cmd": "cmd",
            "powershell": "powershell",
        }

        padroes_abrir_programa = [
            r"^abra\s+(?:a|o|um|uma)?\s*(.+)$",
            r"^abrir\s+(?:a|o|um|uma)?\s*(.+)$",
            r"^inicie\s+(?:a|o|um|uma)?\s*(.+)$",
            r"^iniciar\s+(?:a|o|um|uma)?\s*(.+)$",
            r"^execute\s+(?:a|o|um|uma)?\s*(.+)$",
            r"^executar\s+(?:a|o|um|uma)?\s*(.+)$",
        ]

        for padrao in padroes_abrir_programa:

            match = re.match(padrao, texto)

            if match:

                alvo = match.group(1).strip()

                if alvo in programas:
                    return {
                        "acao": "programa",
                        "programa": programas[alvo]
                    }

        # ==========================================================
        # URL
        # ==========================================================

        url_match = re.search(
            r"(https?://[^\s]+|www\.[^\s]+)",
            original,
            re.IGNORECASE
        )

        if url_match:

            url = url_match.group(1).rstrip(".,!?")

            if not url.lower().startswith(("http://", "https://")):
                url = "https://" + url

            return {
                "acao": "abrir",
                "url": url
            }

        # ==========================================================
        # PESQUISA
        # ==========================================================

        padroes_pesquisa = [
            r"^pesquise\s+(.+)$",
            r"^pesquisar\s+(.+)$",
            r"^procure\s+(.+)$",
            r"^procura\s+(.+)$",
            r"^buscar\s+(.+)$",
            r"^busque\s+(.+)$",
            r"^busca\s+(.+)$",
            r"^faça uma pesquisa sobre\s+(.+)$",
            r"^pesquise no google\s+(.+)$",
        ]

        for padrao in padroes_pesquisa:

            match = re.match(padrao, texto)

            if match:

                consulta = match.group(1).strip()

                return {
                    "acao": "pesquisar_google",
                    "consulta": consulta
                }

        # ==========================================================
        # NAVEGAÇÃO
        # ==========================================================

        if texto in [
            "volte",
            "voltar",
            "volte uma página",
            "voltar uma página"
        ]:
            return {
                "acao": "voltar"
            }

        if texto in [
            "avance",
            "avançar",
            "avançar uma página",
            "avance uma página"
        ]:
            return {
                "acao": "avancar"
            }

        if texto in [
            "leia a página",
            "ler a página",
            "leia essa página",
            "ler essa página",
            "leia a página atual",
            "ler a página atual"
        ]:
            return {
                "acao": "ler"
            }

        # ==========================================================
        # CHROMA — HABILIDADES
        # ==========================================================

        habilidade = self.buscar_habilidade(texto)

        if habilidade:

            acoes = habilidade.get("acoes", [])

            if acoes:

                print()
                print(
                    f"JARVIS: Habilidade encontrada: "
                    f"{habilidade.get('nome', 'sem nome')}"
                )

                return {
                    "acao": "habilidade",
                    "nome": habilidade.get("nome", ""),
                    "acoes": acoes
                }

        # ==========================================================
        # IA
        # ==========================================================

        return {
            "acao": "ia",
            "texto": original
        }
