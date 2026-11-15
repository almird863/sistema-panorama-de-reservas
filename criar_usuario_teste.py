"""
Script utilitário para criar um usuário de teste no banco de dados
e listar as tabelas/usuários existentes.
Rode no terminal:
    python criar_usuario_teste.py
"""
import sqlite3
import os

DB_PATH = os.path.join("databank", "sistema-hotelaria.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Verifica quais tabelas existem
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tabelas = [t[0] for t in cursor.fetchall()]
print(f"📦 Tabelas existentes no banco: {tabelas}")

# 2. Se a tabela Clientes existir (usada pelo login atual)
if "Clientes" in tabelas:
    try:
        from argon2 import PasswordHasher
        ph = PasswordHasher()
        senha_hash = ph.hash("123456")
    except ImportError:
        # Fallback sem argon2 se não tiver
        senha_hash = "123456"

    cpf_teste = "12345678900"
    nome_teste = "Recepcionista Teste"

    cursor.execute("SELECT id FROM Clientes WHERE cpf = ?", (cpf_teste,))
    existente = cursor.fetchone()

    if existente:
        cursor.execute("UPDATE Clientes SET senha = ? WHERE cpf = ?", (senha_hash, cpf_teste))
        conn.commit()
        print(f"✅ Usuário atualizado na tabela Clientes:")
        print(f"   CPF: {cpf_teste}")
        print(f"   Senha: 123456")
    else:
        cursor.execute(
            "INSERT INTO Clientes (nome, idade, cpf, cidade_origem, senha) VALUES (?, ?, ?, ?, ?)",
            (nome_teste, 30, cpf_teste, "São Paulo", senha_hash)
        )
        conn.commit()
        print(f"✅ Usuário criado na tabela Clientes com sucesso!")
        print(f"   CPF: {cpf_teste}")
        print(f"   Senha: 123456")

# 3. Se a tabela Administradores existir (cenário v1.1)
if "Administradores" in tabelas:
    cursor.execute("SELECT id FROM Administradores WHERE usuario = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO Administradores (usuario, senha) VALUES (?, ?)", ("admin", "admin123"))
        conn.commit()
        print(f"✅ Administrador criado na tabela Administradores:")
        print(f"   Usuário: admin | Senha: admin123")

conn.close()
