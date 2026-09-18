import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from IA_ROUTER.api_router import app as ia_router_app
from app.api.chat import router as chat_router
from app.api.status import router as status_router


BASE_DIR = Path(__file__).resolve().parent


app = FastAPI(
    title="JARVIS Cloud",
    version="1.0.0",
    description="Interface central do JARVIS Cloud.",
)


app.include_router(chat_router)
app.include_router(status_router)


app.mount("/ia-router", ia_router_app)


@app.get("/health")
def health():
    return {
        "status": "online",
        "service": "JARVIS Cloud",
        "ia_router": "online",
    }


@app.get("/", response_class=HTMLResponse)
def dashboard():
    arquivo = BASE_DIR / "paginas" / "dashboard.html"

    return arquivo.read_text(
        encoding="utf-8"
    )
