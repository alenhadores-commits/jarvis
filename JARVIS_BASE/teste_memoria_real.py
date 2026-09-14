# -*- coding: utf-8 -*-

from identidade import obter_identidade
from memoria import criar_tabelas
from gerenciador_memoria import GerenciadorMemoria


identidade = obter_identidade()

user_id = identidade["user_id"]
nome = identidade.get("nome", "Alex")


print("USER_ID:", user_id)
print("NOME:", nome)

criar_tabelas()

memoria = GerenciadorMemoria(
    user_id
)

memoria.registrar_usuario(
    nome
)

memoria.lembrar_preferencia(
    "O usuário prefere ser chamado de chefe.",
    importancia=10
)

print()
print("MEMÓRIA ATUAL:")
print(memoria.contexto_textual())