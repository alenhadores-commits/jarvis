import sys
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from habilidades.gerenciador import GerenciadorHabilidades
from habilidades.executor import ExecutorHabilidades


PATH_HABILIDADES = BASE / "ensino" / "path_teste.json"
PROGRESSO = BASE / "ensino" / "progresso_teste.json"


def carregar_json(caminho, padrao):
    if not caminho.exists():
        print(f"JARVIS: Arquivo nao encontrado: {caminho}")
        return padrao

    try:
        texto = caminho.read_text(encoding="utf-8-sig")
        dados = json.loads(texto)

        print(f"JARVIS: JSON carregado: {caminho.name}")
        return dados

    except Exception as erro:
        print(f"JARVIS: ERRO lendo {caminho.name}: {erro}")
        return padrao


def salvar_json(caminho, dados):
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def habilidade_existe(gerenciador, gatilhos):
    for gatilho in gatilhos:

        try:
            encontrada = gerenciador.encontrar_cadastrada(gatilho)
            if encontrada:
                return encontrada
        except Exception as erro:
            print(f"JARVIS: Aviso encontrar_cadastrada: {erro}")

        try:
            encontrada = gerenciador.encontrar(gatilho)
            if encontrada:
                return encontrada
        except Exception as erro:
            print(f"JARVIS: Aviso encontrar: {erro}")

    return None


def executar_treinamento():

    print("=" * 65)
    print(" JARVIS - TESTE REAL DE TREINAMENTO AUTONOMO")
    print("=" * 65)

    print(f"PATH: {PATH_HABILIDADES}")

    path = carregar_json(PATH_HABILIDADES, [])

    print(f"Tipo carregado: {type(path).__name__}")

    if not isinstance(path, list):
        print("JARVIS: ERRO - PATH nao e uma lista.")
        return

    print(f"Total de habilidades: {len(path)}")

    if not path:
        print("JARVIS: PATH de treinamento vazio.")
        return

    progresso = carregar_json(
        PROGRESSO,
        {
            "total": 0,
            "concluidas": [],
            "falhas": [],
            "ultima": None
        }
    )

    progresso["total"] = len(path)

    gerenciador = GerenciadorHabilidades()
    executor = ExecutorHabilidades()

    print(f"Concluidas anteriormente: {len(progresso['concluidas'])}")
    print("=" * 65)

    for indice, habilidade in enumerate(path, start=1):

        nome = habilidade["nome"]

        if nome in progresso["concluidas"]:
            print(f"[{indice}/{len(path)}] {nome} -> JA APROVADA")
            continue

        print()
        print("-" * 65)
        print(f"[{indice}/{len(path)}] ENSINANDO: {nome}")
        print("-" * 65)

        progresso["ultima"] = nome
        salvar_json(PROGRESSO, progresso)

        existente = habilidade_existe(
            gerenciador,
            habilidade.get("gatilhos", [])
        )

        if existente:

            print("JARVIS: Habilidade ja cadastrada.")
            print("JARVIS: Validando execucao real...")

            try:
                resultado = executor.executar(existente)

                print("JARVIS: Resultado:")
                print(resultado)

                if (
                    isinstance(resultado, str)
                    and "falhou" not in resultado.lower()
                ):
                    progresso["concluidas"].append(nome)
                    salvar_json(PROGRESSO, progresso)

                    print("JARVIS: APROVADA.")
                    continue

            except Exception as erro:
                print(f"JARVIS: Falha na habilidade existente: {erro}")

        print("JARVIS: Habilidade nao encontrada.")
        print("JARVIS: Executando teste real da nova habilidade...")

        try:

            resultado = executor.executar(habilidade)

            print("JARVIS: Resultado:")
            print(resultado)

            sucesso = (
                isinstance(resultado, str)
                and "falhou" not in resultado.lower()
                and "erro" not in resultado.lower()
            )

            if not sucesso:

                print("JARVIS: REPROVADA.")

                progresso["falhas"].append({
                    "nome": nome,
                    "resultado": resultado
                })

                salvar_json(PROGRESSO, progresso)
                continue

            print("JARVIS: Execucao funcionou.")
            print("JARVIS: Cadastrando habilidade...")

            try:
                resultado_adicionar = gerenciador.adicionar(
                    nome=habilidade["nome"],
                    gatilhos=habilidade["gatilhos"],
                    acoes=habilidade["acoes"]
                )

                print(f"JARVIS: Cadastro: {resultado_adicionar}")

            except TypeError:
                resultado_adicionar = gerenciador.adicionar(habilidade)
                print(f"JARVIS: Cadastro: {resultado_adicionar}")

            progresso["concluidas"].append(nome)
            salvar_json(PROGRESSO, progresso)

            print("JARVIS: APROVADA E SALVA.")

        except Exception as erro:

            print(f"JARVIS: ERRO NO TREINAMENTO: {erro}")

            progresso["falhas"].append({
                "nome": nome,
                "erro": str(erro)
            })

            salvar_json(PROGRESSO, progresso)

    print()
    print("=" * 65)
    print(" TREINAMENTO FINALIZADO")
    print("=" * 65)
    print(f"Concluidas: {len(progresso['concluidas'])}/{len(path)}")
    print(f"Falhas: {len(progresso['falhas'])}")
    print("=" * 65)


if __name__ == "__main__":
    executar_treinamento()
