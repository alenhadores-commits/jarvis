# -*- coding: utf-8 -*-

import re


TIPOS_VALIDOS = {
    "NOME",
    "PREFERENCIA",
    "ROTINA",
    "PROJETO",
    "TRABALHO",
    "LEMBRETE",
    "AGENDAMENTO",
    "COMANDO",
    "INFORMACAO",
    "OUTRO",
}


INICIO_PERGUNTAS = (
    "qual ",
    "quem ",
    "quando ",
    "onde ",
    "como ",
    "por que ",
    "porque ",
    "quanto ",
    "quantos ",
    "quantas ",
    "o que ",
    "que horas ",
    "qual é ",
    "qual foi ",
    "qual será ",
    "qual será o ",
)


def _parece_pergunta(mensagem):

    texto = mensagem.strip().lower()

    if not texto:
        return False

    if "?" in texto:
        return True

    return texto.startswith(INICIO_PERGUNTAS)


def _limpar_valor(valor):

    valor = re.sub(
        r"\s+",
        " ",
        valor.strip()
    )

    valor = re.split(
        r"[.!?]",
        valor,
        maxsplit=1
    )[0].strip()

    return valor


# ==========================================================
# NOME
# ==========================================================

def _extrair_nome(mensagem):

    padroes = [
        r"\bmeu nome é\s+(.+?)(?=\s+e\s+quero\b|\s+e\s+gostaria\b|\s+e\s+prefiro\b|[.!?]|$)",
        r"\bme chamo\s+(.+?)(?=\s+e\s+quero\b|\s+e\s+gostaria\b|\s+e\s+prefiro\b|[.!?]|$)",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            mensagem,
            re.IGNORECASE
        )

        if not match:
            continue

        nome = _limpar_valor(
            match.group(1)
        )

        if nome:

            return {
                "tipo": "NOME",
                "duracao": "PERMANENTE",
                "conteudo": f"O nome do usuário é {nome}.",
                "importancia": 10,
            }

    return None


# ==========================================================
# PREFERÊNCIA DE TRATAMENTO
# ==========================================================

def _extrair_preferencia_chamado(mensagem):

    padroes = [
        r"\bquero que você sempre me chame de\s+(.+?)(?=\s+e\s+|\s+mas\s+|[.!?]|$)",
        r"\bquero que você me chame de\s+(.+?)(?=\s+e\s+|\s+mas\s+|[.!?]|$)",
        r"\bquero que me chame de\s+(.+?)(?=\s+e\s+|\s+mas\s+|[.!?]|$)",
        r"\bquero ser chamado de\s+(.+?)(?=\s+e\s+|\s+mas\s+|[.!?]|$)",
        r"\bpode me chamar de\s+(.+?)(?=\s+e\s+|\s+mas\s+|[.!?]|$)",
        r"\bprefiro ser chamado de\s+(.+?)(?=\s+e\s+|\s+mas\s+|[.!?]|$)",
        r"\bprefiro que você me chame de\s+(.+?)(?=\s+e\s+|\s+mas\s+|[.!?]|$)",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            mensagem,
            re.IGNORECASE
        )

        if not match:
            continue

        valor = _limpar_valor(
            match.group(1)
        )

        if valor:

            return {
                "tipo": "PREFERENCIA",
                "duracao": "PERMANENTE",
                "conteudo": (
                    f"O usuário prefere ser chamado de {valor}."
                ),
                "importancia": 10,
            }

    return None


# ==========================================================
# GOSTOS
# ==========================================================

def _extrair_gostos(mensagem):

    memorias = []

    # ------------------------------------------------------
    # GOSTO DE
    # ------------------------------------------------------

    match = re.search(
        r"\bgosto de\s+(.+)",
        mensagem,
        re.IGNORECASE
    )

    if match:

        valor = match.group(1)

        # Corta conectores que iniciam outra intenção.
        valor = re.split(
            r"\s+e\s+(?=(?:quero|gostaria|prefiro|não gosto|me chame|ser chamado))",
            valor,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0]

        valor = _limpar_valor(
            valor
        )

        if valor:

            memorias.append({
                "tipo": "PREFERENCIA",
                "duracao": "PERMANENTE",
                "conteudo": f"O usuário gosta de {valor}.",
                "importancia": 8,
            })

    # ------------------------------------------------------
    # NÃO GOSTO DE
    # ------------------------------------------------------

    match = re.search(
        r"\bnão gosto de\s+(.+)",
        mensagem,
        re.IGNORECASE
    )

    if match:

        valor = match.group(1)

        valor = re.split(
            r"\s+e\s+(?=(?:quero|gostaria|prefiro|gosto|me chame|ser chamado))",
            valor,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0]

        valor = _limpar_valor(
            valor
        )

        if valor:

            memorias.append({
                "tipo": "PREFERENCIA",
                "duracao": "PERMANENTE",
                "conteudo": f"O usuário não gosta de {valor}.",
                "importancia": 8,
            })

    return memorias


