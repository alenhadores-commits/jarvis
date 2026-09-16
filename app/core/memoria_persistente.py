import json
import os
from pathlib import Path
from typing import Any

import psycopg


class MemoriaPersistente:
    """
    Memoria do JARVIS Cloud.

    Com DATABASE_URL:
        PostgreSQL persistente.

    Sem DATABASE_URL:
        fallback para MemoriaLocal.
    """

    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "").strip()
        self.seed_paths = [
            Path("/etc/secrets/memorias_permanentes.json"),
            Path(__file__).resolve().parents[2]
            / "JARVIS_BASE"
            / "memoria"
            / "memorias_permanentes.json",
        ]

    def disponivel(self) -> bool:
        return bool(self.database_url)

    def _conectar(self):
        if not self.database_url:
            return None

        return psycopg.connect(
            self.database_url,
            autocommit=True,
            connect_timeout=10,
        )

    def _garantir_tabela(self):
        with self._conectar() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS jarvis_memorias (
                        id TEXT PRIMARY KEY,
                        tipo TEXT NOT NULL,
                        duracao TEXT NOT NULL,
                        conteudo TEXT NOT NULL,
                        importancia INTEGER NOT NULL DEFAULT 5,
                        criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )

                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_jarvis_memorias_tipo
                    ON jarvis_memorias(tipo)
                    """
                )

                cur.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_jarvis_memorias_atualizado
                    ON jarvis_memorias(atualizado_em DESC)
                    """
                )

    def _carregar_seed(self) -> list[dict[str, Any]]:
        for caminho in self.seed_paths:
            try:
                if not caminho.exists():
                    continue

                dados = json.loads(
                    caminho.read_text(
                        encoding="utf-8-sig"
                    )
                )

                memorias = dados.get("memorias", [])

                if isinstance(memorias, list):
                    return [
                        item
                        for item in memorias
                        if isinstance(item, dict)
                    ]

            except Exception:
                continue

        return []

    def _importar_seed_se_necessario(self):
        with self._conectar() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM jarvis_memorias"
                )

                total = int(
                    cur.fetchone()[0]
                )

                if total > 0:
                    return

        memorias = self._carregar_seed()

        if not memorias:
            return

        with self._conectar() as conn:
            with conn.cursor() as cur:
                for memoria in memorias:
                    cur.execute(
                        """
                        INSERT INTO jarvis_memorias (
                            id,
                            tipo,
                            duracao,
                            conteudo,
                            importancia,
                            criado_em,
                            atualizado_em
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s
                        )
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (
                            str(
                                memoria.get(
                                    "id",
                                    ""
                                )
                            ),
                            str(
                                memoria.get(
                                    "tipo",
                                    "OUTRO"
                                )
                            ),
                            str(
                                memoria.get(
                                    "duracao",
                                    "PERMANENTE"
                                )
                            ),
                            str(
                                memoria.get(
                                    "conteudo",
                                    ""
                                )
                            ),
                            int(
                                memoria.get(
                                    "importancia",
                                    5
                                )
                            ),
                            memoria.get("criado_em"),
                            memoria.get("atualizado_em"),
                        ),
                    )

    def preparar(self):
        if not self.disponivel():
            return

        self._garantir_tabela()
        self._importar_seed_se_necessario()

    def salvar_memoria(
        self,
        conteudo: str,
        tipo: str = "OUTRO",
        importancia: int = 5,
        duracao: str = "PERMANENTE",
    ) -> dict[str, Any]:
        conteudo = str(
            conteudo or ""
        ).strip()

        if not conteudo:
            return {}

        if not self.disponivel():
            from JARVIS_BASE.memoria_local import MemoriaLocal
            return MemoriaLocal().salvar_memoria(
                conteudo=conteudo,
                tipo=tipo,
                importancia=importancia,
                duracao=duracao,
            )

        self.preparar()

        importancia = max(
            0,
            min(
                10,
                int(importancia),
            ),
        )

        with self._conectar() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        criado_em
                    FROM jarvis_memorias
                    WHERE LOWER(conteudo) = LOWER(%s)
                    LIMIT 1
                    """,
                    (conteudo,),
                )

                existente = cur.fetchone()

                if existente:
                    memoria_id = str(
                        existente[0]
                    )

                    cur.execute(
                        """
                        UPDATE jarvis_memorias
                        SET
                            tipo = %s,
                            duracao = %s,
                            importancia = %s,
                            atualizado_em = CURRENT_TIMESTAMP
                        WHERE id = %s
                        """,
                        (
                            str(tipo or "OUTRO"),
                            str(
                                duracao
                                or "PERMANENTE"
                            ),
                            importancia,
                            memoria_id,
                        ),
                    )

                else:
                    import uuid

                    memoria_id = str(
                        uuid.uuid4()
                    )

                    cur.execute(
                        """
                        INSERT INTO jarvis_memorias (
                            id,
                            tipo,
                            duracao,
                            conteudo,
                            importancia
                        )
                        VALUES (
                            %s, %s, %s, %s, %s
                        )
                        """,
                        (
                            memoria_id,
                            str(tipo or "OUTRO"),
                            str(
                                duracao
                                or "PERMANENTE"
                            ),
                            conteudo,
                            importancia,
                        ),
                    )

        return {
            "id": memoria_id,
            "tipo": str(tipo or "OUTRO"),
            "duracao": str(
                duracao or "PERMANENTE"
            ),
            "conteudo": conteudo,
            "importancia": importancia,
        }

    def buscar_memorias(
        self,
        consulta: str,
        limite: int = 10,
    ) -> list[dict[str, Any]]:
        consulta = str(
            consulta or ""
        ).strip()

        if not consulta:
            return []

        if not self.disponivel():
            from JARVIS_BASE.memoria_local import MemoriaLocal
            return MemoriaLocal().buscar_memorias(
                consulta
            )[:limite]

        self.preparar()

        palavras = [
            p.lower()
            for p in consulta.split()
            if len(p) >= 3
        ]

        if not palavras:
            return []

        resultados = []

        with self._conectar() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        tipo,
                        duracao,
                        conteudo,
                        importancia,
                        criado_em,
                        atualizado_em
                    FROM jarvis_memorias
                    ORDER BY atualizado_em DESC
                    """
                )

                for row in cur.fetchall():
                    texto = (
                        f"{row[1]} {row[3]}"
                    ).lower()

                    pontos = sum(
                        1
                        for palavra in palavras
                        if palavra in texto
                    )

                    if pontos <= 0:
                        continue

                    resultados.append({
                        "id": row[0],
                        "tipo": row[1],
                        "duracao": row[2],
                        "conteudo": row[3],
                        "importancia": row[4],
                        "criado_em": str(row[5]),
                        "atualizado_em": str(row[6]),
                        "_relevancia": pontos,
                    })

        resultados.sort(
            key=lambda item: (
                item.get("_relevancia", 0),
                item.get("atualizado_em", ""),
                item.get("importancia", 0),
            ),
            reverse=True,
        )

        for item in resultados:
            item.pop(
                "_relevancia",
                None,
            )

        return resultados[:limite]
