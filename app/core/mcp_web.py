from __future__ import annotations

import asyncio
import time
import json
import os
import subprocess
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILES = [
    BASE_DIR / ".env",
    BASE_DIR / "IA_ROUTER" / ".env",
]

PERPLEXITY_SEARCH_URL = "https://api.perplexity.ai/search"


def _carregar_env_local() -> None:
    """
    Carrega variáveis do .env sem sobrescrever variáveis
    que já existam no ambiente do processo.
    """
    for env_file in ENV_FILES:
        if not env_file.exists():
            continue

        try:
            for linha in env_file.read_text(encoding="utf-8").splitlines():
                linha = linha.strip()

                if not linha or linha.startswith("#") or "=" not in linha:
                    continue

                chave, valor = linha.split("=", 1)
                chave = chave.strip()
                valor = valor.strip()

                if (
                    len(valor) >= 2
                    and valor[0] == valor[-1]
                    and valor[0] in ("'", '"')
                ):
                    valor = valor[1:-1]

                if chave and valor and chave not in os.environ:
                    os.environ[chave] = valor
        except Exception:
            continue


_carregar_env_local()


def _perplexity_key() -> str:
    return os.getenv("PERPLEXITY_API_KEY", "").strip()


def _firecrawl_key() -> str:
    return os.getenv("FIRECRAWL_API_KEY", "").strip()


def _texto(valor: Any) -> str:
    if valor is None:
        return ""

    if isinstance(valor, str):
        return valor.strip()

    try:
        return json.dumps(valor, ensure_ascii=False)
    except Exception:
        return str(valor)


def _normalizar_perplexity(item: Dict[str, Any], consulta: str) -> Dict[str, Any]:
    return {
        "provider": "perplexity",
        "title": _texto(item.get("title")),
        "url": _texto(item.get("url")),
        "domain": _texto(item.get("domain")),
        "snippet": _texto(item.get("snippet")),
        "content": _texto(item.get("content") or item.get("snippet")),
        "source_date": _texto(item.get("date")),
        "published_at": _texto(item.get("date")),
        "last_updated": _texto(item.get("last_updated")),
        "score": item.get("score"),
        "query": consulta,
    }


def pesquisar_perplexity(
    consulta: str,
    limite: int = 5,
    temporal: bool = False,
    verificar_atualidade: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """
    Pesquisa diretamente pela Perplexity Search API.

    A API Search fornece resultados web estruturados.
    Não usa o Router API da Perplexity.
    """
    consulta = str(consulta or "").strip()

    if not consulta:
        return []

    api_key = _perplexity_key()

    if not api_key:
        print("JARVIS WEB: PERPLEXITY_API_KEY ausente.", flush=True)
        return []

    try:
        resposta = requests.post(
            PERPLEXITY_SEARCH_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "query": consulta,
            },
            timeout=30,
        )

        if resposta.status_code != 200:
            print(
                f"JARVIS WEB: Perplexity Search HTTP {resposta.status_code}",
                flush=True,
            )
            return []

        dados = resposta.json()
        resultados = dados.get("results", [])

        if not isinstance(resultados, list):
            return []

        normalizados = []

        for item in resultados[:limite]:
            if not isinstance(item, dict):
                continue

            resultado = _normalizar_perplexity(item, consulta)

            if resultado["url"] or resultado["title"] or resultado["content"]:
                normalizados.append(resultado)

        if normalizados:
            print(
                f"JARVIS WEB: Perplexity Search -> {len(normalizados)} resultados",
                flush=True,
            )

        return normalizados

    except requests.RequestException as exc:
        print(
            f"JARVIS WEB: erro Perplexity Search: {exc}",
            flush=True,
        )
        return []

    except Exception as exc:
        print(
            f"JARVIS WEB: erro inesperado Perplexity: {exc}",
            flush=True,
        )
        return []


