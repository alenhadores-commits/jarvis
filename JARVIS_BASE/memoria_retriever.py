# -*- coding: utf-8 -*-

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any

from memoria_chroma import MemoriaChroma


class MemoriaRetriever:

    LIMITE_CANDIDATOS = 20
    LIMITE_FINAL = 5

    PESO_SEMANTICO = 0.65
    PESO_CONCEITO = 0.20
    PESO_TIPO = 0.10
    PESO_IMPORTANCIA = 0.05

    MAPA_TIPO = {

        "NOME": {
            "pergunta": [
                "qual e meu nome",
                "qual é meu nome",
                "como eu me chamo",
                "quem sou eu",
            ],
            "marcadores": [
                "nome",
                "me chamo",
            ],
        },

        "TRABALHO": {
            "pergunta": [
                "qual e minha profissao",
                "qual é minha profissão",
                "com o que eu trabalho",
                "onde eu trabalho",
                "qual minha ocupacao",
                "qual minha ocupação",
            ],
            "marcadores": [
                "profissao",
                "profissão",
                "trabalho",
                "dentista",
                "odontologia",
                "medico",
                "médico",
                "engenheiro",
                "advogado",
                "professor",
                "enfermeiro",
            ],
        },

        "COMIDA": {
            "pergunta": [
                "qual e minha comida favorita",
                "qual é minha comida favorita",
                "o que eu gosto de comer",
                "qual comida eu gosto",
            ],
            "marcadores": [
                "comida",
                "pizza",
                "hamburguer",
                "hambúrguer",
                "carne",
                "comer",
            ],
        },

        "ANIMAL": {
            "pergunta": [
                "qual e meu animal favorito",
                "qual é meu animal favorito",
                "qual animal eu gosto",
                "qual e meu pet favorito",
            ],
            "marcadores": [
                "animal",
                "cachorro",
                "cao",
                "cão",
                "gato",
                "pet",
            ],
        },

        "ESPORTE": {
            "pergunta": [
                "qual e meu time",
                "qual ? meu time",
                "para qual time eu torco",
                "para qual time eu tor?o",
                "qual time eu torco",
                "qual time eu tor?o",
                "qual e meu time de coracao",
                "qual ? meu time de cora??o",
                "qual meu time",
                "qual e o meu time",
                "qual ? o meu time",
            ],
            "marcadores": [
                "time",
                "futebol",
                "torco",
                "tor?o",
                "palmeiras",
                "flamengo",
                "corinthians",
                "vasco",
                "santos",
                "sao paulo",
                "s?o paulo",
                "botafogo",
                "gremio",
                "gr?mio",
                "internacional",
            ],
        },

        "FAMILIA": {
            "pergunta": [
                "qual e o nome da minha esposa",
                "qual ? o nome da minha esposa",
                "qual o nome da minha esposa",
                "como se chama minha esposa",
                "quem e minha esposa",
                "quem ? minha esposa",
                "qual e o nome do meu marido",
                "qual o nome do meu marido",
                "qual e o nome da minha namorada",
                "qual o nome da minha namorada",
                "qual e o nome do meu namorado",
                "qual o nome do meu namorado",
                "qual e o nome do meu filho",
                "qual o nome do meu filho",
                "qual e o nome da minha filha",
                "qual o nome da minha filha",
            ],
            "marcadores": [
                "esposa",
                "marido",
                "namorada",
                "namorado",
                "filho",
                "filha",
                "familia",
                "fam?lia",
            ],
        },

        "PROJETO": {
            "pergunta": [
                "qual e meu principal projeto",
                "qual é meu principal projeto",
                "qual meu projeto principal",
                "em que projeto estou trabalhando",
            ],
            "marcadores": [
                "projeto",
                "sistema",
                "programa",
            ],
        },

        "PREFERENCIA": {
            "pergunta": [
                "do que eu gosto",
                "o que eu gosto",
                "qual e minha preferencia",
                "qual é minha preferência",
            ],
            "marcadores": [
                "gosto",
                "prefiro",
                "adoro",
                "amo",
            ],
        },
    }

    INDICADORES_NEGATIVOS = {
        "nao",
        "não",
        "nunca",
        "detesto",
        "odeio",
    }

    def __init__(
        self,
        memoria: MemoriaChroma | None = None,
    ) -> None:

        self.memoria = (
            memoria
            if memoria is not None
            else MemoriaChroma()
        )

        # Garante que o ?ndice Chroma esteja atualizado
        # com o JSON antes de qualquer busca.
        try:
            self.memoria.sincronizar_completa()
        except Exception:
            pass

    @staticmethod
    def _normalizar(
        texto: str,
    ) -> str:

        texto = str(
            texto or ""
        ).lower()

        texto = unicodedata.normalize(
            "NFKD",
            texto
        )

        texto = "".join(
            caractere
            for caractere in texto
            if not unicodedata.combining(
                caractere
            )
        )

        texto = re.sub(
            r"[^a-z0-9\s]",
            " ",
            texto
        )

        texto = re.sub(
            r"\s+",
            " ",
            texto
        )

        return texto.strip()

    @classmethod
    def _tokens(
        cls,
        texto: str,
    ) -> set[str]:

        stopwords = {
            "qual",
            "meu",
            "minha",
            "meus",
            "minhas",
            "eu",
            "sou",
            "uma",
            "um",
            "o",
            "a",
            "os",
            "as",
            "que",
            "e",
            "é",
            "de",
            "do",
            "da",
            "dos",
            "das",
            "com",
            "para",
            "em",
            "no",
            "na",
            "principal",
        }

        return {
            token
            for token in cls._normalizar(
                texto
            ).split()
            if len(token) >= 3
            and token not in stopwords
        }

    @classmethod
    def inferir_tipo(
        cls,
        consulta: str,
    ) -> str | None:

        texto = cls._normalizar(
            consulta
        )

        melhores = []

        for tipo, configuracao in (
            cls.MAPA_TIPO.items()
        ):

            pontos = 0

            for frase in configuracao[
                "pergunta"
            ]:

                frase_norm = cls._normalizar(
                    frase
                )

                if frase_norm in texto:
                    pontos += (
                        5
                        +
                        len(
                            frase_norm.split()
                        )
                    )

            for marcador in configuracao[
                "marcadores"
            ]:

                marcador_norm = cls._normalizar(
                    marcador
                )

                if (
                    marcador_norm
                    and marcador_norm in texto
                ):

                    pontos += 1

            if pontos:

                melhores.append(
                    (
                        pontos,
                        tipo,
                    )
                )

        if not melhores:
            return None

        # Em consultas sobre relacionamentos, FAMILIA
        # deve prevalecer sobre conceitos gen?ricos como NOME.
        palavras_familia = {
            "esposa",
            "marido",
            "namorada",
            "namorado",
            "filho",
            "filha",
            "familia",
            "fam?lia",
        }

        tokens_consulta = set(
            cls._normalizar(
                consulta
            ).split()
        )

        if tokens_consulta & palavras_familia:

            for pontos, tipo in melhores:

                if tipo == "FAMILIA":
                    return tipo

        melhores.sort(
            key=lambda item: item[0],
            reverse=True
        )

        return melhores[0][1]

    @classmethod
    def _score_conceito(
        cls,
        consulta: str,
        candidato: dict[str, Any],
    ) -> float:

        tipo = cls.inferir_tipo(
            consulta
        )

        if not tipo:
            return 0.0

        memoria = cls._normalizar(
            str(
                candidato.get(
                    "conteudo",
                    ""
                )
            )
        )

        configuracao = (
            cls.MAPA_TIPO.get(
                tipo,
                {}
            )
        )

        marcadores = [
            cls._normalizar(
                marcador
            )
            for marcador in configuracao.get(
                "marcadores",
                []
            )
        ]

        encontrados = [
            marcador
            for marcador in marcadores
            if marcador
            and marcador in memoria
        ]

        if not encontrados:
            return 0.0

        proporcao = (
            len(encontrados)
            /
            max(
                1,
                len(marcadores)
            )
        )

        return max(
            0.0,
            min(
                1.0,
                0.5 + proporcao * 0.5
            )
        )

    @classmethod
    def _score_tipo(
        cls,
        consulta: str,
        candidato: dict[str, Any],
    ) -> float:

        tipo_consulta = (
            cls.inferir_tipo(
                consulta
            )
        )

        tipo_memoria = str(
            candidato.get(
                "tipo",
                "OUTRO"
            )
        ).strip().upper()

        if not tipo_consulta:
            return 0.0

        if (
            tipo_memoria
            == tipo_consulta
        ):
            return 1.0

        return 0.0

    @staticmethod
    def _score_importancia(
        candidato: dict[str, Any],
    ) -> float:

        try:
            valor = int(
                candidato.get(
                    "importancia",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):
            valor = 0

        return max(
            0.0,
            min(
                1.0,
                valor / 10.0
            )
        )

    @staticmethod
    def _score_recencia(
        candidato: dict[str, Any],
    ) -> float:

        valor = str(
            candidato.get(
                "atualizado_em",
                ""
            )
        ).strip()

        if not valor:
            return 0.0

        try:

            data = datetime.fromisoformat(
                valor.replace(
                    "Z",
                    "+00:00"
                )
            )

            agora = datetime.now(
                data.tzinfo
            )

            dias = (agora - data).total_seconds() / 86400.0

            return 1.0 / (
                1.0
                +
                max(
                    0.0,
                    dias
                ) / 30.0
            )

        except (
            ValueError,
            TypeError
        ):

            return 0.0

    def buscar(
        self,
        consulta: str,
        limite: int | None = None,
        tipo: str | None = None,
        importancia_minima: int | None = None,
    ) -> list[dict[str, Any]]:

        candidatos = self.memoria.buscar(
            consulta,
            limite=(
                limite
                if limite is not None
                else self.LIMITE_CANDIDATOS
            ),
            tipo=tipo,
            importancia_minima=(
                importancia_minima
            ),
        )

        if not candidatos:
            return []

        tipo_consulta = (
            self.inferir_tipo(
                consulta
            )
        )

        # Quando conseguimos determinar
        # uma intenção forte, eliminamos tipos
        # incompatíveis antes do ranking final.
        if tipo_consulta:

            filtrados = []

            for candidato in candidatos:

                score_tipo = (
                    self._score_tipo(
                        consulta,
                        candidato
                    )
                )

                if score_tipo > 0:
                    filtrados.append(
                        candidato
                    )

            if filtrados:
                candidatos = filtrados

        resultado = []

        for candidato in candidatos:

            semantico = max(
                0.0,
                min(
                    1.0,
                    float(
                        candidato.get(
                            "similaridade",
                            0.0
                        )
                    )
                )
            )

            conceito = (
                self._score_conceito(
                    consulta,
                    candidato
                )
            )

            tipo_score = (
                self._score_tipo(
                    consulta,
                    candidato
                )
            )

            importancia = (
                self._score_importancia(
                    candidato
                )
            )

            recencia = (
                self._score_recencia(
                    candidato
                )
            )

            score_final = (
                semantico
                * self.PESO_SEMANTICO
                +
                conceito
                * self.PESO_CONCEITO
                +
                tipo_score
                * self.PESO_TIPO
                +
                importancia
                * self.PESO_IMPORTANCIA
                +
                recencia
                * 0.02
            )

            item = dict(
                candidato
            )

            item[
                "score_final"
            ] = score_final

            item[
                "score_conceito"
            ] = conceito

            item[
                "score_tipo"
            ] = tipo_score

            item[
                "score_importancia"
            ] = importancia

            item[
                "score_recencia"
            ] = recencia

            resultado.append(
                item
            )

        resultado.sort(
            key=lambda item:
                item.get(
                    "score_final",
                    0.0
                ),
            reverse=True
        )

        finais = []
        vistos = set()

        for item in resultado:

            chave = self._normalizar(
                str(
                    item.get(
                        "conteudo",
                        ""
                    )
                )
            )

            if (
                not chave
                or chave in vistos
            ):
                continue

            vistos.add(
                chave
            )

            finais.append(
                item
            )

            if len(finais) >= self.LIMITE_FINAL:
                break

        return finais

    def contexto(
        self,
        consulta: str,
    ) -> str:

        resultados = self.buscar(
            consulta
        )

        return "\n".join(
            f"[{item.get('tipo', 'OUTRO')}] "
            f"{item.get('conteudo', '')}"
            for item in resultados
        )


if __name__ == "__main__":

    retriever = MemoriaRetriever()

    sincronizacao = (
        retriever.memoria.sincronizar_completa()
    )

    print(
        json.dumps(
            sincronizacao,
            ensure_ascii=False,
            indent=2
        )
    )

