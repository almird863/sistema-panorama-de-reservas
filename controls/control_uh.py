from models.model_uh import (
    listar_uh, buscar_uh,
    inserir_uh, atualizar_uh_status,
    deletar_uh
)

# -------------------------------------- CADASTRAR UH
def CadastrarUH(numeracao, vm, vc, acc):
    if not numeracao:
        return False, "A numeração é obrigatória."

    try:
        numeracao = int(numeracao)
    except (ValueError, TypeError):
        return False, "A numeração deve ser um número inteiro."

    if numeracao <= 0:
        return False, "A numeração deve ser positiva."

    for valor in (vm, vc, acc):
        if valor not in (0, 1, False, True):
            return False, "As características devem ser 0 ou 1."

    encontrado, uh = buscar_uh(numeracao)

    if not encontrado:
        return False, "Erro ao consultar unidade habitacional."

    if uh is not None:
        return False, "Essa unidade já está cadastrada."

    return inserir_uh(numeracao, vm, vc, acc)

# -------------------------------------- ATUALIZAR UH
def AtualizarStatusUH(status, numeracao):
    status_validos = (
        "Livre e limpa",
        "Em limpeza",
        "Hóspede na casa",
        "Reservado",
        "Indisponível"
    )

    if status not in status_validos:
        return False, "Status inválido."

    if not numeracao:
        return False, "A numeração é obrigatória."

    try:
        numeracao = int(numeracao)
        if numeracao <= 0:
            return False, "A numeração deve ser positiva."

    except (ValueError, TypeError):
        return False, "Numeração inválida."

    encontrado, uh = buscar_uh(numeracao)

    if not encontrado:
        return False, "Erro ao consultar unidade habitacional."

    if uh is None:
        return False, "Unidade habitacional não encontrada"

    return atualizar_uh_status(status, numeracao)


# -------------------------------------- LISTAR UH
def ListarUH():
    encontrado, unidades = listar_uh()

    if not encontrado:
        return False, "Erro ao listar unidades habitacionais."

    return True, unidades


# -------------------------------------- LISTAR UH
def BuscarUH(numeracao):
    if not numeracao:
        return False, "A numeração é obrigatória."

    try:
        numeracao = int(numeracao)
        if numeracao <= 0:
            return False, "A numeração deve ser positiva."
    except (ValueError, TypeError):
        return False, "Numeração inválida."

    encontrado, uh = buscar_uh(numeracao)

    if not encontrado:
        return False, "Erro ao buscar unidade habitacional."

    if uh is None:
        return False, "Unidade habitacional não encontrada"

    return True, uh


# -------------------------------------- DELETAR UH
def DeletarUH(id_uh):
    try:
        id_uh = int(id_uh)
    except (ValueError, TypeError):
        return False, "ID da unidade habitacional inválido."

    if id_uh <= 0:
        return False, "ID inválido."

    return deletar_uh(id_uh)

