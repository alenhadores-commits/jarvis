from fastapi import APIRouter
import requests
import os


router = APIRouter(prefix="/api", tags=["Status"])


def obter_url_status_router():
    port = os.getenv("PORT", "8000")
    return f"http://127.0.0.1:{port}/ia-router/status"


@router.get("/status")
def status():

    resultado = {
        "cloud": "online",
        "ia_router": "offline",
    }

    try:
        resposta = requests.get(
            obter_url_status_router(),
            timeout=10
        )

        if resposta.ok:
            resultado["ia_router"] = "online"
            resultado["ia_router_data"] = resposta.json()
        else:
            resultado["ia_router_http"] = resposta.status_code

    except requests.RequestException as erro:
        resultado["ia_router_error"] = str(erro)

    return resultado
