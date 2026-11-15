from models.model_reserva import (
    inserir_db_reserva,
    buscar_db_reserva,
    listar_db_reservas,
    atualizar_db_reserva,
    deletar_db_reserva,
    # NOVO: check-in / check-out
    adicionar_coluna_checkin,
    listar_db_reservas_para_checkin,
    listar_db_reservas_hospedadas,
    listar_db_reservas_concluidas,
    marcar_checkin_db,
    marcar_checkout_db,
)
from models.model_uh import atualizar_db_apto

#-------------------------------------------------- CADASTRAR RESERVA
def CadastrarReserva(id_cliente, id_apto, data_entrada, data_saida, qt_pessoas):
    try:
        # validar preenchimento
        campos = [id_cliente, id_apto, data_entrada, data_saida, qt_pessoas]
        
        if any(campo is None or not str(campo).strip() for campo in campos):
            return False, "Preencha todos os campos."

        # conversão
        id_cliente = int(id_cliente)
        id_apto = int(id_apto)
        qt_pessoas = int(qt_pessoas)

        if id_cliente <= 0 or id_apto <= 0 or qt_pessoas <= 0:
            return False, "IDs e quantidade de pessoas devem ser positivos."

        # inserção no banco de dados
        resultado, valor = inserir_db_reserva(
            id_cliente, id_apto,
            data_entrada, data_saida,
            qt_pessoas)

        if resultado:
            resultado, valor = atualizar_db_apto("vago", 0, id_apto)
            
            return True, f"Reserva cadastrada! Valor total: R${valor:.2f}"
        return False, "Não foi possível cadastrar a reserva."

    except ValueError as erro:
        return False, str(erro)
    except Exception as erro:
        return False, f"Erro ao cadastrar reserva: {erro}"


# ----------------------------------------------------------------------
# NOVO: Check-in / Check-out
# ----------------------------------------------------------------------

def ListarReservasParaCheckin():
    """Reservas aguardando o hóspede chegar (ainda não fizeram check-in)."""
    adicionar_coluna_checkin()  # garante que a coluna existe, mesmo em bancos antigos
    return listar_db_reservas_para_checkin()


def ListarReservasHospedadas():
    """Reservas com o hóspede já no hotel (já fizeram check-in, aguardando check-out)."""
    return listar_db_reservas_hospedadas()


def ListarReservasConcluidas():
    """Reservas já finalizadas (check-out feito)."""
    return listar_db_reservas_concluidas()


def FazerCheckin(id_reserva):
    """Marca a chegada do hóspede. Retorna (sucesso: bool, mensagem: str)."""
    try:
        ok = marcar_checkin_db(id_reserva)
        if ok:
            return True, "Check-in realizado com sucesso!"
        return False, "Não foi possível fazer o check-in (reserva não encontrada ou já processada)."
    except Exception as erro:
        return False, f"Erro ao fazer check-in: {erro}"


def FazerCheckout(id_reserva):
    """Marca a saída do hóspede e encerra a reserva. Retorna (sucesso: bool, mensagem: str)."""
    try:
        ok = marcar_checkout_db(id_reserva)
        if ok:
            return True, "Check-out realizado com sucesso!"
        return False, "Não foi possível fazer o check-out (reserva não encontrada ou check-in não feito)."
    except Exception as erro:
        return False, f"Erro ao fazer check-out: {erro}"
