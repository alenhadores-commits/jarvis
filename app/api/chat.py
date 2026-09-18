from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.chat_orchestrator import (
    ChatOrchestrator,
    IARouterError,
    InformacaoDesatualizada,
)

router = APIRouter(
    prefix="/api",
    tags=["JARVIS"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


orchestrator = ChatOrchestrator()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    mensagem = request.message.strip()

    if not mensagem:
        raise HTTPException(
            status_code=400,
            detail="Mensagem vazia.",
        )

    try:
        texto = orchestrator.processar(mensagem)
        return ChatResponse(response=texto)

    except InformacaoDesatualizada as erro:
        return ChatResponse(response=str(erro))

    except IARouterError as erro:
        raise HTTPException(
            status_code=502,
            detail=str(erro),
        ) from erro
