# ============================================================
# JARVIS - MEMÓRIAS PERMANENTES
# ============================================================

from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent

ARQUIVO_MEMORIAS = (
    BASE_DIR / "memorias_permanentes.json"
)


# ============================================================
# MEMÓRIAS INICIAIS
# ============================================================

MEMORIAS_INICIAIS = [
    "O usuário prefere ser chamado de chefe.",
    "O usuário é dentista.",
    "O usuário desenvolve o projeto JARVIS.",
    "O usuário prefere respostas curtas, diretas e objetivas.",
    "O JARVIS deve falar português brasileiro.",
    "O JARVIS possui personalidade alagoana, inteligente, debochada e sarcástica.",
]


# ============================================================
# CARREGAR MEMÓRIAS
# ============================================================

def carregar_memorias():
    """
    Carrega as memórias permanentes do arquivo JSON.
    """

    if not ARQUIVO_MEMORIAS.exists():
        salvar_memorias(MEMORIAS_INICIAIS)
        return list(MEMORIAS_INICIAIS)

    try:
        with open(
            ARQUIVO_MEMORIAS,
            "r",
            encoding="utf-8"
        ) as arquivo:

            dados = json.load(arquivo)

        if not isinstance(dados, list):
            raise ValueError(
                "O arquivo de memórias não contém uma lista."
            )

        return [
            str(memoria).strip()
            for memoria in dados
            if str(memoria).strip()
        ]

    except (
        json.JSONDecodeError,
        OSError,
        ValueError
    ):
        return []


# ============================================================
# SALVAR MEMÓRIAS
# ============================================================

def salvar_memorias(memorias):
    """
    Salva as memórias permanentes no arquivo JSON.
    """

    memorias_limpas = []

    for memoria in memorias:

        memoria = str(memoria).strip()

        if not memoria:
            continue

        if memoria not in memorias_limpas:
            memorias_limpas.append(memoria)

    with open(
        ARQUIVO_MEMORIAS,
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            memorias_limpas,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


# ============================================================
# OBTER MEMÓRIAS
# ============================================================

def obter_memorias_permanentes():
    """
    Retorna todas as memórias permanentes.
    """

    return carregar_memorias()


# ============================================================
# FORMATAR PARA O CHATGPT
# ============================================================

def formatar_memorias_permanentes():
    """
    Converte as memórias para texto que será enviado
    ao ChatGPT.
    """

    memorias = obter_memorias_permanentes()

    if not memorias:
        return "Nenhuma memória permanente cadastrada."

    return "\n".join(
        f"- {memoria}"
        for memoria in memorias
    )


# ============================================================
# ADICIONAR MEMÓRIA
# ============================================================

def adicionar_memoria(memoria):
    """
    Adiciona uma nova memória permanente.
    """

    memoria = str(memoria).strip()

    if not memoria:
        return False

    memorias = carregar_memorias()

    if memoria in memorias:
        return False

    memorias.append(memoria)

    salvar_memorias(memorias)

    return True


# ============================================================
# REMOVER MEMÓRIA
# ============================================================

def remover_memoria(indice):
    """
    Remove uma memória pelo número exibido na lista.
    """

    memorias = carregar_memorias()

    try:
        indice = int(indice)
    except (TypeError, ValueError):
        return False

    posicao = indice - 1

    if posicao < 0 or posicao >= len(memorias):
        return False

    memorias.pop(posicao)

    salvar_memorias(memorias)

    return True


# ============================================================
# LISTAR MEMÓRIAS
# ============================================================

def listar_memorias():
    """
    Exibe as memórias permanentes no terminal.
    """

    memorias = carregar_memorias()

    print()
    print("=" * 60)
    print(" JARVIS - MEMÓRIAS PERMANENTES")
    print("=" * 60)

    if not memorias:
        print()
        print("Nenhuma memória cadastrada.")
        print()
        return

    for numero, memoria in enumerate(memorias, start=1):

        print(
            f"[{numero}] {memoria}"
        )

    print()


# ============================================================
# MENU DE MEMÓRIAS
# ============================================================

def menu_memorias():
    """
    Menu independente para gerenciamento
    das memórias permanentes.
    """

    while True:

        listar_memorias()

        print("[1] Adicionar memória")
        print("[2] Remover memória")
        print("[3] Voltar")

        escolha = input(
            "\nEscolha: "
        ).strip()

        # ----------------------------------------------------
        # ADICIONAR
        # ----------------------------------------------------

        if escolha == "1":

            memoria = input(
                "\nNova memória: "
            ).strip()

            if adicionar_memoria(memoria):

                print(
                    "\nJARVIS: Memória permanente salva."
                )

            else:

                print(
                    "\nJARVIS: Essa memória já existe "
                    "ou está vazia."
                )

        # ----------------------------------------------------
        # REMOVER
        # ----------------------------------------------------

        elif escolha == "2":

            indice = input(
                "\nNúmero da memória para remover: "
            ).strip()

            if remover_memoria(indice):

                print(
                    "\nJARVIS: Memória removida."
                )

            else:

                print(
                    "\nJARVIS: Número de memória inválido."
                )

        # ----------------------------------------------------
        # VOLTAR
        # ----------------------------------------------------

        elif escolha == "3":

            print()
            break

        else:

            print(
                "\nJARVIS: Escolha inválida."
            )


# ============================================================
# TESTE DIRETO
# ============================================================

if __name__ == "__main__":

    listar_memorias()

    print(
        "Arquivo:",
        ARQUIVO_MEMORIAS
    )
