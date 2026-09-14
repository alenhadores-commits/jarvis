# -*- coding: utf-8 -*-

import requests


URLS_TESTE = [
    "https://connectivitycheck.gstatic.com/generate_204",
    "https://www.cloudflare.com/",
]


def internet_disponivel(timeout=3):
    """
    Verifica se existe acesso real à internet.
    Retorna True ou False.
    """

    for url in URLS_TESTE:

        try:

            resposta = requests.get(
                url,
                timeout=timeout,
                allow_redirects=True
            )

            if resposta.status_code < 500:
                return True

        except requests.RequestException:
            continue

    return False