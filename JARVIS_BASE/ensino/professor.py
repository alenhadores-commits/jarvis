import sys
import json
import inspect
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from habilidades.gerenciador import GerenciadorHabilidades
from habilidades.executor import ExecutorHabilidades


PASTA = BASE / "ensino"
PATH_FILE = PASTA / "path_habilidades.json"
PROGRESSO_FILE = PASTA / "progresso.json"


def salvar(caminho, dados):
    caminho.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def carregar(caminho, padrao):
    if not caminho.exists():
        return padrao

    try:
        return json.loads(
            caminho.read_text(encoding="utf-8-sig")
        )
    except Exception as erro:
        print(f"JARVIS: Erro lendo {caminho.name}: {erro}")
        return padrao


def criar_path():
    path = [
        ("ABRIR GOOGLE", ["abrir google", "abra o google"], "powershell", 'Start-Process "https://www.google.com"', True),
        ("ABRIR NAVEGADOR", ["abrir navegador", "abra o navegador"], "powershell", 'Start-Process "https://www.google.com"', True),
        ("ABRIR CHROME", ["abrir chrome", "abra o chrome"], "abrir_programa", "chrome", True),
        ("ABRIR EDGE", ["abrir edge", "abra o edge"], "abrir_programa", "msedge.exe", True),
        ("ABRIR BLOCO DE NOTAS", ["abrir bloco de notas", "abra o bloco de notas"], "abrir_programa", "notepad.exe", True),
        ("ABRIR CALCULADORA", ["abrir calculadora", "abra a calculadora"], "abrir_programa", "calc.exe", True),
        ("ABRIR EXPLORADOR", ["abrir explorador", "abrir arquivos"], "abrir_programa", "explorer.exe", True),
        ("ABRIR CONFIGURACOES", ["abrir configurações", "abrir configuracoes"], "powershell", 'Start-Process "ms-settings:"', True),
        ("ABRIR GERENCIADOR DE TAREFAS", ["abrir gerenciador de tarefas"], "powershell", "Start-Process taskmgr.exe", True),
        ("ABRIR POWERSHELL", ["abrir powershell"], "powershell", "Start-Process powershell.exe", True),

        ("ABRIR DOCUMENTOS", ["abrir documentos"], "powershell", 'Start-Process "$HOME\\Documents"', True),
        ("ABRIR DOWNLOADS", ["abrir downloads"], "powershell", 'Start-Process "$HOME\\Downloads"', True),
        ("ABRIR DESKTOP", ["abrir desktop", "abrir área de trabalho"], "powershell", 'Start-Process "$HOME\\Desktop"', True),
        ("ABRIR IMAGENS", ["abrir imagens"], "powershell", 'Start-Process "$HOME\\Pictures"', True),
        ("ABRIR VIDEOS", ["abrir vídeos", "abrir videos"], "powershell", 'Start-Process "$HOME\\Videos"', True),
        ("ABRIR MUSICA", ["abrir música", "abrir musica"], "powershell", 'Start-Process "$HOME\\Music"', True),
        ("ABRIR LIXEIRA", ["abrir lixeira"], "powershell", 'Start-Process "shell:RecycleBinFolder"', True),
        ("ABRIR PAINEL DE CONTROLE", ["abrir painel de controle"], "powershell", "Start-Process control.exe", True),
        ("ABRIR CONEXOES DE REDE", ["abrir conexões de rede"], "powershell", 'Start-Process "ncpa.cpl"', True),
        ("ABRIR DISPOSITIVOS", ["abrir dispositivos"], "powershell", 'Start-Process "ms-settings:bluetooth"', True),

        ("MOSTRAR AREA DE TRABALHO", ["mostrar área de trabalho", "mostrar minha área de trabalho"], "combinacao_teclas", "win d", True),
        ("ABRIR JANELA EXECUTAR", ["abrir executar", "abrir run"], "combinacao_teclas", "win r", True),
        ("ABRIR PESQUISA WINDOWS", ["abrir pesquisa", "pesquisar no windows"], "combinacao_teclas", "win s", True),
        ("ALTERNAR JANELAS", ["alternar janelas", "trocar de janela"], "combinacao_teclas", "alt tab", True),
        ("MINIMIZAR JANELA", ["minimizar janela"], "combinacao_teclas", "win down", True),
        ("MAXIMIZAR JANELA", ["maximizar janela"], "combinacao_teclas", "win up", True),
        ("FECHAR JANELA", ["fechar janela", "fechar janela atual"], "combinacao_teclas", "alt f4", True),
        ("ATUALIZAR JANELA", ["atualizar janela"], "combinacao_teclas", "f5", True),
        ("COPIAR", ["copiar"], "combinacao_teclas", "ctrl c", True),
        ("COLAR", ["colar"], "combinacao_teclas", "ctrl v", True),

        ("DESFAZER", ["desfazer"], "combinacao_teclas", "ctrl z", True),
        ("REFAZER", ["refazer"], "combinacao_teclas", "ctrl y", True),
        ("SALVAR", ["salvar", "salvar arquivo"], "combinacao_teclas", "ctrl s", True),
        ("SELECIONAR TUDO", ["selecionar tudo"], "combinacao_teclas", "ctrl a", True),
        ("ABRIR NOVA ABA", ["abrir nova aba", "nova aba"], "combinacao_teclas", "ctrl t", True),
        ("FECHAR ABA", ["fechar aba"], "combinacao_teclas", "ctrl w", True),
        ("REABRIR ABA", ["reabrir aba"], "combinacao_teclas", "ctrl shift t", True),
        ("VOLTAR PAGINA", ["voltar página", "voltar pagina"], "combinacao_teclas", "alt left", True),
        ("AVANCAR PAGINA", ["avançar página", "avancar pagina"], "combinacao_teclas", "alt right", True),
        ("ABRIR HISTORICO", ["abrir histórico", "abrir historico"], "combinacao_teclas", "ctrl h", True),

        ("ABRIR DOWNLOADS NAVEGADOR", ["abrir downloads do navegador"], "combinacao_teclas", "ctrl j", True),
        ("PESQUISAR NA PAGINA", ["pesquisar na página", "pesquisar na pagina"], "combinacao_teclas", "ctrl f", True),
        ("ABRIR NOVA JANELA", ["abrir nova janela"], "combinacao_teclas", "ctrl n", True),
        ("RECARREGAR PAGINA", ["recarregar página", "recarregar pagina"], "combinacao_teclas", "ctrl r", True),
        ("ZOOM MAIS", ["aumentar zoom"], "combinacao_teclas", "ctrl +", True),
        ("ZOOM MENOS", ["diminuir zoom"], "combinacao_teclas", "ctrl -", True),
        ("ZOOM NORMAL", ["zoom normal"], "combinacao_teclas", "ctrl 0", True),
        ("ABRIR YOUTUBE", ["abrir youtube"], "powershell", 'Start-Process "https://www.youtube.com"', True),
        ("ABRIR GMAIL", ["abrir gmail"], "powershell", 'Start-Process "https://mail.google.com"', True),
        ("ABRIR WHATSAPP WEB", ["abrir whatsapp web"], "powershell", 'Start-Process "https://web.whatsapp.com"', True),

        ("PESQUISAR GOOGLE", ["pesquisar no google", "pesquisar google"], "powershell", 'Start-Process "https://www.google.com"', True),
        ("PESQUISAR YOUTUBE", ["pesquisar no youtube", "buscar no youtube"], "powershell", 'Start-Process "https://www.youtube.com"', True),
        ("ABRIR GITHUB", ["abrir github"], "powershell", 'Start-Process "https://github.com"', True),
        ("ABRIR CHATGPT", ["abrir chatgpt"], "powershell", 'Start-Process "https://chatgpt.com"', True),
        ("ABRIR GOOGLE DRIVE", ["abrir google drive"], "powershell", 'Start-Process "https://drive.google.com"', True),
        ("ABRIR GOOGLE MAPS", ["abrir google maps"], "powershell", 'Start-Process "https://maps.google.com"', True),
        ("ABRIR TRADUTOR", ["abrir tradutor"], "powershell", 'Start-Process "https://translate.google.com"', True),
        ("ABRIR WIKIPEDIA", ["abrir wikipedia"], "powershell", 'Start-Process "https://pt.wikipedia.org"', True),
        ("ABRIR REDDIT", ["abrir reddit"], "powershell", 'Start-Process "https://www.reddit.com"', True),
        ("ABRIR AMAZON", ["abrir amazon"], "powershell", 'Start-Process "https://www.amazon.com.br"', True),

        ("ABRIR VS CODE", ["abrir vs code", "abrir vscode"], "abrir_programa", "code", True),
        ("ABRIR TERMINAL", ["abrir terminal"], "powershell", "Start-Process wt.exe", True),
        ("ABRIR CMD", ["abrir cmd"], "abrir_programa", "cmd.exe", True),
        ("ABRIR PYTHON", ["abrir python"], "powershell", "Start-Process python.exe", True),
        ("ABRIR PASTA JARVIS", ["abrir pasta jarvis"], "powershell", f'Start-Process "{BASE}"', True),
        ("EXECUTAR JARVIS", ["executar jarvis", "iniciar jarvis"], "powershell", f'Start-Process powershell.exe -ArgumentList \'-NoExit -Command cd "{BASE}"; python .\\jarvis.py\'', True),
        ("VER PYTHON", ["ver versão do python", "ver versao do python"], "powershell", "python --version", True),
        ("VER PIP", ["ver versão do pip", "ver versao do pip"], "powershell", "python -m pip --version", True),
        ("VER PROCESSOS", ["ver processos"], "powershell", "Get-Process | Select-Object -First 20", True),
        ("VER DISCO", ["ver armazenamento", "ver espaço em disco"], "powershell", "Get-PSDrive -PSProvider FileSystem", True),

        ("VER CPU", ["ver uso da cpu", "ver cpu"], "powershell", "Get-Counter '\\Processor(_Total)\\% Processor Time' -SampleInterval 1 -MaxSamples 1", True),
        ("VER MEMORIA", ["ver uso da memória", "ver uso da memoria", "ver ram"], "powershell", "Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory,TotalVisibleMemorySize", True),
        ("VER SISTEMA", ["ver informações do sistema", "ver informacoes do sistema"], "powershell", "Get-ComputerInfo | Select-Object WindowsProductName,WindowsVersion,OsArchitecture", True),
        ("VER HOST", ["ver nome do computador", "ver computador"], "powershell", "hostname", True),
        ("VER DATA", ["ver data"], "powershell", "Get-Date -Format 'dd/MM/yyyy'", True),
        ("VER HORA", ["ver hora"], "powershell", "Get-Date -Format 'HH:mm:ss'", True),
        ("ABRIR MONITOR DE RECURSOS", ["abrir monitor de recursos"], "powershell", "Start-Process resmon.exe", True),
        ("ABRIR SERVICOS", ["abrir serviços", "abrir servicos"], "powershell", "Start-Process services.msc", True),
        ("ABRIR EVENTOS", ["abrir eventos do windows"], "powershell", "Start-Process eventvwr.msc", True),
        ("ABRIR GERENCIAMENTO DE DISCO", ["abrir gerenciamento de disco"], "powershell", "Start-Process diskmgmt.msc", True),

        ("AUMENTAR VOLUME", ["aumentar volume"], "combinacao_teclas", "volume up", True),
        ("DIMINUIR VOLUME", ["diminuir volume"], "combinacao_teclas", "volume down", True),
        ("SILENCIAR", ["silenciar", "mutar"], "combinacao_teclas", "volume mute", True),
        ("PAUSAR MIDIA", ["pausar mídia", "pausar midia"], "combinacao_teclas", "media play pause", True),
        ("REPRODUZIR MIDIA", ["reproduzir mídia", "reproduzir midia"], "combinacao_teclas", "media play pause", True),
        ("PROXIMA MUSICA", ["próxima música", "proxima musica"], "combinacao_teclas", "media next", True),
        ("MUSICA ANTERIOR", ["música anterior", "musica anterior"], "combinacao_teclas", "media previous", True),
        ("ABRIR SPOTIFY", ["abrir spotify"], "powershell", 'Start-Process "https://open.spotify.com"', True),
        ("ABRIR NETFLIX", ["abrir netflix"], "powershell", 'Start-Process "https://www.netflix.com"', True),
        ("ABRIR PRIME VIDEO", ["abrir prime video"], "powershell", 'Start-Process "https://www.primevideo.com"', True),

        ("TIRAR SCREENSHOT", ["tirar screenshot", "tirar captura de tela"], "combinacao_teclas", "win shift s", True),
        ("ABRIR FERRAMENTA DE CAPTURA", ["abrir ferramenta de captura"], "powershell", "Start-Process snippingtool.exe", True),
        ("ABRIR PAINT", ["abrir paint"], "abrir_programa", "mspaint.exe", True),
        ("ABRIR WORDPAD", ["abrir wordpad"], "powershell", "Start-Process wordpad.exe", True),
        ("ABRIR NOTAS RAPIDAS", ["abrir notas rápidas", "abrir notas rapidas"], "powershell", "Start-Process stikynot.exe", True),
        ("ABRIR CAMERA", ["abrir câmera", "abrir camera"], "powershell", "Start-Process microsoft.windows.camera:", True),
        ("ABRIR BLUETOOTH", ["abrir bluetooth"], "powershell", 'Start-Process "ms-settings:bluetooth"', True),
        ("ABRIR WIFI", ["abrir wifi"], "powershell", 'Start-Process "ms-settings:network-wifi"', True),
        ("ABRIR TELA", ["abrir configurações de tela"], "powershell", 'Start-Process "ms-settings:display"', True),
        ("ABRIR SOM", ["abrir configurações de som"], "powershell", 'Start-Process "ms-settings:sound"', True),

        ("ABRIR WINDOWS UPDATE", ["abrir windows update"], "powershell", 'Start-Process "ms-settings:windowsupdate"', True),
        ("ABRIR CONTAS", ["abrir contas do windows"], "powershell", 'Start-Process "ms-settings:accounts"', True),
        ("ABRIR PERSONALIZACAO", ["abrir personalização"], "powershell", 'Start-Process "ms-settings:personalization"', True),
        ("ABRIR APLICATIVOS", ["abrir aplicativos instalados"], "powershell", 'Start-Process "ms-settings:appsfeatures"', True),
        ("ABRIR PRIVACIDADE", ["abrir privacidade"], "powershell", 'Start-Process "ms-settings:privacy"', True),
        ("ABRIR IDIOMA", ["abrir idioma"], "powershell", 'Start-Process "ms-settings:regionlanguage"', True),
        ("ABRIR ARMAZENAMENTO", ["abrir armazenamento"], "powershell", 'Start-Process "ms-settings:storagesense"', True),
        ("ABRIR RECUPERACAO", ["abrir recuperação"], "powershell", 'Start-Process "ms-settings:recovery"', True),
        ("ABRIR ACESSIBILIDADE", ["abrir acessibilidade"], "powershell", 'Start-Process "ms-settings:easeofaccess"', True),
        ("ABRIR SOBRE O PC", ["abrir sobre o pc", "informações do pc"], "powershell", 'Start-Process "ms-settings:about"', True),

        ("TESTE MULTI ACAO", ["teste multi ação", "teste multi acao"], "abrir_programa", "notepad.exe", True),
        ("FALAR TESTE", ["falar teste", "teste de voz"], "falar", "Teste de treinamento automático concluído, chefe.", True),
        ("ESPERAR", ["testar espera"], "esperar", "1", True),
        ("ABRIR CALENDARIO", ["abrir calendário", "abrir calendario"], "powershell", "Start-Process outlookcal:", True),
        ("ABRIR CALCULADORA WINDOWS", ["abrir calculadora windows"], "abrir_programa", "calc.exe", True),
        ("ABRIR TERMINAL ADMIN", ["abrir terminal administrativo"], "powershell", "Start-Process wt.exe -Verb RunAs", False),
        ("BLOQUEAR COMPUTADOR", ["bloquear computador"], "powershell", "rundll32.exe user32.dll,LockWorkStation", False),
        ("REINICIAR COMPUTADOR", ["reiniciar computador"], "powershell", "Restart-Computer", False),
        ("DESLIGAR COMPUTADOR", ["desligar computador"], "powershell", "Stop-Computer", False),
        ("ESVAZIAR LIXEIRA", ["esvaziar lixeira"], "powershell", "Clear-RecycleBin -Force", False),
    ]

    resultado = []

    for nome, gatilhos, tipo, valor, testavel in path:
        resultado.append({
            "nome": nome,
            "gatilhos": gatilhos,
            "acoes": [
                {
                    "tipo": tipo,
                    "valor": valor
                }
            ],
            "ativa": True,
            "testavel_automaticamente": testavel
        })

    salvar(PATH_FILE, resultado)

    return resultado


