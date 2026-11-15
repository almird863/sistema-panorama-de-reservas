import sqlite3
import os

DB_PATH = os.path.join("databank", "sistema-hotelaria.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("--- DIAGNÓSTICO DO BANCO DE DADOS ---")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tabelas = [t[0] for t in cursor.fetchall()]
print(f"Tabelas encontradas: {tabelas}\n")

for tab in tabelas:
    cursor.execute(f"PRAGMA table_info({tab});")
    colunas = [c[1] for c in cursor.fetchall()]
    cursor.execute(f"SELECT COUNT(*) FROM {tab};")
    qtd = cursor.fetchone()[0]
    print(f"Tabela '{tab}' ({qtd} registros) -> Colunas: {colunas}")
    if qtd > 0:
        cursor.execute(f"SELECT * FROM {tab} LIMIT 3;")
        for row in cursor.fetchall():
            print(f"   Exemplo: {row}")
    print()

conn.close()
