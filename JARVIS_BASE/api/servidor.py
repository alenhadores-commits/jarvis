from datetime import datetime
import asyncio

from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
)

from .runtime import runtime


app = FastAPI(
    title="JARVIS API",
    description="Interface de acesso ao núcleo operacional do JARVIS",
    version="1.0.0",
)


clientes = set()


async def publicar_evento(
    evento: str,
    dados=None,
):
    mensagem = {
        "evento": evento,
        "dados": dados,
        "timestamp": datetime.now().isoformat(),
    }

    desconectados = set()

    for cliente in list(clientes):

        try:
            await cliente.send_json(
                mensagem
            )

        except Exception:
            desconectados.add(cliente)

    for cliente in desconectados:
        clientes.discard(cliente)


@app.get("/status")
def status():

    return {
        "status": "online",
        "sistema": "JARVIS",
        "api": "online",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/memorias")
def memorias():

    try:

        if runtime.banco_chroma is None:
            return {
                "erro": "Chroma indisponível."
            }

        resultado = {}

        for nome in (
            "memorias",
            "procedimentos",
        ):

            try:

                colecao = (
                    runtime.banco_chroma.obter(
                        nome
                    )
                )

                resultado[nome] = (
                    colecao.count()
                )

            except Exception as erro:

                resultado[nome] = (
                    f"erro: {erro}"
                )

        return resultado

    except Exception as erro:

        return {
            "erro": str(erro)
        }


@app.get("/procedimentos")
def procedimentos():

    try:

        if runtime.banco_chroma is None:
            return {
                "erro": "Chroma indisponível."
            }

        colecao = (
            runtime.banco_chroma.obter(
                "procedimentos"
            )
        )

        dados = colecao.get(
            include=[
                "documents",
                "metadatas",
            ]
        )

        return {
            "total": len(
                dados.get(
                    "documents",
                    [],
                )
            ),
            "documentos": dados.get(
                "documents",
                [],
            ),
            "metadados": dados.get(
                "metadatas",
                [],
            ),
        }

    except Exception as erro:

        return {
            "erro": str(erro)
        }


@app.get("/habilidades")
def habilidades():

    try:

        habilidades = (
            runtime.gerenciador_habilidades.listar()
        )

        return {
            "total": len(habilidades),
            "habilidades": habilidades,
        }

    except Exception as erro:

        return {
            "erro": str(erro)
        }


@app.post("/comando")
async def comando(dados: dict):

    texto = str(
        dados.get(
            "comando",
            "",
        )
    ).strip()

    if not texto:

        return {
            "ok": False,
            "erro": "Comando vazio.",
        }

    await publicar_evento(
        "comando_recebido",
        {
            "comando": texto
        },
    )

    resultado = await asyncio.to_thread(
        runtime.processar,
        texto,
    )

    await publicar_evento(
        "triagem_concluida",
        resultado.get(
            "triagem"
        ),
    )

    if resultado.get("ok"):

        await publicar_evento(
            "resposta",
            {
                "comando": texto,
                "resposta": resultado.get(
                    "resposta",
                    "",
                ),
            },
        )

    else:

        await publicar_evento(
            "erro",
            {
                "comando": texto,
                "erro": resultado.get(
                    "erro",
                    "Erro desconhecido.",
                ),
            },
        )

    return resultado


@app.post("/memoria")
def memoria(dados: dict):

    return {
        "ok": False,
        "status": "endpoint ainda não implementado",
        "dados": dados,
    }


@app.post("/ensinar")
def ensinar(dados: dict):

    return {
        "ok": False,
        "status": "endpoint ainda não implementado",
        "dados": dados,
    }


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
):

    await websocket.accept()

    clientes.add(websocket)

    try:

        await websocket.send_json(
            {
                "evento": "sistema_online",
                "timestamp": datetime.now().isoformat(),
            }
        )

        while True:

            mensagem = (
                await websocket.receive_text()
            )

            await websocket.send_json(
                {
                    "evento": "mensagem_recebida",
                    "dados": mensagem,
                    "timestamp": datetime.now().isoformat(),
                }
            )

    except WebSocketDisconnect:

        clientes.discard(websocket)

    except Exception:

        clientes.discard(websocket)
