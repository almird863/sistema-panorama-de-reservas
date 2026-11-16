from models.model_estadia import (
    inserir_estadia,
    buscar_estadia,
    buscar_estadia_por_hospede,
    buscar_estadias_por_uh,
    buscar_estadia_por_checkin,
    buscar_estadia_por_checkout,
    buscar_estadia_por_status,
    atualizar_checkin_data_e_hora,
    atualizar_checkout_data_e_hora,
    atualizar_estadia_status,
    atualizar_estadia_pessoas
)

#------------------------------------------------ CADASTRAR ESTADIA
def CadastrarEstadia(id_hospede, id_uh, qt_pessoas):
    try:
        id_hospede = int(id_hospede)
        id_uh = int(id_uh)
        qt_pessoas = int(qt_pessoas)
    except (ValueError, TypeError):
        return False, "IDs e quantidade de pessoas devem ser números inteiros."

    if id_hospede <= 0 or id_uh <= 0:
        return False, "Os IDs devem ser positivos."

    if qt_pessoas <= 0:
        return False, "A quantidade de pessoas deve ser positiva."

    return inserir_estadia(id_hospede, id_uh, qt_pessoas)


#------------------------------------------------ LISTAR ESTADIA
def ListarEstadias():
    encontrado, estadias = buscar_estadia()
    if not encontrado:
        return False, "Erro ao listar estadias."

    return True, estadias


