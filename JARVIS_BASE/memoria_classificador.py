# -*- coding: utf-8 -*-

"""
CLASSIFICADOR DE MEMORIA DO JARVIS

Responsabilidades:
- Identificar informacoes que podem ser armazenadas.
- Separar corretamente nome, forma de tratamento, pet, favoritos,
  preferencias, trabalho, familia, projeto e rotina.
- Impedir que uma forma de tratamento seja confundida com o nome.
- Impedir que perguntas sejam gravadas como memoria.
- Preservar memoria manual explicita.
"""

import re
import unicodedata


PONTUACAO_MINIMA_PERMANENTE = 7


def normalizar(texto: str) -> str:
    """
    Normaliza acentos e caixa para facilitar as comparacoes.
    Mantem o texto original intacto no campo 'conteudo'.
    """
    texto = str(texto or "").strip().lower()

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    texto = re.sub(r"\s+", " ", texto)

    return texto


def eh_pergunta(texto: str) -> bool:
    """
    Detecta perguntas diretas.
    """
    normalizado = normalizar(texto)

    if not normalizado:
        return False

    if "?" in texto:
        return True

    padroes = [
        r"^\s*qual\b",
        r"^\s*quem\b",
        r"^\s*onde\b",
        r"^\s*quando\b",
        r"^\s*como\b",
        r"^\s*por que\b",
        r"^\s*porque\b",
        r"^\s*quanto\b",
        r"^\s*quantos\b",
        r"^\s*quantas\b",
        r"^\s*o que\b",
        r"^\s*que\b",
        r"^\s*qual e\b",
        r"^\s*qual meu\b",
        r"^\s*qual minha\b",
        r"^\s*qual o\b",
        r"^\s*qual a\b",
    ]

    return any(
        re.search(padrao, normalizado)
        for padrao in padroes
    )


def memoria_explicitamente_solicitada(texto: str) -> bool:
    """
    Detecta quando o usuario pede explicitamente para memorizar.
    """
    normalizado = normalizar(texto)

    padroes = [
        r"\blembre\b",
        r"\blembra\b",
        r"\bguarde\b",
        r"\bmemorize\b",
        r"\bmemorizar\b",
        r"\bsalve\b",
        r"\bsalvar\b",
        r"\banote\b",
        r"\banotar\b",
        r"\bregistre\b",
        r"\bregistrar\b",
        r"\btenha em mente\b",
        r"\bnao esqueca\b",
        r"\bquero que voce lembre\b",
        r"\bquero que voce saiba\b",
        r"\baprenda que\b",
    ]

    return any(
        re.search(padrao, normalizado)
        for padrao in padroes
    )


