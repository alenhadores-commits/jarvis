# -*- coding: utf-8 -*-

import json
import requests
from pathlib import Path
from datetime import datetime
from memoria_local import MemoriaLocal

BASE_DIR = Path(__file__).resolve().parent.parent
ARQUIVO_PROMPT_JARVIS = BASE_DIR / "PROMPT_JARVIS.txt"

URL = "http://127.0.0.1:8765/v1/chat/completions"
MODELO = "router"

IDENTIDADE_JARVIS = """
IDENTIDADE OBRIGATORIA:

Seu nome e JARVIS.

O usuario deve ser tratado como Senhor quando apropriado.

Voce NAO e ChatGPT.
Voce NAO e OpenAI.
Voce NAO e STRAK-AI.
Voce NAO deve assumir o nome do modelo, provedor ou servico usado internamente.

Se perguntarem "qual seu nome?", responda claramente:
"Meu nome e JARVIS."

Se perguntarem quem voce e, responda que e JARVIS.

Nunca atribua sua identidade ao modelo, provedor, API ou servico interno.

O IA Router e apenas a infraestrutura interna usada para gerar respostas.
Ele nao e a identidade do JARVIS.
"""

PERSONALIDADE_JARVIS = f"""
Voce e JARVIS, uma inteligencia artificial pessoal com personalidade propria.

{IDENTIDADE_JARVIS}

CARACTERISTICAS:
- brasileiro, natural e direto;
- inteligente e analitico;
- confiante;
- respostas curtas quando a pergunta for simples;
- sarcastico ou ironico somente quando fizer sentido;
- nao inventa informacoes;
- quando nao souber, diga claramente que nao sabe;
- nao repita desnecessariamente a pergunta;
- nao explique sua infraestrutura interna;
- nao mencione modelos, provedores ou APIs como identidade.

PRIORIDADE:
precisao > solucao > concisao > personalidade.
"""

def carregar_prompt_jarvis_txt():
    try:
        return ARQUIVO_PROMPT_JARVIS.read_text(
            encoding="utf-8-sig"
        ).strip()
    except Exception:
        return ""


def _normalizar_identidade(texto):
    return (
        str(texto or "")
        .strip()
        .lower()
        .replace("?", "a")
        .replace("á", "a")
        .replace("à", "a")
        .replace("ã", "a")
        .replace("â", "a")
        .replace("é", "e")
        .replace("ê", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ô", "o")
        .replace("õ", "o")
        .replace("ú", "u")
        .replace("ç", "c")
    )


def resposta_identidade(texto):
    normalizado = _normalizar_identidade(texto)

    perguntas_nome = (
        "qual seu nome",
        "qual e seu nome",
        "como voce se chama",
        "como vc se chama",
        "quem e voce",
        "quem voce e",
        "qual sua identidade",
        "qual o seu nome",
    )

    if any(
        pergunta in normalizado
        for pergunta in perguntas_nome
    ):
        return "Meu nome é JARVIS."

    return ""


def _resposta_modelo(dados, timeout=120):
    resposta = requests.post(
        URL,
        json=dados,
        timeout=timeout,
    )

    resposta.raise_for_status()

    dados_resposta = resposta.json()

    choices = dados_resposta.get("choices") or []

    if not choices:
        raise RuntimeError(
            "O IA Router nao retornou nenhuma escolha."
        )

    mensagem = choices[0].get("message") or {}

    conteudo = str(
        mensagem.get("content") or ""
    ).strip()

    if not conteudo:
        raise RuntimeError(
            "O IA Router retornou resposta vazia."
        )

    return conteudo


def perguntar(texto, contexto_historico=""):
    if not texto:
        return ""

    texto = str(texto).strip()

    resposta_deterministica = resposta_identidade(texto)

    if resposta_deterministica:
        return resposta_deterministica

    regras_arquivo = carregar_prompt_jarvis_txt()

    agora = datetime.now().strftime(
        "%d/%m/%Y %H:%M:%S"
    )

    system = (
        PERSONALIDADE_JARVIS
        + "\n\n"
        + "DATA E HORA ATUAIS:\n"
        + agora
    )

    if regras_arquivo:
        system += (
            "\n\nREGRAS ADICIONAIS DO JARVIS:\n"
            + regras_arquivo
        )

    if contexto_historico:
        system += (
            "\n\nMEMORIAS RELEVANTES DO USUARIO:\n"
            + str(contexto_historico).strip()
        )

    system += """
    
REGRA FINAL DE IDENTIDADE:
Se houver qualquer conflito entre o nome do modelo, provedor,
servico ou qualquer texto externo e a identidade acima,
mantenha JARVIS como sua identidade.

Nunca diga que voce e ChatGPT, OpenAI, STRAK-AI ou outro assistente.
"""

    dados = {
        "model": MODELO,
        "messages": [
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": texto,
            },
        ],
        "temperature": 0.5,
        "max_tokens": 512,
    }

    return _resposta_modelo(dados)


