# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any


class MemoriaReranker:

    WORKER = "memoria_reranker_worker.py"

    def __init__(self) -> None:

        self._processo = None

    def _iniciar(self) -> None:

        if (
            self._processo is not None
            and self._processo.poll() is None
        ):
            return

        caminho = (
            Path(__file__).resolve().parent
            / self.WORKER
        )

        self._processo = subprocess.Popen(
            [
                sys.executable,
                "-u",
                str(caminho),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        linha = None

        if self._processo.stderr is not None:
            pass

    @staticmethod
    def _softmax(
        valores: list[float]
    ) -> list[float]:

        if not valores:
            return []

        maior = max(
            valores
        )

        exp_values = [
            math.exp(
                max(
                    -30.0,
                    min(
                        30.0,
                        valor - maior
                    )
                )
            )
            for valor in valores
        ]

        soma = sum(
            exp_values
        )

        if soma <= 0:
            return [
                1.0 / len(valores)
                for _ in valores
            ]

        return [
            valor / soma
            for valor in exp_values
        ]

    def _scores(
        self,
        pares: list[list[str]],
    ) -> list[float]:

        self._iniciar()

        if (
            self._processo is None
            or self._processo.stdin is None
            or self._processo.stdout is None
        ):
            raise RuntimeError(
                "Worker do reranker não foi iniciado."
            )

        if (
            self._processo.poll()
            is not None
        ):
            raise RuntimeError(
                "Worker do reranker encerrou."
            )

        pedido = json.dumps(
            {
                "pares": pares
            },
            ensure_ascii=False,
        )

        try:

            self._processo.stdin.write(
                pedido + "\n"
            )

            self._processo.stdin.flush()

        except Exception as erro:

            self._processo = None

            raise RuntimeError(
                f"Falha enviando dados ao reranker: {erro}"
            ) from erro

        resposta = (
            self._processo.stdout.readline()
        )

        if not resposta:

            self._processo = None

            raise RuntimeError(
                "Worker do reranker não retornou resposta."
            )

        dados = json.loads(
            resposta
        )

        if not dados.get(
            "ok",
            False
        ):
            raise RuntimeError(
                str(
                    dados.get(
                        "erro",
                        "Erro desconhecido no reranker."
                    )
                )
            )

        scores = dados.get(
            "scores",
            []
        )

        return [
            float(valor)
            for valor in scores
        ]

    def rerank(
        self,
        consulta: str,
        candidatos: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        if not candidatos:
            return []

        consulta = str(
            consulta or ""
        ).strip()

        pares = []

        for candidato in candidatos:

            tipo = str(
                candidato.get(
                    "tipo",
                    "OUTRO"
                )
            ).strip().upper()

            conteudo = str(
                candidato.get(
                    "conteudo",
                    ""
                )
            ).strip()

            documento = (
                f"{tipo}: {conteudo}"
            )

            pares.append(
                [
                    consulta,
                    documento
                ]
            )

        brutos = self._scores(
            pares
        )

        if len(brutos) != len(
            candidatos
        ):
            raise RuntimeError(
                "Quantidade de scores do reranker "
                "não corresponde aos candidatos."
            )

        probabilidades = self._softmax(
            brutos
        )

        resultado = []

        for candidato, bruto, relativo in zip(
            candidatos,
            brutos,
            probabilidades,
        ):

            enriquecido = dict(
                candidato
            )

            enriquecido[
                "rerank_bruto"
            ] = bruto

            enriquecido[
                "rerank_relevancia"
            ] = relativo

            resultado.append(
                enriquecido
            )

        resultado.sort(
            key=lambda item:
                item.get(
                    "rerank_relevancia",
                    0.0
                ),
            reverse=True
        )

        return resultado

    def fechar(self) -> None:

        if self._processo is None:
            return

        try:

            if (
                self._processo.stdin
                is not None
            ):

                self._processo.stdin.close()

        except Exception:
            pass

        try:
            self._processo.terminate()

        except Exception:
            pass

        self._processo = None

    def __del__(self):

        try:
            self.fechar()

        except Exception:
            pass
