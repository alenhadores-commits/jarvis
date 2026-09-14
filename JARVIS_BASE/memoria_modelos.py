# -*- coding: utf-8 -*-

from __future__ import annotations

from functools import lru_cache
import os
from typing import Any


MODELO_EMBEDDING = (
    "intfloat/multilingual-e5-base"
)

MODELO_RERANKER = (
    "unicamp-dl/mMiniLM-L6-v2-en-pt-msmarco-v2"
)


def _dispositivo(nome: str) -> str:

    valor = str(
        os.getenv(nome, "cpu")
    ).strip().lower()

    if valor in {
        "cuda",
        "cuda:0",
        "cpu",
    }:
        return valor

    return "cpu"


DEVICE_EMBEDDING = _dispositivo(
    "JARVIS_EMBEDDING_DEVICE"
)

DEVICE_RERANKER = "cpu"


@lru_cache(maxsize=1)
def carregar_embedding() -> Any:

    # Importacao sob demanda.
    # Evita carregar Torch/Transformers durante
    # a inicializacao normal do JARVIS.
    from sentence_transformers import SentenceTransformer

    print(
        "JARVIS: carregando embedding local "
        f"{MODELO_EMBEDDING}..."
    )

    return SentenceTransformer(
        MODELO_EMBEDDING,
        device=DEVICE_EMBEDDING,
    )


@lru_cache(maxsize=1)
def carregar_reranker() -> Any:

    # Importacao sob demanda.
    from sentence_transformers import CrossEncoder

    print(
        "JARVIS: carregando reranker local "
        f"{MODELO_RERANKER}..."
    )

    return CrossEncoder(
        MODELO_RERANKER,
        device=DEVICE_RERANKER,
        max_length=384,
    )


