# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import sys

from sentence_transformers import CrossEncoder


MODEL_NAME = (
    "unicamp-dl/mMiniLM-L6-v2-en-pt-msmarco-v2"
)


os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"


def main() -> None:

    print(
        "JARVIS RERANKER WORKER: carregando "
        f"{MODEL_NAME}...",
        file=sys.stderr,
        flush=True,
    )

    model = CrossEncoder(
        MODEL_NAME,
        device="cpu",
        max_length=384,
    )

    print(
        "JARVIS RERANKER WORKER: modelo carregado.",
        file=sys.stderr,
        flush=True,
    )

    for linha in sys.stdin:

        linha = linha.strip()

        if not linha:
            continue

        try:

            pedido = json.loads(
                linha
            )

            pares = pedido.get(
                "pares",
                []
            )

            scores = model.predict(
                pares,
                batch_size=4,
                show_progress_bar=False,
                convert_to_numpy=True,
            )

            sys.stdout.write(
                json.dumps(
                    {
                        "ok": True,
                        "scores": [
                            float(score)
                            for score in scores
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

            sys.stdout.flush()

        except Exception as erro:

            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "erro": str(erro),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )

            sys.stdout.flush()


if __name__ == "__main__":
    main()
