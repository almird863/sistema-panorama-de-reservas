from dataclasses import dataclass  # [MOCK] Suporte à camada de reservas em objetos.

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
    buscar_db_reservas_cliente,  # [MOCK] Consulta das reservas da tela Minha Conta.
)


def CadastrarReserva(id_cliente, id_apto, data_entrada, data_saida, qt_pessoas):
    try:
        if not all([id_cliente, id_apto, data_entrada, data_saida, qt_pessoas]):
            return False, "Preencha todos os campos."

        qt_pessoas = int(qt_pessoas)
        resultado, valor = inserir_db_reserva(
            id_cliente, id_apto,
            data_entrada, data_saida,
            qt_pessoas
        )

        if resultado:
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


# ----------------------------------------------------------------------
# [MOCK] NOVO: ControlReserva — classe usada pela tela "Minha conta"
# (views/view_usuarios.py chama ControlReserva().buscar_reserva_ativa(id)
# e .buscar_historico(id), esperando OBJETOS com .id, .apartamento,
# .data_entrada, .data_saida, .status, .valor — não tuplas cruas do banco).
# As funções soltas acima (CadastrarReserva, FazerCheckin, etc.) continuam
# existindo normalmente; isso aqui é só uma camada por cima para quem prefere
# objetos.
# ----------------------------------------------------------------------

@dataclass
class Reserva:
    id: int
    apartamento: str
    data_entrada: str
    data_saida: str
    status: str
    valor: float
    checkin_feito: bool = False


def _linha_para_reserva(linha):
    (id_reserva, id_cliente, id_apto, data_entrada, data_saida,
     qt_pessoas, valor, status, checkin_feito, numero_apto) = linha
    return Reserva(
        id=id_reserva,
        apartamento=numero_apto if numero_apto is not None else f"(ID {id_apto})",
        data_entrada=data_entrada,
        data_saida=data_saida,
        status=status,
        valor=valor,
        checkin_feito=bool(checkin_feito),
    )


class ControlReserva:
    """Camada em objetos (Reserva) por cima das reservas de um cliente."""

    def buscar_reserva_ativa(self, id_cliente):
        """Devolve a reserva 'em aberto' mais recente do cliente, ou None."""
        linhas = buscar_db_reservas_cliente(id_cliente)
        for linha in linhas:
            reserva = _linha_para_reserva(linha)
            if reserva.status == "em aberto":
                return reserva
        return None

    def buscar_historico(self, id_cliente):
        """Reservas já encerradas (concluídas ou canceladas) do cliente."""
        linhas = buscar_db_reservas_cliente(id_cliente)
        return [
            _linha_para_reserva(linha) for linha in linhas
            if _linha_para_reserva(linha).status != "em aberto"
        ]