class FirecrawlMCP:
    """
    Cliente MCP mínimo para o servidor oficial firecrawl-mcp.

    Mantém o transporte simples via stdio para evitar dependências
    adicionais no projeto principal.
    """

    def __init__(self) -> None:
        self.process: Optional[subprocess.Popen] = None
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def start(self) -> bool:
        if self.process is not None and self.process.poll() is None:
            return True

        if not _firecrawl_key():
            print("JARVIS WEB: FIRECRAWL_API_KEY ausente.", flush=True)
            return False

        try:
            env = os.environ.copy()
            env["FIRECRAWL_API_KEY"] = _firecrawl_key()

            npx_executavel = (
                shutil.which("npx.cmd")
                if sys.platform == "win32"
                else shutil.which("npx")
            )

            if not npx_executavel:
                print(
                    "JARVIS WEB: npx nao disponivel; "
                    "Firecrawl MCP sera ignorado.",
                    flush=True,
                )
                self.process = None
                return False

            self.process = subprocess.Popen(
                [
                    npx_executavel,
                    "-y",
                    "firecrawl-mcp",
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if sys.platform == "win32"
                    else 0
                ),
            )

            return self.process.poll() is None

        except Exception as exc:
            print(
                f"JARVIS WEB: falha iniciando Firecrawl MCP: {exc}",
                flush=True,
            )
            self.process = None
            return False

    def stop(self) -> None:
        if self.process is None:
            return

        try:
            if self.process.poll() is None:
                self.process.terminate()
                self.process.wait(timeout=5)
        except Exception:
            try:
                self.process.kill()
            except Exception:
                pass

        self.process = None

    def _send(self, payload: Dict[str, Any], timeout: float = 45.0) -> Dict[str, Any]:
        if not self.start():
            return {}

        assert self.process is not None
        assert self.process.stdin is not None
        assert self.process.stdout is not None

        try:
            mensagem = json.dumps(payload, ensure_ascii=False)
            self.process.stdin.write(mensagem + "\n")
            self.process.stdin.flush()

            inicio = time.monotonic()

            while True:
                if time.monotonic() - inicio > timeout:
                    raise TimeoutError("timeout aguardando resposta MCP")

                linha = self.process.stdout.readline()

                if not linha:
                    if self.process.poll() is not None:
                        raise RuntimeError("processo Firecrawl MCP encerrou")
                    continue

                linha = linha.strip()

                if not linha:
                    continue

                try:
                    resposta = json.loads(linha)
                except json.JSONDecodeError:
                    continue

                if resposta.get("id") == payload.get("id"):
                    return resposta

        except Exception as exc:
            print(
                f"JARVIS WEB: erro transporte Firecrawl MCP: {exc}",
                flush=True,
            )
            self.stop()
            return {}

    def initialize(self) -> bool:
        resposta = self._send(
            {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "jarvis-cloud",
                        "version": "1.0.0",
                    },
                },
            }
        )

        return bool(resposta.get("result"))

    def list_tools(self) -> List[Dict[str, Any]]:
        resposta = self._send(
            {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/list",
                "params": {},
            }
        )

        resultado = resposta.get("result", {})
        ferramentas = resultado.get("tools", [])

        return ferramentas if isinstance(ferramentas, list) else []

    def call_tool(
        self,
        nome: str,
        argumentos: Dict[str, Any],
    ) -> Dict[str, Any]:
        return self._send(
            {
                "jsonrpc": "2.0",
                "id": self._next_id(),
                "method": "tools/call",
                "params": {
                    "name": nome,
                    "arguments": argumentos,
                },
            }
        )


def _extrair_texto_mcp(conteudo: Any) -> str:
    if isinstance(conteudo, str):
        return conteudo

    if isinstance(conteudo, list):
        partes = []

        for item in conteudo:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    partes.append(_texto(item.get("text")))
                elif "text" in item:
                    partes.append(_texto(item.get("text")))
                else:
                    partes.append(_texto(item))
            else:
                partes.append(_texto(item))

        return "\n".join(p for p in partes if p)

    if isinstance(conteudo, dict):
        return _texto(conteudo)

    return ""


def _normalizar_firecrawl(
    dados: Any,
    consulta: str,
    limite: int,
) -> List[Dict[str, Any]]:
    """
    Normaliza as respostas do firecrawl_search para o formato interno
    usado pelo JARVIS.

    Formato esperado do MCP Firecrawl:
    {
        "success": true,
        "data": {
            "web": [
                {
                    "url": "...",
                    "title": "...",
                    "description": "...",
                    "position": 1
                }
            ]
        }
    }
    """
    resultados: Any = dados

    if isinstance(resultados, dict):
        data = resultados.get("data")

        if isinstance(data, dict):
            resultados = (
                data.get("web")
                or data.get("results")
                or data.get("items")
                or []
            )
        elif isinstance(data, list):
            resultados = data
        else:
            resultados = (
                resultados.get("web")
                or resultados.get("results")
                or resultados.get("items")
                or resultados
            )

    if isinstance(resultados, dict):
        resultados = [resultados]

    if not isinstance(resultados, list):
        return []

    saida: List[Dict[str, Any]] = []

    for item in resultados:
        if not isinstance(item, dict):
            continue

        title = (
            item.get("title")
            or item.get("name")
            or ""
        )

        url = (
            item.get("url")
            or item.get("link")
            or ""
        )

        snippet = (
            item.get("description")
            or item.get("snippet")
            or item.get("content")
            or ""
        )

        content = (
            item.get("content")
            or item.get("markdown")
            or snippet
            or ""
        )

        source_date = (
            item.get("date")
            or item.get("publishedDate")
            or item.get("published_at")
            or ""
        )

        last_updated = (
            item.get("last_updated")
            or item.get("lastUpdated")
            or ""
        )

        domain = ""

        if url:
            try:
                from urllib.parse import urlparse

                domain = urlparse(str(url)).netloc
            except Exception:
                domain = ""

        if not title and not url and not content:
            continue

        saida.append(
            {
                "provider": "firecrawl",
                "title": _texto(title),
                "url": _texto(url),
                "domain": _texto(domain),
                "snippet": _texto(snippet),
                "content": _texto(content),
                "source_date": _texto(source_date),
                "published_at": _texto(source_date),
                "last_updated": _texto(last_updated),
                "score": item.get("score"),
                "query": consulta,
            }
        )

        if len(saida) >= limite:
            break

    return saida

