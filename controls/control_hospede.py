from models import model_hospede
from validate_docbr import CPF
from datetime import datetime

validador_cpf = CPF()

#--------------------------------- CADASTRAR HÓSPEDE
def cadastrar_hospede(nome, cpf, telefone, email):

    if not all([nome, cpf, telefone, email]):
        return False, "Todos os campos são obrigatórios."

    if not all(isinstance(campo, str) for campo in [nome, cpf, telefone, email]):
        return False, "Todos os campos devem ser textos."

    if len(nome.strip()) < 2:
        return False, "Nome inválido."

    cpf = cpf.strip()
    if not validador_cpf.validate(cpf):
        return False, "CPF inválido."

    telefone = telefone.strip()
    if len(telefone) < 8:
        return False, "Telefone inválido."

    email = email.strip()
    if "@" not in email:
        return False, "Inválido: falta @."
    elif "." not in email:
        return False, "Inválido: falta '.'."


    return model_hospede.registrar_hospede(
        nome.strip(), cpf, telefone, email
    )

#--------------------------------- LISTAR HÓSPEDES
def listar_hospedes():
    return model_hospede.buscar_hospedes()


#--------------------------------- BUSCAR HÓSPEDE POR CPF
def buscar_hospede_por_cpf(cpf):
    if not isinstance(cpf, str) or not cpf.strip():
        return False, "CPF não informado."

    cpf = cpf.strip()
    if not validador_cpf.validate(cpf):
        return False, "CPF inválido."

    return model_hospede.buscar_hospede_por_cpf(cpf)


#--------------------------------- BUSCAR HÓSPEDES POR NOME
def buscar_hospede_por_nome(nome):
    if not isinstance(nome, str) or len(nome.strip()) < 2:
        return False, "Nome inválido."

    return model_hospede.buscar_hospede_por_nome(nome.strip())


# ATUALIZAÇÕES DE DADOS -------------------------------------------
#--------------------------------- ATUALIZAR NOME
def atualizar_nome(nome, id):
    if not isinstance(nome, str) or len(nome.strip()) < 2:
        return False, "Nome inválido."

    if not isinstance(id, int) or id <= 0:
        return False, "ID inválido."

    return model_hospede.atualizar_nome(nome.strip(), id)


#--------------------------------- ATUALIZAR CPF
def atualizar_cpf(cpf, id):
    if not isinstance(cpf, str) or not cpf.strip():
        return False, "CPF não informado."

    cpf = cpf.strip()
    if not validador_cpf.validate(cpf):
        return False, "CPF inválido."

    if not isinstance(id, int) or id <= 0:
        return False, "ID inválido."

    return model_hospede.atualizar_cpf(cpf, id)


#--------------------------------- ATUALIZAR TELEFONE
def atualizar_telefone(telefone, id):
    if not isinstance(telefone, str) or len(telefone.strip()) < 8:
        return False, "Telefone inválido."

    if not isinstance(id, int) or id <= 0:
        return False, "ID inválido."

    return model_hospede.atualizar_telefone(telefone.strip(), id)


#--------------------------------- ATUALIZAR EMAIL
def atualizar_email(email, id):
    if not isinstance(email, str) or not email.strip():
        return False, "E-mail não informado."

    email = email.strip()
    if "@" not in email:
        return False, "Inválido: falta @."
    elif "." not in email:
        return False, "Inválido: falta '.'."

    if not isinstance(id, int) or id <= 0:
        return False, "ID inválido."

    return model_hospede.atualizar_email(email, id)


#--------------------------------- ATUALIZAR DATA DE NASCIMENTO
def atualizar_data_nascimento(data, id):
    if not isinstance(data, str) or not data.strip():
        return False, "Data não informada."

    try:
        datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        return False, "Data inválida. Use DD/MM/AAAA."

    if not isinstance(id, int) or id <= 0:
        return False, "ID inválido."

    return model_hospede.atualizar_data_nascimento(data.strip(), id)


#--------------------------------- ATUALIZAR CEP
def atualizar_cep(cep, id):
    if not isinstance(cep, str) or not cep.strip():
        return False, "CEP não informado."

    cep = cep.strip().replace("-","")
    if len(cep) != 8 or not cep.isdigit():
        return False, "CEP inválido."

    if not isinstance(id, int) or id <= 0:
        return False, "ID inválido."

    return model_hospede.atualizar_cep(cep, id)


#--------------------------------- ATUALIZAR RESIDÊNCIA
def atualizar_residencia(residencia, id):
    if not isinstance(residencia, str) or not residencia.strip():
        return False, "Residência não informada."

    if not isinstance(id, int) or id <= 0:
        return False, "ID inválido."

    return model_hospede.atualizar_residencia(residencia.strip(), id)


#--------------------------------- ATUALIZAR BAIRRO
def atualizar_bairro(bairro, id):

    if not isinstance(bairro, str) or not bairro.strip():
        return False, "Bairro não informado."

    if not isinstance(id, int) or id <= 0:
        return False, "ID inválido."

    return model_hospede.atualizar_bairro(bairro.strip(), id)


#--------------------------------- ATUALIZAR CIDADE
def atualizar_cidade(cidade, id):

    if not isinstance(cidade, str) or not cidade.strip():
        return False, "Cidade não informada."

    if not isinstance(id, int) or id <= 0:
        return False, "ID inválido."

    return model_hospede.atualizar_cidade(cidade.strip(), id)


#--------------------------------- ATUALIZAR ESTADO
def atualizar_estado(estado, id):

    if not isinstance(estado, str) or not estado.strip():
        return False, "Estado não informado."

    if not isinstance(id, int) or id <= 0:
        return False, "ID inválido."

    return model_hospede.atualizar_estado(estado.strip(), id)


#--------------------------------- ATUALIZAR PAÍS
def atualizar_pais(pais, id):

    if not isinstance(pais, str) or not pais.strip():
        return False, "País não informado."

    if not isinstance(id, int) or id <= 0:
        return False, "ID inválido."

    return model_hospede.atualizar_pais(pais.strip(), id)


#--------------------------------- EXCLUIR HÓSPEDE
def excluir_hospede(id):
    if not isinstance(id, int) or id <= 0 :
        return False, "ID inválido."
    
    return model_hospede.excluir_hospede(id)

