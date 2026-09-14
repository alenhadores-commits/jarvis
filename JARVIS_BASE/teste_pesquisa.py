# -*- coding: utf-8 -*-

from playwright.sync_api import sync_playwright

from ai.executor import Executor
from ai.orquestrador import Orquestrador


orquestrador = Orquestrador()

acao = orquestrador.interpretar(
    "qual o próximo jogo do Palmeiras"
)

print("AÇÃO:")
print(acao)

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False
    )

    page = browser.new_page()

    print()
    print("EXECUTANDO PESQUISA...")

    resposta = Executor().executar(
        page,
        acao
    )

    print()
    print("=" * 60)
    print("RESPOSTA FINAL DO JARVIS")
    print("=" * 60)
    print(resposta)
    print("=" * 60)

    input("\nPressione ENTER para fechar...")

    browser.close()
