# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import uuid
from pathlib import Path
from datetime import datetime


BASE = Path(__file__).resolve().parent
ARQUIVO = (
    BASE
    / "memoria"
    / "memorias_permanentes.json"
)


def agora():
    return datetime.now().isoformat(
        timespec="seconds"
    )


def novo_id():
    return str(uuid.uuid4())


def nova_memoria(
    conteudo,
    tipo,
    importancia,
    criado_em=None,
    atualizado_em=None,
):
    momento = agora()

    return {
        "id": novo_id(),
        "tipo": tipo,
        "duracao": "PERMANENTE",
        "conteudo": conteudo,
        "importancia": importancia,
        "criado_em": criado_em or momento,
        "atualizado_em": atualizado_em or momento,
    }


def main():

    dados = json.loads(
        ARQUIVO.read_text(
            encoding="utf-8-sig"
        )
    )

    memorias = dados.get(
        "memorias",
        []
    )

    novas = []

    alteradas = 0
    removidas = 0
    criadas = 0

    for memoria in memorias:

        if not isinstance(
            memoria,
            dict
        ):
            continue

        conteudo = str(
            memoria.get(
                "conteudo",
                ""
            )
        ).strip()

        normalizado = (
            conteudo
            .lower()
            .strip()
        )

        criado_em = memoria.get(
            "criado_em"
        )

        atualizado_em = memoria.get(
            "atualizado_em"
        )

        # ======================================================
        # NOME + PROFISSÃO MISTURADOS
        # ======================================================

        if (
            normalizado
            == "meu nome é alex, sou dentista."
            or
            normalizado
            == "meu nome e alex, sou dentista."
        ):

            novas.append(
                nova_memoria(
                    "Meu nome é Alex.",
                    "NOME",
                    8,
                    criado_em,
                    atualizado_em,
                )
            )

            novas.append(
                nova_memoria(
                    "Sou dentista.",
                    "TRABALHO",
                    8,
                    criado_em,
                    atualizado_em,
                )
            )

            removidas += 1
            criadas += 2
            alteradas += 1

            continue

        # ======================================================
        # ANIMAL FAVORITO COM PREFIXO JARVIS
        # ======================================================

        if (
            "meu animal favorito é cachorro"
            in normalizado
            or
            "meu animal favorito e cachorro"
            in normalizado
        ):

            memoria["conteudo"] = (
                "Meu animal favorito é cachorro."
            )

            memoria["tipo"] = (
                "PREFERENCIA"
            )

            memoria["duracao"] = (
                "PERMANENTE"
            )

            memoria["atualizado_em"] = (
                agora()
            )

            novas.append(
                memoria
            )

            alteradas += 1

            continue

        # ======================================================
        # PROJETO JARVIS
        # ======================================================

        if (
            "estamos construindo um assistente pessoal chamado jarvis"
            in normalizado
        ):

            memoria["conteudo"] = (
                "Meu principal projeto é o JARVIS."
            )

            memoria["tipo"] = (
                "PROJETO"
            )

            memoria["duracao"] = (
                "PERMANENTE"
            )

            memoria["importancia"] = max(
                8,
                int(
                    memoria.get(
                        "importancia",
                        0
                    )
                )
            )

            memoria["atualizado_em"] = (
                agora()
            )

            novas.append(
                memoria
            )

            alteradas += 1

            continue

        # ======================================================
        # PROFISSÃO ENCONTRADA EM OUTROS REGISTROS
        # ======================================================

        if (
            "sou dentista"
            in normalizado
            and
            "nome"
            not in normalizado
        ):

            memoria["tipo"] = (
                "TRABALHO"
            )

            memoria["atualizado_em"] = (
                agora()
            )

            novas.append(
                memoria
            )

            alteradas += 1

            continue

        novas.append(
            memoria
        )

    dados["memorias"] = novas

    ARQUIVO.write_text(
        json.dumps(
            dados,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("=" * 60)
    print(" MIGRAÇÃO DA MEMÓRIA JARVIS")
    print("=" * 60)
    print()
    print("memórias originais:", len(memorias))
    print("memórias finais:", len(novas))
    print("registros alterados:", alteradas)
    print("registros removidos:", removidas)
    print("registros criados:", criadas)
    print()
    print("BACKUP:", "OK")
    print("ARQUIVO:", ARQUIVO)


if __name__ == "__main__":
    main()
