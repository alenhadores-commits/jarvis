from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import requests


router = APIRouter(prefix="/api", tags=["JARVIS"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


def obter_url_router():
    port = os.getenv("PORT", "8000")
    return f"http://127.0.0.1:{port}/ia-router/v1/chat/completions"


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    mensagem = request.message.strip()

    if not mensagem:
        raise HTTPException(
            status_code=400,
            detail="Mensagem vazia."
        )

    payload = {
        "messages": [
            {
                "role": "user",
                "content": mensagem
            }
        ]
    }

    try:
        resposta = requests.post(
            obter_url_router(),
            json=payload,
            timeout=120
        )

        if resposta.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"IA Router retornou HTTP {resposta.status_code}."
            )

        dados = resposta.json()

        try:
            texto = dados["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            texto = str(dados)

        return ChatResponse(response=texto)

    except requests.RequestException as erro:
        raise HTTPException(
            status_code=502,
            detail=f"Falha ao comunicar com o IA Router: {erro}"
        )