def pesquisar_firecrawl(
    consulta: str,
    limite: int = 5,
    temporal: bool = False,
    verificar_atualidade: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    consulta = str(consulta or "").strip()

    if not consulta:
        return []

    cliente = FirecrawlMCP()

    try:
        if not cliente.start():
            return []

        if not cliente.initialize():
            print("JARVIS WEB: Firecrawl MCP não inicializou.", flush=True)
            return []

        ferramentas = cliente.list_tools()

        nomes = {
            str(
                ferramenta.get("name")
            )
            for ferramenta in ferramentas
            if isinstance(ferramenta, dict)
        }

        if "firecrawl_search" not in nomes:
            print(
                "JARVIS WEB: ferramenta firecrawl_search não encontrada.",
                flush=True,
            )
            return []

        resposta = cliente.call_tool(
            "firecrawl_search",
            {
                "query": consulta,
                "limit": limite,
            },
        )

        resultado = resposta.get("result", {})

        if resultado.get("isError"):
            print(
                "JARVIS WEB: Firecrawl retornou erro na pesquisa.",
                flush=True,
            )
            return []

        conteudo = resultado.get("content", [])

        texto = _extrair_texto_mcp(conteudo)

        if texto:
            try:
                dados = json.loads(texto)
            except Exception:
                dados = conteudo
        else:
            dados = conteudo

        resultados = _normalizar_firecrawl(
            dados,
            consulta,
            limite,
        )

        if resultados:
            print(
                f"JARVIS WEB: Firecrawl MCP -> {len(resultados)} resultados",
                flush=True,
            )

        return resultados

    except Exception as exc:
        print(
            f"JARVIS WEB: erro Firecrawl: {exc}",
            flush=True,
        )
        return []

    finally:
        cliente.stop()


def pesquisar_mcp(
    consultas,
    limite: int = 5,
    temporal: bool = False,
    verificar_atualidade: Optional[bool] = None,
    usar_firecrawl: bool = True,
) -> List[Dict[str, Any]]:
    """
    Pipeline principal de pesquisa:

    1. Perplexity Search
    2. Firecrawl MCP somente se Perplexity não retornar resultados
    """
    if isinstance(consultas, str):
        consultas = [consultas]

    consultas = list(consultas or [])

    for consulta in consultas:
        consulta = str(consulta or "").strip()

        if not consulta:
            continue

        resultados = pesquisar_perplexity(
            consulta=consulta,
            limite=limite,
            temporal=temporal,
            verificar_atualidade=verificar_atualidade,
        )

        if resultados:
            return resultados[:limite]

        if usar_firecrawl:
            print(
                "JARVIS WEB: Perplexity sem resultados -> fallback Firecrawl MCP",
                flush=True,
            )

            resultados = pesquisar_firecrawl(
                consulta=consulta,
                limite=limite,
                temporal=temporal,
                verificar_atualidade=verificar_atualidade,
            )

            if resultados:
                return resultados[:limite]

    return []


def pesquisar_com_mcp(
    consultas,
    limite: int = 5,
    temporal: bool = False,
    verificar_atualidade: Optional[bool] = None,
    usar_firecrawl: bool = True,
) -> List[Dict[str, Any]]:
    return pesquisar_mcp(
        consultas=consultas,
        limite=limite,
        temporal=temporal,
        verificar_atualidade=verificar_atualidade,
        usar_firecrawl=usar_firecrawl,
    )


if __name__ == "__main__":
    print("=" * 70)
    print("TESTE JARVIS WEB")
    print("=" * 70)

    print(
        "PERPLEXITY_API_KEY:",
        "CONFIGURADA" if _perplexity_key() else "AUSENTE",
    )

    print(
        "FIRECRAWL_API_KEY:",
        "CONFIGURADA" if _firecrawl_key() else "AUSENTE",
    )

    consulta = "Palmeiras próximo jogo"

    print()
    print("CONSULTA:", consulta)
    print()

    resultados = pesquisar_mcp(
        consultas=[consulta],
        limite=5,
        temporal=True,
        verificar_atualidade=True,
        usar_firecrawl=True,
    )

    print()
    print("TOTAL:", len(resultados))

    for i, resultado in enumerate(resultados, 1):
        print()
        print(f"[{i}] {resultado.get('provider')}")
        print("TÍTULO:", resultado.get("title", ""))
        print("URL:", resultado.get("url", ""))
        print("DATA:", resultado.get("source_date", ""))
