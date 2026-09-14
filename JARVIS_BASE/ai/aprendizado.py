from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DADOS_DIR = BASE_DIR / "dados" / "aprendizado"
EXPERIENCIAS_FILE = DADOS_DIR / "experiencias.jsonl"
MODELO_FILE = DADOS_DIR / "modelo_aprendizado.joblib"


class AprendizadoJarvis:

    def __init__(self) -> None:
        DADOS_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        self.modelo = None

        self._carregar_modelo()

    # ---------------------------------------------------------
    # EXPERIÊNCIA
    # ---------------------------------------------------------

    def registrar_experiencia(
        self,
        comando: str,
        intencao: str = "",
        acao: str = "",
        estrategia: str = "",
        resultado: Any = "",
        sucesso: bool = False,
        tentativa: int = 1,
        recompensa: float | None = None,
    ) -> dict:

        if recompensa is None:
            recompensa = self.calcular_recompensa(
                sucesso=sucesso,
                tentativa=tentativa,
            )

        experiencia = {
            "comando": str(comando or "").strip(),
            "intencao": str(intencao or "").strip(),
            "acao": str(acao or "").strip(),
            "estrategia": str(estrategia or "").strip(),
            "resultado": self._normalizar_resultado(resultado),
            "sucesso": bool(sucesso),
            "tentativa": int(tentativa),
            "recompensa": float(recompensa),
        }

        with EXPERIENCIAS_FILE.open(
            "a",
            encoding="utf-8"
        ) as arquivo:

            arquivo.write(
                json.dumps(
                    experiencia,
                    ensure_ascii=False,
                )
                + "\n"
            )

        return experiencia

    # ---------------------------------------------------------
    # RECOMPENSA
    # ---------------------------------------------------------

    def calcular_recompensa(
        self,
        sucesso: bool,
        tentativa: int = 1,
    ) -> float:

        if sucesso:

            if tentativa <= 1:
                return 1.0

            return max(
                0.5,
                1.0 - (
                    (tentativa - 1) * 0.2
                )
            )

        return -1.0

    # ---------------------------------------------------------
    # LEITURA
    # ---------------------------------------------------------

    def carregar_experiencias(self) -> list[dict]:

        if not EXPERIENCIAS_FILE.exists():
            return []

        experiencias = []

        with EXPERIENCIAS_FILE.open(
            "r",
            encoding="utf-8"
        ) as arquivo:

            for linha in arquivo:

                linha = linha.strip()

                if not linha:
                    continue

                try:

                    item = json.loads(
                        linha
                    )

                    if isinstance(
                        item,
                        dict
                    ):
                        experiencias.append(
                            item
                        )

                except Exception:
                    continue

        return experiencias

    # ---------------------------------------------------------
    # ESTATÍSTICAS
    # ---------------------------------------------------------

    def obter_estatisticas(self) -> dict:

        experiencias = (
            self.carregar_experiencias()
        )

        total = len(
            experiencias
        )

        sucessos = sum(
            1
            for item in experiencias
            if item.get(
                "sucesso",
                False
            )
        )

        falhas = total - sucessos

        taxa_sucesso = (
            sucessos / total
            if total
            else 0.0
        )

        return {
            "total": total,
            "sucessos": sucessos,
            "falhas": falhas,
            "taxa_sucesso": taxa_sucesso,
        }

    # ---------------------------------------------------------
    # TREINAMENTO
    # ---------------------------------------------------------

    def treinar(self) -> dict:

        experiencias = (
            self.carregar_experiencias()
        )

        if len(experiencias) < 5:

            return {
                "treinado": False,
                "motivo": (
                    "Experiências insuficientes."
                ),
                "quantidade": len(
                    experiencias
                ),
            }

        try:

            from sklearn.feature_extraction.text import (
                TfidfVectorizer
            )

            from sklearn.linear_model import (
                LogisticRegression
            )

            import joblib

        except Exception as erro:

            return {
                "treinado": False,
                "motivo": (
                    "Dependência ausente: "
                    + str(erro)
                ),
            }

        textos = []
        alvos = []

        for item in experiencias:

            comando = str(
                item.get(
                    "comando",
                    ""
                )
            ).strip()

            acao = str(
                item.get(
                    "acao",
                    ""
                )
            ).strip()

            intencao = str(
                item.get(
                    "intencao",
                    ""
                )
            ).strip()

            texto = " ".join(
                part
                for part in (
                    comando,
                    intencao,
                    acao,
                )
                if part
            )

            if not texto:
                continue

            textos.append(
                texto
            )

            alvos.append(
                int(
                    bool(
                        item.get(
                            "sucesso",
                            False
                        )
                    )
                )
            )

        if len(
            set(alvos)
        ) < 2:

            return {
                "treinado": False,
                "motivo": (
                    "É necessário ter "
                    "experiências de sucesso "
                    "e falha."
                ),
            }

        vetor = TfidfVectorizer(
            lowercase=True,
            ngram_range=(1, 2),
            max_features=2000,
        )

        X = vetor.fit_transform(
            textos
        )

        modelo = LogisticRegression(
            max_iter=1000
        )

        modelo.fit(
            X,
            alvos
        )

        self.modelo = {
            "vetor": vetor,
            "modelo": modelo,
        }

        joblib.dump(
            self.modelo,
            MODELO_FILE
        )

        return {
            "treinado": True,
            "quantidade": len(
                textos
            ),
            "arquivo": str(
                MODELO_FILE
            ),
        }

    # ---------------------------------------------------------
    # PREVISÃO
    # ---------------------------------------------------------

    def prever_sucesso(
        self,
        comando: str,
        intencao: str = "",
        acao: str = "",
    ) -> float:

        if not self.modelo:
            return 0.5

        texto = " ".join(
            part
            for part in (
                str(comando or "").strip(),
                str(intencao or "").strip(),
                str(acao or "").strip(),
            )
            if part
        )

        if not texto:
            return 0.5

        try:

            vetor = self.modelo[
                "vetor"
            ]

            modelo = self.modelo[
                "modelo"
            ]

            X = vetor.transform(
                [texto]
            )

            probabilidades = (
                modelo.predict_proba(
                    X
                )[0]
            )

            classes = list(
                modelo.classes_
            )

            if 1 in classes:

                indice = classes.index(
                    1
                )

                return float(
                    probabilidades[
                        indice
                    ]
                )

        except Exception:
            pass

        return 0.5

    # ---------------------------------------------------------
    # MODELO
    # ---------------------------------------------------------

    def _carregar_modelo(
        self
    ) -> None:

        if not MODELO_FILE.exists():
            return

        try:

            import joblib

            self.modelo = (
                joblib.load(
                    MODELO_FILE
                )
            )

        except Exception:

            self.modelo = None

    # ---------------------------------------------------------
    # UTILITÁRIO
    # ---------------------------------------------------------

    @staticmethod
    def _normalizar_resultado(
        resultado: Any
    ) -> str:

        if resultado is None:
            return ""

        if isinstance(
            resultado,
            str
        ):
            return resultado[:2000]

        try:

            return json.dumps(
                resultado,
                ensure_ascii=False,
                default=str,
            )[:2000]

        except Exception:

            return str(
                resultado
            )[:2000]


_aprendizado = None


def obter_aprendizado() -> AprendizadoJarvis:

    global _aprendizado

    if _aprendizado is None:

        _aprendizado = (
            AprendizadoJarvis()
        )

    return _aprendizado
