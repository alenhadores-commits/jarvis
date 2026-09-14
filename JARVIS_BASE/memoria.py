# -*- coding: utf-8 -*-

import os

os.environ["PGCLIENTENCODING"] = "WIN1252"

import psycopg2
from psycopg2.extras import RealDictCursor


# ==========================================================
# CONFIGURAÇÃO DO BANCO DE MEMÓRIA DO JARVIS
# ==========================================================

DB_HOST = "localhost"
DB_PORT = 5433
DB_NAME = "jarvis"
DB_USER = "jarvis"
DB_PASSWORD = "jarvis123"


# ==========================================================
# CONEXÃO
# ==========================================================

def conectar():

    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


# ==========================================================
# TESTAR CONEXÃO
# ==========================================================

def testar_conexao():

    conexao = None

    try:

        conexao = conectar()

        with conexao.cursor() as cursor:

            cursor.execute(
                "SELECT 1;"
            )

            resultado = cursor.fetchone()

        return resultado[0] == 1

    finally:

        if conexao is not None:
            conexao.close()


# ==========================================================
# CRIAR ESTRUTURA
# ==========================================================

def criar_tabelas():

    conexao = None

    try:

        conexao = conectar()

        with conexao.cursor() as cursor:

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS jarvis_users (
                    user_id TEXT PRIMARY KEY,
                    nome TEXT,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS jarvis_memory (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    duracao TEXT NOT NULL,
                    conteudo TEXT NOT NULL,
                    importancia INTEGER DEFAULT 0,
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT fk_jarvis_memory_user
                        FOREIGN KEY (user_id)
                        REFERENCES jarvis_users(user_id)
                        ON DELETE CASCADE
                );
                """
            )

            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                idx_jarvis_memory_unica
                ON jarvis_memory(
                    user_id,
                    tipo,
                    duracao,
                    conteudo
                );
                """
            )

        conexao.commit()

    finally:

        if conexao is not None:
            conexao.close()


# ==========================================================
# SALVAR USUÁRIO
# ==========================================================

def salvar_usuario(user_id, nome=None):

    conexao = None

    try:

        conexao = conectar()

        with conexao.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO jarvis_users(
                    user_id,
                    nome
                )
                VALUES(
                    %s,
                    %s
                )
                ON CONFLICT(user_id)
                DO UPDATE SET
                    nome = COALESCE(
                        EXCLUDED.nome,
                        jarvis_users.nome
                    ),
                    atualizado_em = CURRENT_TIMESTAMP;
                """,
                (
                    user_id,
                    nome
                )
            )

        conexao.commit()

    finally:

        if conexao is not None:
            conexao.close()


# ==========================================================
# BUSCAR USUÁRIO
# ==========================================================

def buscar_usuario(user_id):

    conexao = None

    try:

        conexao = conectar()

        with conexao.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT
                    user_id,
                    nome,
                    criado_em,
                    atualizado_em
                FROM jarvis_users
                WHERE user_id = %s;
                """,
                (user_id,)
            )

            return cursor.fetchone()

    finally:

        if conexao is not None:
            conexao.close()


# ==========================================================
# SALVAR MEMÓRIA
# ==========================================================

def salvar_memoria(
    user_id,
    tipo,
    duracao,
    conteudo,
    importancia=0
):

    conexao = None

    try:

        conexao = conectar()

        with conexao.cursor() as cursor:

            cursor.execute(
                """
                INSERT INTO jarvis_memory(
                    user_id,
                    tipo,
                    duracao,
                    conteudo,
                    importancia
                )
                VALUES(
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT(
                    user_id,
                    tipo,
                    duracao,
                    conteudo
                )
                DO UPDATE SET
                    importancia = GREATEST(
                        jarvis_memory.importancia,
                        EXCLUDED.importancia
                    ),
                    atualizado_em = CURRENT_TIMESTAMP;
                """,
                (
                    user_id,
                    tipo,
                    duracao,
                    conteudo,
                    importancia
                )
            )

        conexao.commit()

        return True

    finally:

        if conexao is not None:
            conexao.close()


# ==========================================================
# CONSULTAR MEMÓRIAS DO USUÁRIO
# ==========================================================

def consultar_memoria(
    user_id,
    limite=50
):

    conexao = None

    try:

        conexao = conectar()

        with conexao.cursor(
            cursor_factory=RealDictCursor
        ) as cursor:

            cursor.execute(
                """
                SELECT
                    id,
                    user_id,
                    tipo,
                    duracao,
                    conteudo,
                    importancia,
                    criado_em,
                    atualizado_em
                FROM jarvis_memory
                WHERE user_id = %s
                ORDER BY
                    importancia DESC,
                    atualizado_em DESC
                LIMIT %s;
                """,
                (
                    user_id,
                    limite
                )
            )

            return cursor.fetchall()

    finally:

        if conexao is not None:
            conexao.close()