def encontrar(gerenciador, gatilhos):
    for gatilho in gatilhos:
        try:
            h = gerenciador.encontrar_cadastrada(gatilho)
            if h:
                return h
        except Exception:
            pass

        try:
            h = gerenciador.encontrar(gatilho)
            if h:
                return h
        except Exception:
            pass

    return None


def cadastrar(gerenciador, habilidade):

    try:
        assinatura = inspect.signature(gerenciador.adicionar)
        parametros = list(assinatura.parameters)

        kwargs = {}

        if "nome" in parametros:
            kwargs["nome"] = habilidade["nome"]

        if "gatilhos" in parametros:
            kwargs["gatilhos"] = habilidade["gatilhos"]

        if "acoes" in parametros:
            kwargs["acoes"] = habilidade["acoes"]

        if "ativa" in parametros:
            kwargs["ativa"] = habilidade.get("ativa", True)

        if kwargs:
            return gerenciador.adicionar(**kwargs)

    except Exception:
        pass

    try:
        return gerenciador.adicionar(habilidade)
    except Exception as erro:
        return f"ERRO_CADASTRO: {erro}"


def executar():

    print("=" * 70)
    print(" JARVIS - PROFESSOR AUTONOMO")
    print("=" * 70)

    path = criar_path()

    progresso = carregar(
        PROGRESSO_FILE,
        {
            "total": len(path),
            "concluidas": [],
            "cadastradas_sem_teste": [],
            "falhas": [],
            "ultima": None
        }
    )

    gerenciador = GerenciadorHabilidades()
    executor = ExecutorHabilidades()

    progresso["total"] = len(path)

    print(f"PATH: {len(path)} habilidades")
    print(f"APROVADAS: {len(progresso['concluidas'])}")
    print(f"CADASTRADAS SEM TESTE: {len(progresso['cadastradas_sem_teste'])}")
    print(f"FALHAS: {len(progresso['falhas'])}")
    print("=" * 70)

    for numero, habilidade in enumerate(path, 1):

        nome = habilidade["nome"]

        if (
            nome in progresso["concluidas"]
            or nome in progresso["cadastradas_sem_teste"]
        ):
            continue

        progresso["ultima"] = nome
        salvar(PROGRESSO_FILE, progresso)

        print()
        print(f"[{numero}/{len(path)}] {nome}")

        existente = encontrar(
            gerenciador,
            habilidade["gatilhos"]
        )

        if existente:

            print("  STATUS: JA EXISTE")

            if not habilidade.get("testavel_automaticamente", True):

                print("  ACAO: PROTEGIDA - NAO EXECUTADA")

                progresso["cadastradas_sem_teste"].append(nome)
                salvar(PROGRESSO_FILE, progresso)

                print("  RESULTADO: CADASTRADA/VALIDADA")
                continue

            print("  TESTE: EXECUTANDO")

            try:
                resultado = executor.executar(existente)

                if (
                    isinstance(resultado, str)
                    and "falhou" not in resultado.lower()
                ):
                    progresso["concluidas"].append(nome)
                    salvar(PROGRESSO_FILE, progresso)

                    print("  RESULTADO: APROVADA")
                else:
                    progresso["falhas"].append({
                        "nome": nome,
                        "motivo": str(resultado)
                    })
                    salvar(PROGRESSO_FILE, progresso)

                    print("  RESULTADO: FALHOU")

            except Exception as erro:

                progresso["falhas"].append({
                    "nome": nome,
                    "motivo": str(erro)
                })

                salvar(PROGRESSO_FILE, progresso)

                print(f"  RESULTADO: ERRO - {erro}")

            continue

        print("  STATUS: NOVA HABILIDADE")

        cadastrada = cadastrar(
            gerenciador,
            habilidade
        )

        if isinstance(cadastrada, str) and cadastrada.startswith("ERRO_CADASTRO"):

            progresso["falhas"].append({
                "nome": nome,
                "motivo": cadastrada
            })

            salvar(PROGRESSO_FILE, progresso)

            print(f"  CADASTRO: {cadastrada}")
            continue

        print("  STATUS: CADASTRADA")

        if not habilidade.get("testavel_automaticamente", True):

            progresso["cadastradas_sem_teste"].append(nome)
            salvar(PROGRESSO_FILE, progresso)

            print("  TESTE: PROTEGIDO")
            print("  RESULTADO: CADASTRADA SEM EXECUCAO")
            continue

        print("  TESTE: EXECUTANDO")

        try:

            resultado = executor.executar(habilidade)

            sucesso = (
                isinstance(resultado, str)
                and "falhou" not in resultado.lower()
                and "erro" not in resultado.lower()
            )

            if sucesso:

                progresso["concluidas"].append(nome)
                salvar(PROGRESSO_FILE, progresso)

                print("  RESULTADO: APROVADA")

            else:

                progresso["falhas"].append({
                    "nome": nome,
                    "motivo": str(resultado)
                })

                salvar(PROGRESSO_FILE, progresso)

                print("  RESULTADO: FALHOU")

        except Exception as erro:

            progresso["falhas"].append({
                "nome": nome,
                "motivo": str(erro)
            })

            salvar(PROGRESSO_FILE, progresso)

            print(f"  RESULTADO: ERRO - {erro}")

    print()
    print("=" * 70)
    print(" TREINAMENTO FINALIZADO")
    print("=" * 70)
    print(f"TOTAL: {len(path)}")
    print(f"APROVADAS: {len(progresso['concluidas'])}")
    print(f"PROTEGIDAS: {len(progresso['cadastradas_sem_teste'])}")
    print(f"FALHAS: {len(progresso['falhas'])}")
    print("=" * 70)


if __name__ == "__main__":
    executar()
