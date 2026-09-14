# -*- coding: utf-8 -*-

"""
J.A.R.V.I.S — MEMÓRIA LOCAL

Controla dois níveis de memória:

1. HISTÓRICO TEMPORÁRIO
   - Conversas recentes
   - Mantido em historico_conversas.json
   - Limitado para não crescer indefinidamente

2. MEMÓRIA PERMANENTE
   - Informações que JARVIS deve lembrar
   - Mantida em memorias_permanentes.json
   - Permanece entre reinicializações
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


class MemoriaLocal:
    """Gerenciador central da memória local do JARVIS."""

    LIMITE_HISTORICO = 1000

    def __init__(self) -> None:
        self.base_dir = Path(__file__).resolve().parent
        self.memoria_dir = self.base_dir / "memoria"

        self.arquivo_historico = (
            self.memoria_dir / "historico_conversas.json"
        )

        self.arquivo_permanente = (
            self.memoria_dir / "memorias_permanentes.json"
        )

        self.memoria_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self._garantir_arquivos()

    # ============================================================
    # UTILITARIOS
    # ============================================================

    @staticmethod
    def _agora() -> str:
        return datetime.now().isoformat(
            timespec="seconds"
        )

    @staticmethod
    def _ler_json(
        arquivo: Path,
        padrao: Any,
    ) -> Any:

        try:
            if not arquivo.exists():
                return padrao

            conteudo = arquivo.read_text(
                encoding="utf-8-sig"
            )

            if not conteudo.strip():
                return padrao

            return json.loads(conteudo)

        except (
            OSError,
            json.JSONDecodeError,
            TypeError,
            ValueError,
        ):
            return padrao

    @staticmethod
    def _escrever_json(
        arquivo: Path,
        dados: Any,
    ) -> None:

        temporario = arquivo.with_suffix(
            arquivo.suffix + ".tmp"
        )

        texto = json.dumps(
            dados,
            ensure_ascii=False,
            indent=4
        )

        temporario.write_text(
            texto,
            encoding="utf-8"
        )

        temporario.replace(arquivo)

    # ============================================================
    # GARANTIR ESTRUTURA
    # ============================================================

    def _garantir_arquivos(self) -> None:

        if not self.arquivo_historico.exists():

            self._escrever_json(
                self.arquivo_historico,
                {
                    "versao": 1,
                    "conversas": []
                }
            )

        if not self.arquivo_permanente.exists():

            self._escrever_json(
                self.arquivo_permanente,
                {
                    "versao": 1,
                    "memorias": []
                }
            )

    # ============================================================
    # HISTORICO TEMPORARIO
    # ============================================================

    def carregar_historico(self) -> list[dict[str, Any]]:
        """Carrega o histórico temporário."""

        dados = self._ler_json(
            self.arquivo_historico,
            {
                "versao": 1,
                "conversas": []
            }
        )

        if not isinstance(dados, dict):
            return []

        conversas = dados.get(
            "conversas",
            []
        )

        if not isinstance(conversas, list):
            return []

        return [
            item
            for item in conversas
            if isinstance(item, dict)
        ]

    def registrar_conversa(
        self,
        usuario: str,
        jarvis: str = "",
        tipo: str = "CONVERSA",
    ) -> dict[str, Any]:
        """
        Registra uma interação no histórico temporário.
        """

        usuario = str(usuario or "").strip()
        jarvis = str(jarvis or "").strip()

        if not usuario:
            return {}

        historico = self.carregar_historico()

        item = {
            "id": str(uuid.uuid4()),
            "data": self._agora(),
            "tipo": str(tipo or "CONVERSA"),
            "usuario": usuario,
            "jarvis": jarvis,
        }

        historico.append(item)

        historico = historico[
            -self.LIMITE_HISTORICO:
        ]

        self._escrever_json(
            self.arquivo_historico,
            {
                "versao": 1,
                "conversas": historico
            }
        )

        return item

    def atualizar_ultima_conversa(
        self,
        jarvis: str,
    ) -> dict[str, Any]:
        """
        Atualiza a resposta da conversa mais recente.
        """

        jarvis = str(jarvis or "").strip()

        if not jarvis:
            return {}

        historico = self.carregar_historico()

        if not historico:
            return {}

        historico[-1]["jarvis"] = jarvis
        historico[-1]["atualizado_em"] = self._agora()

        self._escrever_json(
            self.arquivo_historico,
            {
                "versao": 1,
                "conversas": historico
            }
        )

        return historico[-1]

    def ultimas_conversas(
        self,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        """Retorna as conversas mais recentes."""

        historico = self.carregar_historico()

        try:
            limite = max(
                1,
                int(limite)
            )
        except (
            TypeError,
            ValueError,
        ):
            limite = 10

        return historico[-limite:]

    def limpar_historico(self) -> None:
        """Apaga somente o histórico temporário."""

        self._escrever_json(
            self.arquivo_historico,
            {
                "versao": 1,
                "conversas": []
            }
        )

    # ============================================================
    # MEMORIA PERMANENTE
    # ============================================================

    def carregar_memorias(
        self,
    ) -> list[dict[str, Any]]:
        """Carrega as memórias permanentes."""

        dados = self._ler_json(
            self.arquivo_permanente,
            {
                "versao": 1,
                "memorias": []
            }
        )

        if not isinstance(dados, dict):
            return []

        memorias = dados.get(
            "memorias",
            []
        )

        if not isinstance(memorias, list):
            return []

        return [
            item
            for item in memorias
            if isinstance(item, dict)
        ]

    def salvar_memoria(
        self,
        conteudo: str,
        tipo: str = "OUTRO",
        importancia: int = 5,
        duracao: str = "PERMANENTE",
    ) -> dict[str, Any]:
        """
        Cria ou atualiza uma memória permanente.
        """

        conteudo = str(
            conteudo or ""
        ).strip()

        if not conteudo:
            return {}

        try:
            importancia = max(
                0,
                min(
                    10,
                    int(importancia)
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            importancia = 5

        memorias = self.carregar_memorias()

        existente = None

        for memoria in memorias:

            valor = str(
                memoria.get(
                    "conteudo",
                    ""
                )
            ).strip().lower()

            if valor == conteudo.lower():
                existente = memoria
                break

        agora = self._agora()

        if existente is not None:

            existente["tipo"] = (
                str(tipo or existente.get(
                    "tipo",
                    "OUTRO"
                ))
            )

            existente["duracao"] = (
                str(
                    duracao
                    or existente.get(
                        "duracao",
                        "PERMANENTE"
                    )
                )
            )

            existente["importancia"] = (
                importancia
            )

            existente["atualizado_em"] = (
                agora
            )

            memoria_final = existente

        else:

            memoria_final = {
                "id": str(uuid.uuid4()),
                "tipo": str(
                    tipo or "OUTRO"
                ),
                "duracao": str(
                    duracao
                    or "PERMANENTE"
                ),
                "conteudo": conteudo,
                "importancia": importancia,
                "criado_em": agora,
                "atualizado_em": agora,
            }

            memorias.append(
                memoria_final
            )

        self._escrever_json(
            self.arquivo_permanente,
            {
                "versao": 1,
                "memorias": memorias
            }
        )

        return memoria_final

    def buscar_memorias(
        self,
        consulta: str,
    ) -> list[dict[str, Any]]:
        """
        Busca memórias por palavras do texto.
        """

        consulta = str(
            consulta or ""
        ).strip().lower()

        if not consulta:
            return []

        palavras = {
            palavra
            for palavra in consulta.split()
            if len(palavra) >= 3
        }

        if not palavras:
            return []

        resultados = []

        for memoria in self.carregar_memorias():

            texto = " ".join(
                [
                    str(
                        memoria.get(
                            "tipo",
                            ""
                        )
                    ),
                    str(
                        memoria.get(
                            "conteudo",
                            ""
                        )
                    ),
                ]
            ).lower()

            pontos = sum(
                1
                for palavra in palavras
                if palavra in texto
            )

            if pontos > 0:

                copia = dict(memoria)

                copia["_relevancia"] = pontos

                resultados.append(copia)

        resultados.sort(
            key=lambda item: (
                item.get(
                    "_relevancia",
                    0
                ),
                item.get(
                    "importancia",
                    0
                ),
            ),
            reverse=True
        )

        for item in resultados:
            item.pop(
                "_relevancia",
                None
            )

        return resultados

    def remover_memoria(
        self,
        memoria_id: str,
    ) -> bool:
        """Remove uma memória permanente pelo ID."""

        memoria_id = str(
            memoria_id or ""
        ).strip()

        if not memoria_id:
            return False

        memorias = self.carregar_memorias()

        novas = [
            memoria
            for memoria in memorias
            if str(
                memoria.get(
                    "id",
                    ""
                )
            ) != memoria_id
        ]

        if len(novas) == len(memorias):
            return False

        self._escrever_json(
            self.arquivo_permanente,
            {
                "versao": 1,
                "memorias": novas
            }
        )

        return True

    def limpar_memorias(self) -> None:
        """Apaga todas as memórias permanentes."""

        self._escrever_json(
            self.arquivo_permanente,
            {
                "versao": 1,
                "memorias": []
            }
        )

    # ============================================================
    # CONTEXTO PARA A IA
    # ============================================================

    def contexto_memoria(
        self,
        consulta: str = "",
        limite_permanente: int = 10,
        limite_historico: int = 10,
    ) -> dict[str, Any]:
        """
        Monta um contexto compacto para o cérebro do JARVIS.
        """

        if consulta:
            permanentes = self.buscar_memorias(
                consulta
            )
        else:
            permanentes = self.carregar_memorias()

        permanentes = permanentes[
            :limite_permanente
        ]

        historico = self.ultimas_conversas(
            limite_historico
        )

        return {
            "memorias_permanentes": permanentes,
            "historico_recente": historico,
        }

    def status(self) -> dict[str, Any]:
        """Retorna o estado atual das duas memórias."""

        return {
            "arquivo_historico": str(
                self.arquivo_historico
            ),
            "arquivo_permanente": str(
                self.arquivo_permanente
            ),
            "total_historico": len(
                self.carregar_historico()
            ),
            "total_memorias": len(
                self.carregar_memorias()
            ),
        }


if __name__ == "__main__":

    memoria = MemoriaLocal()

    print("=" * 60)
    print(" JARVIS - MEMORIA LOCAL")
    print("=" * 60)

    estado = memoria.status()

    print(
        f"Historico: {estado['total_historico']}"
    )

    print(
        f"Memorias permanentes: "
        f"{estado['total_memorias']}"
    )

    print()
    print(
        "Arquivo temporario:"
    )
    print(
        estado["arquivo_historico"]
    )

    print()
    print(
        "Arquivo permanente:"
    )
    print(
        estado["arquivo_permanente"]
    )



