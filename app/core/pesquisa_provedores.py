"""
JARVIS CLOUD - Pesquisa Web via MCP

Ponte de compatibilidade entre pesquisa_web.py e o MCP web.
"""

from typing import Any, Dict, List

from app.core.mcp_web import pesquisar_mcp


def pesquisar_com_fallback(
    consulta: str = "",
    *args,
    **kwargs,
) -> List[Dict[str, Any]]:
    """
    Mantem compatibilidade com pesquisa_web.py.

    Aceita:
    - consulta="..."
    - consultas=["...", "..."]
    - query="..."

    Repassa os parametros compativeis para pesquisar_mcp().
    """

    # ---------------------------------------------------------
    # 1. Interface principal usada por pesquisa_web.py
    # ---------------------------------------------------------
    consultas = kwargs.get("consultas")

    if consultas:
        if isinstance(consultas, str):
            consulta = consultas.strip()

        elif isinstance(consultas, (list, tuple)):
            partes = []

            for item in consultas:
                if isinstance(item, str) and item.strip():
                    partes.append(item.strip())

            if partes:
                consulta = " OR ".join(partes)

    # ---------------------------------------------------------
    # 2. Interface direta
    # ---------------------------------------------------------
    if not consulta:
        consulta = kwargs.get("query", "")

    # ---------------------------------------------------------
    # 3. Compatibilidade com argumentos posicionais antigos
    # ---------------------------------------------------------
    if not consulta and args:
        for valor in args:
            if isinstance(valor, str) and valor.strip():
                consulta = valor.strip()
                break

    consulta = str(consulta or "").strip()

    if not consulta:
        return []

    # ---------------------------------------------------------
    # 4. Parametros compativeis com pesquisar_mcp()
    # ---------------------------------------------------------
    limite = kwargs.get("limite", 5)

    temporal = kwargs.get(
        "temporal",
        False,
    )

    verificar_atualidade = kwargs.get(
        "verificar_atualidade",
        None,
    )

    usar_firecrawl = kwargs.get(
        "usar_firecrawl",
        True,
    )

    # ---------------------------------------------------------
    # 5. Chamada correta do MCP
    # ---------------------------------------------------------
    return pesquisar_mcp(
        consultas=[consulta],
        limite=limite,
        temporal=temporal,
        verificar_atualidade=verificar_atualidade,
        usar_firecrawl=usar_firecrawl,
    )
