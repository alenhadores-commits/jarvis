from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import requests


class IARouter:
    """
    SDK simples para conectar qualquer projeto ao IA Router.

    O projeto consumidor não precisa conhecer Groq, Gemini,
    OpenRouter, NVIDIA, Hugging Face ou Cohere.
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int = 120,
    ):
        self.base_url = (
            base_url
            or os.getenv(
                "IA_ROUTER_URL",
                "http://127.0.0.1:8765",
            )
        ).rstrip("/")

        self.api_key = (
            api_key
            if api_key is not None
            else os.getenv(
                "ROUTER_API_KEY",
                "",
            )
        ).strip()

        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }

        if self.api_key:
            headers["Authorization"] = (
                f"Bearer {self.api_key}"
            )

        return headers

    def ask(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 128,
    ) -> str:

        messages = []

        if system:
            messages.append({
                "role": "system",
                "content": system,
            })

        messages.append({
            "role": "user",
            "content": prompt,
        })

        result = self.chat(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return result["text"]

    def chat(
        self,
        messages: list[dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 128,
    ) -> dict[str, Any]:

        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers=self._headers(),
            json={
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            timeout=self.timeout,
        )

        response.raise_for_status()

        data = response.json()

        choice = (
            data.get("choices") or [{}]
        )[0]

        message = choice.get(
            "message",
            {},
        )

        return {
            "text": message.get("content", ""),
            "provider": (
                data.get("router", {})
                .get("provider")
            ),
            "model": data.get("model"),
            "usage": data.get("usage", {}),
            "raw": data,
        }

    def status(self) -> dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/status",
            headers=self._headers(),
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    def providers(self) -> list[dict[str, Any]]:
        response = requests.get(
            f"{self.base_url}/providers",
            headers=self._headers(),
            timeout=10,
        )

        response.raise_for_status()

        return response.json().get(
            "providers",
            [],
        )

    def usage(self) -> dict[str, Any]:
        response = requests.get(
            f"{self.base_url}/usage",
            headers=self._headers(),
            timeout=10,
        )

        response.raise_for_status()

        return response.json()

    def test(self) -> dict[str, Any]:
        return self.chat(
            [
                {
                    "role": "user",
                    "content": "Responda apenas: OK",
                }
            ],
            temperature=0,
            max_tokens=8,
        )

    async def websocket(
        self,
        message_type: str = "status",
    ):
        """
        Cliente WebSocket assíncrono.

        Requer:
            pip install websockets
        """

        try:
            import websockets
        except ImportError as exc:
            raise RuntimeError(
                "Instale websockets com: "
                "python -m pip install websockets"
            ) from exc

        ws_url = (
            self.base_url
            .replace("https://", "wss://")
            .replace("http://", "ws://")
            + "/ws"
        )

        async with websockets.connect(
            ws_url,
            additional_headers=(
                self._headers()
            ),
        ) as websocket:

            conectado = await websocket.recv()

            await websocket.send(
                json.dumps({
                    "type": message_type,
                })
            )

            resposta = await websocket.recv()

            return {
                "connected": json.loads(conectado),
                "response": json.loads(resposta),
            }


_default = IARouter()


def ask(
    prompt: str,
    system: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 128,
) -> str:

    return _default.ask(
        prompt=prompt,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def chat(
    messages: list[dict[str, Any]],
    temperature: float = 0.7,
    max_tokens: int = 128,
) -> dict[str, Any]:

    return _default.chat(
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def status():
    return _default.status()


def providers():
    return _default.providers()


def usage():
    return _default.usage()


def test():
    return _default.test()


async def websocket(message_type="status"):
    return await _default.websocket(message_type)
