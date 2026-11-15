# ======================================================================
# [MOCK] AJUSTE TEMPORÁRIO PARA USABILIDADE DA VIEW:
# Suporte a múltiplos cenários de banco de dados (Clientes vs Hospedes vs Administradores)
# para garantir que o login na View funcione independente da tabela ativa no SQLite.
# ======================================================================
import sqlite3

def buscar_cliente_por_cpf(cpf):
    """[MOCK] Busca o usuário em Clientes, Hospedes ou Administradores."""
    try:
        conn = sqlite3.connect('databank/sistema-hotelaria.db')
        cur = conn.cursor()
        
        # 1. Tenta buscar na tabela Clientes
        try:
            cur.execute("SELECT id, nome, idade, cpf, cidade_origem, senha FROM Clientes WHERE cpf = ?", (cpf,))
            row = cur.fetchone()
            if row:
                conn.close()
                return row
        except sqlite3.OperationalError:
            pass

        # 2. Tenta buscar na tabela Administradores (usuario = cpf ou 'admin')
        try:
            cur.execute("SELECT id, usuario, 0, usuario, '', senha FROM Administradores WHERE usuario = ?", (cpf,))
            row = cur.fetchone()
            if row:
                conn.close()
                return row
        except sqlite3.OperationalError:
            pass

        # 3. Tenta buscar na tabela Hospedes
        try:
            cur.execute("SELECT id, nome, 0, cpf, cidade, '' FROM Hospedes WHERE cpf = ?", (cpf,))
            row = cur.fetchone()
            if row:
                conn.close()
                return row
        except sqlite3.OperationalError:
            pass

        conn.close()
        return None
    except Exception as e:
        print(f"[MOCK] Erro na busca de usuário: {e}")
        return None

def inserir_db_cliente(nome, idade, cpf, cidade_origem, senha):
    try:
        conn = sqlite3.connect('databank/sistema-hotelaria.db')
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS Clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    idade INTEGER,
                    cpf TEXT UNIQUE,
                    cidade_origem TEXT,
                    senha TEXT)''')
        cur.execute("INSERT INTO Clientes (nome, idade, cpf, cidade_origem, senha) VALUES (?, ?, ?, ?, ?)",
                    (nome, idade, cpf, cidade_origem, senha))
        conn.commit()
        conn.close()
        return True, "Cliente inserido com sucesso"
    except Exception as e:
        return False, str(e)
# ======================================================================

from validate_docbr import CPF
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

#------------------- CRIPTOGRAFIA ----------------------------
ph = PasswordHasher()
def gerar_hash_senha(senha):
    return ph.hash(senha)

#------------------- FUNÇÃO DE CADASTRO ----------------------------
def CadastrarCliente(nome, idade, cpf, cidade_origem, senha):
    print("ENTRAMOS NO CONTROL")
    """
    Validar dados da View e solicitar cadastro ao Model

    argumentos:
        nome do cliente - string
        idade do cliente - integer
        cpf - string 
        cidade_origem - string
        senha - string

    o padrão é retornar uma tupla:
        return(sucesso, mensagem) - para puxar um messagebox na view
    """

    # verificação para campos vazios
    if not nome.strip():
        return False, "O nome é obrigatório."

    if not cpf.strip():
        return False, "O CPF é obrigatório"

    if not cidade_origem.strip():
        return False, "A cidade de origem é obrigatória."

    if not senha:
        return False, "A senha é obrigatória."

    # verificação CPF válido
    documento = CPF()
    
    if not documento.validate(cpf):
        return False, "CPF inválido."

    # verificação para idade
    # 1 - tipo errado
    try:
        idade = int(idade)
    except (ValueError, TypeError):
        return False, "A idade deve ser um número inteiro."

    # 2 - nula
    if idade <= 0:
        return False, "A idade deve ser maior que zero."
    # 3 - idade impossivel
    elif idade > 130:
        return False, "A idade deve ser menor que 130."
    #=================== INSERINDO CLIENTE =====================
    try:
        senha_criptografada = gerar_hash_senha(senha)

        a, b = inserir_db_cliente(nome, idade, cpf, cidade_origem, senha_criptografada)
        if a:
            print(b)
            return True, "Sucesso ao cadastrar cliente."
        else:
            print(b)
    except Exception as e:
        return False, f"Erro, ao cadastrar cliente: {e}"


#------------------- FUNÇÃO DE LOGIN ----------------------------
def AutenticarCliente(cpf, senha):
    # Buscar cliente no banco de dados
    cliente = buscar_cliente_por_cpf(cpf)

    # verificar se cliente existe
    if cliente is None:
        return False, "CPF não encontrado."

    senha_armazenada = cliente[5] if len(cliente) > 5 else ""

    # Se a senha no banco for texto puro (ex: admin123 ou mock)
    if senha_armazenada == senha:
        return True, "Login realizado com sucesso."

    try:
        ph.verify(senha_armazenada, senha)
    except VerifyMismatchError:
        return False, "Senha incorreta."
    except VerificationError:
        # Fallback de comparação direta
        if senha_armazenada == senha:
            return True, "Login realizado com sucesso."
        return False, "Não foi possível verificar a senha."

    return True, "Login realizado com sucesso."


# ----------------------------------------------------------------------
# [MOCK] NOVO: classe fina usada pela tela "Minha conta" (views/view_usuarios.py),
# que chama control_cliente.ControlCliente().buscar_por_cpf(cpf) em vez da
# função solta. Só repassa para buscar_cliente_por_cpf, que já existia e
# devolve a tupla (id, nome, idade, cpf, cidade_origem, senha).
# ----------------------------------------------------------------------
class ControlCliente:
    def buscar_por_cpf(self, cpf):
        return buscar_cliente_por_cpf(cpf)