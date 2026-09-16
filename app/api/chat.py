from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import requests

from JARVIS_BASE.memoria_classificador import classificar_memoria
from app.core.memoria_persistente import MemoriaPersistente
from app.core.pesquisa_web import (
    deve_pesquisar,
    montar_contexto_web,
    pesquisar_web,
)

router = APIRouter(
    prefix="/api",
    tags=["JARVIS"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


def obter_url_router():
    port = os.getenv(
        "PORT",
        "8000",
    )

    return (
        f"http://127.0.0.1:{port}"
        "/ia-router/v1/chat/completions"
    )


def salvar_memoria_se_aplicavel(
    mensagem: str,
) -> None:
    try:
        classificacao = classificar_memoria(
            mensagem
        )

        if not classificacao.get(
            "permanente",
            False,
        ):
            return

        conteudo = str(
            classificacao.get(
                "conteudo",
                mensagem,
            )
        ).strip()

        if not conteudo:
            return

        prefixos = (
            "lembre que ",
            "lembra que ",
            "guarde que ",
            "memorize que ",
            "salve que ",
            "anote que ",
            "registre que ",
            "tenha em mente que ",
            "nao esqueca que ",
            "não esqueça que ",
        )

        normalizado = conteudo.lower()

        for prefixo in prefixos:
            if normalizado.startswith(prefixo):
                conteudo = (
                    conteudo[
                        len(prefixo):
                    ].strip()
                )
                break

        if not conteudo:
            return

        memoria = MemoriaPersistente()

        memoria.salvar_memoria(
            conteudo=conteudo,
            tipo=str(
                classificacao.get(
                    "tipo",
                    "OUTRO",
                )
            ).strip() or "OUTRO",
            importancia=int(
                classificacao.get(
                    "importancia",
                    5,
                )
            ),
            duracao="PERMANENTE",
        )

    except Exception:
        return


def recuperar_memoria(
    mensagem: str,
) -> str:
    try:
        memoria = MemoriaPersistente()

        resultados = memoria.buscar_memorias(
            mensagem,
            limite=8,
        )

        if not resultados:
            return ""

        partes = [
            "CONTEXTO DE MEMÓRIA DO J.A.R.V.I.S.",
            "Use somente quando for relevante.",
            "",
        ]

        for item in resultados:
            tipo = str(
                item.get(
                    "tipo",
                    "MEMORIA",
                )
            ).strip()

            conteudo = str(
                item.get(
                    "conteudo",
                    "",
                )
            ).strip()

            if conteudo:
                partes.append(
                    f"[{tipo}] {conteudo}"
                )

        return "\n".join(
            partes
        )

    except Exception:
        return ""


@router.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(
    request: ChatRequest,
):
    mensagem = request.message.strip()

    if not mensagem:
        raise HTTPException(
            status_code=400,
            detail="Mensagem vazia.",
        )

    salvar_memoria_se_aplicavel(
        mensagem
    )

    mensagens = []

    contexto_memoria = (
        recuperar_memoria(mensagem)
    )

    if contexto_memoria:
        mensagens.append({
            "role": "system",
            "content": contexto_memoria,
        })

    contexto_web = ""

    if deve_pesquisar(mensagem):
        resultados_web = pesquisar_web(
            mensagem,
            limite=5,
        )

        contexto_web = montar_contexto_web(
            resultados_web
        )

        if contexto_web:
            mensagens.append({
                "role": "system",
                "content": contexto_web,
            })

    mensagens.append({
        "role": "user",
        "content": mensagem,
    })

    payload = {
        "messages": mensagens,
    }

    try:
        resposta = requests.post(
            obter_url_router(),
            json=payload,
            timeout=120,
        )

        if resposta.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=(
                    "IA Router retornou "
                    f"HTTP {resposta.status_code}."
                ),
            )

        dados = resposta.json()

        try:
            texto = dados[
                "choices"
            ][0][
                "message"
            ][
                "content"
            ]
        except (
            KeyError,
            IndexError,
            TypeError,
        ):
            texto = str(
                dados
            )

        return ChatResponse(
            response=texto
        )

    except requests.RequestException as erro:
        raise HTTPException(
            status_code=502,
            detail=(
                "Falha ao comunicar com "
                f"o IA Router: {erro}"
            ),
        )
