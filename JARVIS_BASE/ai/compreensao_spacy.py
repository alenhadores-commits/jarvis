from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import spacy


@dataclass
class AnaliseLinguistica:
    texto: str
    tokens: list[str] = field(default_factory=list)
    entidades: list[dict[str, str]] = field(default_factory=list)
    verbo_principal: str = ""
    sujeito: str = ""

    def para_dict(self) -> dict[str, Any]:
        return {
            "texto": self.texto,
            "tokens": self.tokens,
            "entidades": self.entidades,
            "verbo_principal": self.verbo_principal,
            "sujeito": self.sujeito,
        }


class CompreensorSpacy:
    """
    Camada linguística do JARVIS.

    spaCy organiza a entrada.
    Qwen continua responsável pelo raciocínio.
    """

    VERBOS = {
        "abra": "abrir",
        "abri": "abrir",
        "abrir": "abrir",
        "abre": "abrir",

        "feche": "fechar",
        "fechar": "fechar",
        "fecha": "fechar",
        "fechou": "fechar",

        "execute": "executar",
        "executar": "executar",
        "executa": "executar",

        "inicie": "iniciar",
        "iniciar": "iniciar",
        "inicia": "iniciar",

        "pare": "parar",
        "parar": "parar",

        "pesquise": "pesquisar",
        "pesquisar": "pesquisar",
        "pesquisa": "pesquisar",

        "procure": "procurar",
        "procurar": "procurar",
        "procura": "procurar",

        "mostre": "mostrar",
        "mostrar": "mostrar",
        "mostra": "mostrar",

        "diga": "dizer",
        "dizer": "dizer",

        "lembre": "lembrar",
        "lembrar": "lembrar",
    }

    def __init__(self) -> None:
        self.nlp = spacy.load("pt_core_news_sm")

    def analisar(self, texto: str) -> AnaliseLinguistica:

        texto = str(texto or "").strip()

        doc = self.nlp(texto)

        tokens = [
            token.text
            for token in doc
            if not token.is_space
        ]

        entidades = []

        for ent in doc.ents:

            texto_entidade = ent.text.strip()

            # JARVIS é o nome do assistente,
            # não uma entidade útil para o comando.
            if texto_entidade.lower() == "jarvis":
                continue

            tipo = ent.label_

            # Corrige programas que o modelo
            # costuma classificar como LOC.
            if texto_entidade.lower() in {
                "chrome",
                "google chrome",
                "edge",
                "microsoft edge",
                "firefox",
                "notepad",
                "bloco de notas",
                "vscode",
                "visual studio code",
                "whatsapp",
            }:
                tipo = "PROGRAMA"

            elif tipo in {
                "LOC",
                "GPE",
                "FAC",
            }:
                tipo = "LOCAL"

            entidades.append(
                {
                    "texto": texto_entidade,
                    "tipo": tipo,
                    "inicio": str(ent.start_char),
                    "fim": str(ent.end_char),
                }
            )

        verbo_principal = ""

        # Primeiro tenta encontrar um verbo conhecido
        # diretamente na forma usada pelo usuário.
        for token in doc:

            palavra = token.text.lower().strip()

            if palavra in self.VERBOS:
                verbo_principal = self.VERBOS[palavra]
                break

        # Se não encontrou, usa o lema fornecido pelo spaCy.
        if not verbo_principal:

            for token in doc:

                if token.pos_ in {"VERB", "AUX"}:

                    verbo_principal = (
                        token.lemma_.lower().strip()
                    )

                    break

        sujeito = ""

        for token in doc:

            if token.dep_ in {
                "nsubj",
                "nsubj:pass",
            }:

                sujeito = token.text
                break

        return AnaliseLinguistica(
            texto=texto,
            tokens=tokens,
            entidades=entidades,
            verbo_principal=verbo_principal,
            sujeito=sujeito,
        )


_compreensor = None


def obter_compreensor() -> CompreensorSpacy:

    global _compreensor

    if _compreensor is None:
        _compreensor = CompreensorSpacy()

    return _compreensor


def analisar_texto(
    texto: str,
) -> dict[str, Any]:

    return (
        obter_compreensor()
        .analisar(texto)
        .para_dict()
    )