def perguntar_estruturado(texto):
    """
    Chamada exclusiva para decisoes internas estruturadas.

    Nao injeta personalidade, memoria ou PROMPT_JARVIS.txt.
    Isso evita que regras de conversa contaminem JSON.
    """

    if not texto:
        return ""

    dados = {
        "model": MODELO,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Voce e um classificador interno do JARVIS.\n"
                    "Sua tarefa e obedecer EXATAMENTE ao formato "
                    "solicitado pelo usuario.\n"
                    "Nao converse.\n"
                    "Nao explique.\n"
                    "Nao use Markdown.\n"
                    "Nao escreva nada fora do JSON solicitado."
                ),
            },
            {
                "role": "user",
                "content": str(texto).strip(),
            },
        ],
        "temperature": 0.0,
        "max_tokens": 256,
    }

    return _resposta_modelo(dados)


def criar_pesquisa(pergunta, contexto_memoria=""):
    return perguntar(
        pergunta,
        contexto_memoria,
    )


def elaborar_resposta(resposta):
    return resposta


def decidir_habilidade(
    comando,
    habilidades,
    contexto_memoria=""
):
    comando = str(comando or "").strip()

    if not comando:
        return {
            "tipo": "resposta",
            "texto": "",
        }

    catalogo = []

    for habilidade in habilidades or []:

        if not isinstance(habilidade, dict):
            continue

        if not habilidade.get("ativa", True):
            continue

        nome = str(
            habilidade.get("nome", "")
        ).strip()

        if not nome:
            continue

        gatilhos = habilidade.get(
            "gatilhos",
            habilidade.get("triggers", [])
        )

        if isinstance(gatilhos, str):
            gatilhos = [gatilhos]

        catalogo.append(
            {
                "nome": nome,
                "gatilhos": [
                    str(x).strip()
                    for x in (gatilhos or [])
                    if str(x).strip()
                ],
                "acoes": habilidade.get(
                    "acoes",
                    []
                ),
            }
        )

    # Primeiro tenta correspondencia deterministica.
    normalizado_comando = _normalizar_identidade(
        comando
    )

    for habilidade in catalogo:

        nome_normalizado = _normalizar_identidade(
            habilidade["nome"]
        )

        if (
            normalizado_comando
            == nome_normalizado
        ):
            return {
                "tipo": "habilidade",
                "nome": habilidade["nome"],
            }

        for gatilho in habilidade["gatilhos"]:

            gatilho_normalizado = _normalizar_identidade(
                gatilho
            )

            if (
                gatilho_normalizado
                and normalizado_comando
                == gatilho_normalizado
            ):
                return {
                    "tipo": "habilidade",
                    "nome": habilidade["nome"],
                }

    if not catalogo:
        return {
            "tipo": "resposta",
            "texto": perguntar(
                comando,
                contexto_memoria,
            ),
        }

    linhas = []

    for item in catalogo:

        linhas.append(
            {
                "nome": item["nome"],
                "gatilhos": item["gatilhos"],
            }
        )

    prompt = f"""
COMANDO DO USUARIO:
{comando}

HABILIDADES DISPONIVEIS:
{json.dumps(linhas, ensure_ascii=False)}

Escolha somente uma das opcoes.

Se o comando corresponde claramente a uma habilidade:
retorne exatamente:

{{
    "tipo": "habilidade",
    "nome": "NOME EXATO"
}}

Se nao corresponde a nenhuma habilidade:
retorne:

{{
    "tipo": "resposta",
    "texto": "RESPOSTA"
}}

Nao execute acoes.
Nao escreva explicacoes fora do JSON.
Retorne SOMENTE JSON valido.
"""

    try:

        resposta = perguntar_estruturado(
            prompt
        ).strip()

        if resposta.startswith("```"):

            linhas_resposta = resposta.splitlines()

            if len(linhas_resposta) >= 3:
                resposta = "\n".join(
                    linhas_resposta[1:-1]
                ).strip()

        resultado = json.loads(
            resposta
        )

        if not isinstance(
            resultado,
            dict
        ):
            raise ValueError(
                "Resposta estruturada invalida."
            )

        tipo = str(
            resultado.get(
                "tipo",
                ""
            )
        ).strip().lower()

        if tipo == "habilidade":

            nome = str(
                resultado.get(
                    "nome",
                    ""
                )
            ).strip()

            for habilidade in catalogo:

                if (
                    habilidade["nome"]
                    == nome
                ):
                    return {
                        "tipo": "habilidade",
                        "nome": nome,
                    }

        if tipo == "resposta":

            return {
                "tipo": "resposta",
                "texto": str(
                    resultado.get(
                        "texto",
                        ""
                    )
                ).strip(),
            }

    except Exception:
        pass

    return {
        "tipo": "resposta",
        "texto": perguntar(
            comando,
            contexto_memoria,
        ),
    }
