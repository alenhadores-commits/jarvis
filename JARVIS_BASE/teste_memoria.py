# -*- coding: utf-8 -*-

from memoria import (
    criar_tabelas,
    salvar_usuario,
    salvar_memoria,
    consultar_memoria,
    buscar_usuario,
)


USER_ID = "teste-user-001"


print("CRIANDO TABELAS...")
criar_tabelas()

print("SALVANDO USUÁRIO...")
salvar_usuario(
    USER_ID,
    "Alex"
)

print("SALVANDO MEMÓRIA...")
salvar_memoria(
    user_id=USER_ID,
    tipo="PREFERENCIA",
    duracao="PERMANENTE",
    conteudo="O usuário prefere ser chamado de chefe.",
    importancia=8
)

print()
print("USUÁRIO:")
print(buscar_usuario(USER_ID))

print()
print("MEMÓRIAS DO USUÁRIO:")
memorias = consultar_memoria(USER_ID)

for memoria in memorias:
    print(memoria)

print()
print("TESTE CONCLUÍDO.")