def classificar_memoria(texto: str) -> dict:
    """
    Classifica uma mensagem para o sistema de memoria do JARVIS.

    Retorno:
    {
        "eh_memoria": bool,
        "permanente": bool,
        "tipo": str,
        "importancia": int,
        "conteudo": str,
        "motivo": str
    }
    """

    original = str(texto or "").strip()

    if not original:
        return {
            "eh_memoria": False,
            "permanente": False,
            "tipo": "OUTRO",
            "importancia": 0,
            "conteudo": "",
            "motivo": "entrada_vazia",
        }

    normalizado = normalizar(original)

    motivos = []
    pontos = 0
    tipo = "OUTRO"

    memoria_explicita = memoria_explicitamente_solicitada(
        original
    )

    # ==========================================================
    # PERGUNTA
    # ==========================================================

    if eh_pergunta(original) and not memoria_explicita:
        return {
            "eh_memoria": False,
            "permanente": False,
            "tipo": "PERGUNTA",
            "importancia": 0,
            "conteudo": original,
            "motivo": "pergunta_nao_deve_ser_memoria",
        }

    # ==========================================================
    # COMO O USUARIO QUER SER CHAMADO
    # ==========================================================

    # IMPORTANTE:
    # Esta verificacao vem ANTES de NOME.
    # Assim:
    # "Quero que me chame de SENHOR"
    # nao vira nome = SENHOR.

    if (
        re.search(
            r"\bquero que voce me chame de\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bquero que me chame de\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bme chame de\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bpode me chamar de\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bpode chamar de\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bprefiro ser chamado de\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bprefiro que me chame de\s+(.+)",
            normalizado,
        )
    ):
        tipo = "COMO_CHAMAR"
        pontos += 8
        motivos.append("forma_de_tratamento")

    # ==========================================================
    # NOME DO USUARIO
    # ==========================================================

    elif (
        re.search(
            r"\bmeu nome e\s+([a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ\s'-]*)",
            normalizado,
        )
        or re.search(
            r"\bme chamo\s+([a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ\s'-]*)",
            normalizado,
        )
        or re.search(
            r"\bmeu nome é\s+([a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ\s'-]*)",
            original.lower(),
        )
    ):
        tipo = "NOME"
        pontos += 8
        motivos.append("identidade")

    # ==========================================================
    # PET / ANIMAL DE ESTIMACAO
    # ==========================================================

    elif (
        re.search(
            r"\bmeu cachorro se chama\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bo nome do meu cachorro e\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bminha cachorra se chama\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bo nome da minha cachorra e\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bmeu gato se chama\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bo nome do meu gato e\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bminha gata se chama\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bo nome da minha gata e\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bmeu pet se chama\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\bo nome do meu pet e\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\btenho um cachorro chamado\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\btenho uma cachorra chamada\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\btenho um gato chamado\s+(.+)",
            normalizado,
        )
        or re.search(
            r"\btenho uma gata chamada\s+(.+)",
            normalizado,
        )
    ):
        tipo = "PET"
        pontos += 8
        motivos.append("animal_estimacao")

    # ==========================================================
    # COMIDA FAVORITA
    # ==========================================================

    elif (
        re.search(
            r"\bminha comida favorita e\b",
            normalizado,
        )
        or re.search(
            r"\bminha comida preferida e\b",
            normalizado,
        )
        or re.search(
            r"\bmeu prato favorito e\b",
            normalizado,
        )
        or re.search(
            r"\bmeu prato preferido e\b",
            normalizado,
        )
    ):
        tipo = "FAVORITO"
        pontos += 7
        motivos.append("comida_favorita")

    # ==========================================================
    # ANIMAL FAVORITO
    # ==========================================================

    elif (
        re.search(
            r"\bmeu animal favorito e\b",
            normalizado,
        )
        or re.search(
            r"\bmeu animal preferido e\b",
            normalizado,
        )
    ):
        tipo = "FAVORITO"
        pontos += 7
        motivos.append("animal_favorito")

    # ==========================================================
    # FILME FAVORITO
    # ==========================================================

    elif (
        re.search(
            r"\bmeu filme favorito e\b",
            normalizado,
        )
        or re.search(
            r"\bmeu filme preferido e\b",
            normalizado,
        )
    ):
        tipo = "FAVORITO"
        pontos += 7
        motivos.append("filme_favorito")

    # ==========================================================
    # JOGO FAVORITO
    # ==========================================================

    elif (
        re.search(
            r"\bmeu jogo favorito e\b",
            normalizado,
        )
        or re.search(
            r"\bmeu jogo preferido e\b",
            normalizado,
        )
    ):
        tipo = "FAVORITO"
        pontos += 7
        motivos.append("jogo_favorito")

    # ==========================================================
    # MUSICA FAVORITA
    # ==========================================================

    elif (
        re.search(
            r"\bminha musica favorita e\b",
            normalizado,
        )
        or re.search(
            r"\bminha musica preferida e\b",
            normalizado,
        )
    ):
        tipo = "FAVORITO"
        pontos += 7
        motivos.append("musica_favorita")

    # ==========================================================
    # COR FAVORITA
    # ==========================================================

    elif (
        re.search(
            r"\bminha cor favorita e\b",
            normalizado,
        )
        or re.search(
            r"\bminha cor preferida e\b",
            normalizado,
        )
    ):
        tipo = "FAVORITO"
        pontos += 7
        motivos.append("cor_favorita")

    # ==========================================================
    # ESPORTE / TIME
    # ==========================================================

    elif (
        re.search(
            r"\btorco para\b",
            normalizado,
        )
        or re.search(
            r"\bmeu time\b",
            normalizado,
        )
        or re.search(
            r"\btime que eu torco\b",
            normalizado,
        )
        or re.search(
            r"\bsou palmeirense\b",
            normalizado,
        )
        or re.search(
            r"\bsou flamenguista\b",
            normalizado,
        )
        or re.search(
            r"\bsou corinthiano\b",
            normalizado,
        )
        or re.search(
            r"\bsou vasca(?:ino|no)\b",
            normalizado,
        )
        or re.search(
            r"\bsou sao paulino\b",
            normalizado,
        )
    ):
        tipo = "ESPORTE"
        pontos += 7
        motivos.append("time_esportivo")

    # ==========================================================
    # TRABALHO / PROFISSAO
    # ==========================================================

    elif (
        re.search(
            r"\bsou\s+[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ\s'-]+",
            normalizado,
        )
        or re.search(
            r"\btrabalho como\b",
            normalizado,
        )
        or re.search(
            r"\bminha profissao e\b",
            normalizado,
        )
        or re.search(
            r"\bminha profissao e\b",
            normalizado,
        )
    ):
        # Nao classificar "sou Alex" como profissao.
        if not re.search(
            r"\bsou\s+(alex|meu nome)\b",
            normalizado,
        ):
            tipo = "TRABALHO"
            pontos += 6
            motivos.append("profissao")

    # ==========================================================
    # FAMILIA
    # ==========================================================

    elif (
        re.search(
            r"\bminha esposa\b",
            normalizado,
        )
        or re.search(
            r"\bmeu marido\b",
            normalizado,
        )
        or re.search(
            r"\bminha namorada\b",
            normalizado,
        )
        or re.search(
            r"\bmeu namorado\b",
            normalizado,
        )
        or re.search(
            r"\bmeu filho\b",
            normalizado,
        )
        or re.search(
            r"\bminha filha\b",
            normalizado,
        )
        or re.search(
            r"\bmeu pai\b",
            normalizado,
        )
        or re.search(
            r"\bminha mae\b",
            normalizado,
        )
        or re.search(
            r"\bmeu irmao\b",
            normalizado,
        )
        or re.search(
            r"\bminha irma\b",
            normalizado,
        )
    ):
        tipo = "FAMILIA"
        pontos += 7
        motivos.append("relacionamento_familiar")

    # ==========================================================
    # PROJETO
    # ==========================================================

    elif (
        re.search(
            r"\bmeu projeto\b",
            normalizado,
        )
        or re.search(
            r"\bestou desenvolvendo\b",
            normalizado,
        )
        or re.search(
            r"\bestou construindo\b",
            normalizado,
        )
        or re.search(
            r"\bestou criando\b",
            normalizado,
        )
    ):
        tipo = "PROJETO"
        pontos += 6
        motivos.append("projeto")

    # ==========================================================
    # ROTINA / HABITO
    # ==========================================================

    elif (
        re.search(
            r"\bcostumo\b",
            normalizado,
        )
        or re.search(
            r"\btenho o habito\b",
            normalizado,
        )
        or re.search(
            r"\bminha rotina\b",
            normalizado,
        )
        or re.search(
            r"\btodo dia\b",
            normalizado,
        )
        or re.search(
            r"\btodos os dias\b",
            normalizado,
        )
    ):
        tipo = "ROTINA"
        pontos += 5
        motivos.append("rotina_estavel")

    # ==========================================================
    # PREFERENCIA GERAL
    # ==========================================================

    elif (
        re.search(
            r"\bgosto de\b",
            normalizado,
        )
        or re.search(
            r"\badoro\b",
            normalizado,
        )
        or re.search(
            r"\bamo\b",
            normalizado,
        )
        or re.search(
            r"\bcurto\b",
            normalizado,
        )
        or re.search(
            r"\bprefiro\b",
            normalizado,
        )
        or re.search(
            r"\bmeu favorito\b",
            normalizado,
        )
        or re.search(
            r"\bminha favorita\b",
            normalizado,
        )
    ):
        tipo = "PREFERENCIA"
        pontos += 6
        motivos.append("preferencia")

    # ==========================================================
    # MEMORIA MANUAL EXPLICITA
    # ==========================================================

    if memoria_explicita:
        pontos += 5
        motivos.append("memoria_explicita")

    # ==========================================================
    # CONTEXTO TEMPORARIO
    # ==========================================================

    temporarios = [
        r"\bhoje\b",
        r"\bagora\b",
        r"\bnesse momento\b",
        r"\bno momento\b",
        r"\besta semana\b",
        r"\bamanha\b",
        r"\bontem\b",
        r"\bnessa semana\b",
    ]

    if any(
        re.search(
            padrao,
            normalizado,
        )
        for padrao in temporarios
    ):
        pontos -= 3
        motivos.append("contexto_temporario")

    # ==========================================================
    # REFERENCIA PESSOAL
    # ==========================================================

    palavras_pessoais = {
        "eu",
        "meu",
        "minha",
        "meus",
        "minhas",
        "me",
        "comigo",
        "meu",
        "minha",
    }

    palavras = set(
        normalizado.split()
    )

    tem_referencia_pessoal = bool(
        palavras.intersection(
            palavras_pessoais
        )
    )

    if tem_referencia_pessoal:
        pontos += 1
        motivos.append("referencia_pessoal")

    # ==========================================================
    # SE FOR MEMORIA MANUAL EXPLICITA,
    # GARANTIR QUE ELA SEJA ACEITA.
    # ==========================================================

    if memoria_explicita and tipo == "OUTRO":
        tipo = "CONTEXTO"
        pontos = max(
            pontos,
            PONTUACAO_MINIMA_PERMANENTE,
        )

    # ==========================================================
    # CALCULO FINAL
    # ==========================================================

    pontos = max(
        0,
        min(
            10,
            pontos,
        ),
    )

    eh_memoria = (
        pontos >= 4
    )

    if memoria_explicita:
        pontos = max(
            pontos,
            PONTUACAO_MINIMA_PERMANENTE,
        )

    permanente = (
        pontos >= PONTUACAO_MINIMA_PERMANENTE
    )

    if permanente and "importancia_duradoura" not in motivos:
        motivos.append(
            "importancia_duradoura"
        )

    # ==========================================================
    # RETORNO
    # ==========================================================

    return {
        "eh_memoria": eh_memoria,
        "permanente": permanente,
        "tipo": tipo,
        "importancia": pontos,
        "conteudo": original,
        "motivo": "; ".join(
            motivos
        ),
    }


# ==============================================================
# TESTE LOCAL
# ==============================================================

if __name__ == "__main__":

    exemplos = [
        "Meu nome é Alex.",
        "Meu nome é Alex. Quero que você me chame de SENHOR.",
        "Quero que você me chame de SENHOR.",
        "Pode me chamar de chefe.",
        "Meu cachorro se chama NEGUINHO.",
        "O nome do meu cachorro é NEGUINHO.",
        "Minha comida favorita é pizza.",
        "Meu animal favorito é cachorro.",
        "Eu gosto de Palmeiras.",
        "Meu projeto é o JARVIS.",
        "Hoje vou almoçar fora.",
        "Amanhã vou ao dentista.",
        "QUAL MEU NOME",
        "QUAL O NOME DO MEU CACHORRO",
    ]

    print("=" * 60)
    print(" TESTE DO CLASSIFICADOR DE MEMORIA")
    print("=" * 60)

    for exemplo in exemplos:

        resultado = classificar_memoria(
            exemplo
        )

        print()
        print("ENTRADA:")
        print(exemplo)
        print()
        print("RESULTADO:")
        print(resultado)
        print("-" * 60)
