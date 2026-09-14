from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import requests

from JARVIS_BASE.memoria_local import MemoriaLocal
from JARVIS_BASE.memoria_classificador import classificar_memoria

router = APIRouter(prefix="/api", tags=["JARVIS"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


def obter_url_router():
    port = os.getenv("PORT", "8000")
    return f"http://127.0.0.1:{port}/ia-router/v1/chat/completions"


def recuperar_memoria(mensagem: str) -> str:
    try:
        memoria = MemoriaLocal()
        resultados = memoria.buscar_memorias(mensagem)

        if not resultados:
            return ""

        partes = []

        for item in resultados[:5]:
            tipo = str(
                item.get("tipo", "MEMORIA")
            ).strip()

            conteudo = str(
                item.get("conteudo", "")
            ).strip()

            if conteudo:
                partes.append(
                    f"[{tipo}] {conteudo}"
                )

        if not partes:
            return ""

        return (
            "CONTEXTO DE MEMÓRIA DO J.A.R.V.I.S.\n"
            "Use estas informações como memória previamente "
            "registrada quando forem relevantes para responder "
            "ao usuário.\n\n"
            + "\n".join(partes)
        )

    except Exception:
        return ""


def salvar_memoria_se_aplicavel(mensagem: str) -> None:
    try:
        classificacao = classificar_memoria(mensagem)

        if not classificacao.get("permanente", False):
            return

        conteudo = str(
            classificacao.get(
                "conteudo",
                mensagem
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

        conteudo_normalizado = conteudo.lower()

        for prefixo in prefixos:
            if conteudo_normalizado.startswith(prefixo):
                conteudo = conteudo[len(prefixo):].strip()
                break

        if not conteudo:
            return

        tipo = str(
            classificacao.get(
                "tipo",
                "OUTRO"
            )
        ).strip() or "OUTRO"

        try:
            importancia = int(
                classificacao.get(
                    "importancia",
                    5
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            importancia = 5

        memoria = MemoriaLocal()

        memoria.salvar_memoria(
            conteudo=conteudo,
            tipo=tipo,
            importancia=importancia,
            duracao="PERMANENTE",
        )

    except Exception:
        # Memória nunca pode impedir a conversa de funcionar.
        return


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    mensagem = request.message.strip()

    if not mensagem:
        raise HTTPException(
            status_code=400,
            detail="Mensagem vazia."
        )

    # Primeiro tenta promover a mensagem para memória permanente.
    salvar_memoria_se_aplicavel(mensagem)

    mensagens = []

    contexto_memoria = recuperar_memoria(
        mensagem
    )

    if contexto_memoria:
        mensagens.append({
            "role": "system",
            "content": contexto_memoria,
        })

    mensagens.append({
        "role": "user",
        "content": mensagem,
    })

    payload = {
        "messages": mensagens
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
            texto = dados["choices"][0]["message"]["content"]
        except (
            KeyError,
            IndexError,
            TypeError,
        ):
            texto = str(dados)

        return ChatResponse(
            response=texto
        )

    except requests.RequestException as erro:
        raise HTTPException(
            status_code=502,
            detail=(
                "Falha ao comunicar com o IA Router: "
                f"{erro}"
            ),
        )
