from models.model_adm import (
    inserir_administrador, buscar_administrador, buscar_administrador_por_usuario,
    atualizar_senha, atualizar_usuario, deletar_administrador
)

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

# CRIPTOGRAFIA
ph = PasswordHasher()

def gerar_hash_senha(senha):
    return ph.hash(senha)


#------------------------------------ CADASTRO ADMINISTRADOR
def CadastrarAdm(usuario, senha):
    if not usuario.strip():
        return False, "O usuário é obrigatório."

    if not senha:
        return False, "A senha é obrigatória."

    if len(senha) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."

    encontrado, adm = buscar_administrador_por_usuario(usuario)
    if not encontrado:
        return False, "Erro ao consultar administrador."

    if adm is not None:
        return False, "Esse usuário já está cadastrado."

    senha_hash = gerar_hash_senha(senha)
    return inserir_administrador(usuario, senha_hash)


#------------------------------------ AUTENTICAR ADMINISTRADOR
def AutenticarAdm(usuario, senha):
    if not usuario.strip():
        return False, "O usuário é obrigatório."

    if not senha:
        return False, "A senha é obrigatória."

    encontrado, adm = buscar_administrador_por_usuario(usuario)
    if not encontrado:
        return False, "Erro ao consultar administrador."

    if adm is None:
        return False, "Administrador não encontrado."

    try:
        ph.verify(adm[2], senha)
        return True, adm[1]
    except VerifyMismatchError:
        return False, "Senha incorreta."
    except VerificationError:
        return False, "Não foi possível verificar a senha."
    except Exception:
        return False, "Erro ao verificar a senha."


#------------------------------------ ATUALIZAR ADMINISTRADOR
def AtualizarUsuario(usuario, id_adm):
    if not usuario.strip():
        return False, "Usuário é obrigatório."

    encontrado, adm = buscar_administrador_por_usuario(usuario)
    if not encontrado:
        return False, "Erro ao consultar administrador."

    if adm is not None and adm[0] != id_adm:
        return False, "Esse usuário já está cadastrado."

    return atualizar_usuario(usuario, id_adm)


#------------------------------------ ATUALIZAR SENHA
def AtualizarSenha(senha, id_adm):
    if not senha:
        return False, "A senha é obrigatória."

    if len(senha) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres."

    senha_hash = gerar_hash_senha(senha)
    return atualizar_senha(senha_hash, id_adm)


#------------------------------------ LISTAR ADMINISTRADORES
def ListarAdm():
    encontrado, administradores = buscar_administrador()

    if not encontrado:
        return False, "Erro ao buscar administradores."

    return True, administradores


#------------------------------------ EXCLUIR ADMINISTRADORES
def DeletarAdm(id_adm):
    try:
        id_adm = int(id_adm)
    except (ValueError, TypeError):
        return False, "ID do administrador inválido."

    if id_adm <= 0:
        return False, "ID do administrador inválido."

    return deletar_administrador(id_adm)