# ==========================================================
# PROJETO
# ==========================================================

def _extrair_projeto(mensagem):

    padroes = [
        r"\bestou trabalhando no projeto\s+(.+)",
        r"\bmeu projeto é\s+(.+)",
        r"\bestou desenvolvendo\s+(.+)",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            mensagem,
            re.IGNORECASE
        )

        if not match:
            continue

        projeto = match.group(1)

        projeto = re.split(
            r"\s+e\s+(?=(?:quero|gostaria|prefiro|gosto))",
            projeto,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0]

        projeto = _limpar_valor(
            projeto
        )

        if projeto:

            return {
                "tipo": "PROJETO",
                "duracao": "PERMANENTE",
                "conteudo": (
                    f"O usuário está trabalhando em {projeto}."
                ),
                "importancia": 8,
            }

    return None


# ==========================================================
# ROTINA
# ==========================================================

def _extrair_rotina(mensagem):

    padroes = [
        r"\beu sempre\s+(.+)",
        r"\beu costumo\s+(.+)",
        r"\bnormalmente eu\s+(.+)",
    ]

    for padrao in padroes:

        match = re.search(
            padrao,
            mensagem,
            re.IGNORECASE
        )

        if not match:
            continue

        rotina = match.group(1)

        rotina = re.split(
            r"\s+e\s+(?=(?:quero|gostaria|prefiro|gosto|me chame|ser chamado))",
            rotina,
            maxsplit=1,
            flags=re.IGNORECASE
        )[0]

        rotina = _limpar_valor(
            rotina
        )

        if rotina:

            return {
                "tipo": "ROTINA",
                "duracao": "PERMANENTE",
                "conteudo": (
                    f"O usuário costuma {rotina}."
                ),
                "importancia": 5,
            }

    return None


# ==========================================================
# EXTRAÇÃO
# ==========================================================

def extrair_memorias(mensagem):

    if not mensagem:
        return []

    mensagem = mensagem.strip()

    if not mensagem:
        return []

    # Nunca memorizar perguntas automaticamente.
    if _parece_pergunta(mensagem):
        return []

    memorias = []

    # ------------------------------------------------------
    # NOME
    # ------------------------------------------------------

    nome = _extrair_nome(
        mensagem
    )

    if nome:
        memorias.append(
            nome
        )

    # ------------------------------------------------------
    # PREFERÊNCIA DE TRATAMENTO
    # ------------------------------------------------------

    preferencia_chamado = (
        _extrair_preferencia_chamado(
            mensagem
        )
    )

    if preferencia_chamado:
        memorias.append(
            preferencia_chamado
        )

    # ------------------------------------------------------
    # GOSTOS
    # ------------------------------------------------------

    memorias.extend(
        _extrair_gostos(
            mensagem
        )
    )

    # ------------------------------------------------------
    # PROJETO
    # ------------------------------------------------------

    projeto = _extrair_projeto(
        mensagem
    )

    if projeto:
        memorias.append(
            projeto
        )

    # ------------------------------------------------------
    # ROTINA
    # ------------------------------------------------------

    rotina = _extrair_rotina(
        mensagem
    )

    if rotina:
        memorias.append(
            rotina
        )

    # ------------------------------------------------------
    # REMOVER DUPLICATAS
    # ------------------------------------------------------

    resultado = []

    vistos = set()

    for memoria in memorias:

        chave = (
            memoria["tipo"],
            memoria["conteudo"].lower().strip()
        )

        if chave in vistos:
            continue

        vistos.add(
            chave
        )

        resultado.append(
            memoria
        )

    return resultado


# ==========================================================
# COMPATIBILIDADE
# ==========================================================

def extrair_memoria(mensagem):

    memorias = extrair_memorias(
        mensagem
    )

    if not memorias:
        return None

    return memorias[0]