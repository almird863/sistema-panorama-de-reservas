"""
View de Reservas - Sistema de Reservas - Hotel
Compatível tanto como tela embutida (TelaBase no menu principal)
quanto executável de forma independente para testes.

Layout (v1.1 - cenário real de recepção, 10 quartos):
- Cabeçalho: ícone + título "Reserva de Quartos" + legenda de status
  (Disponível / Ocupado / Indisponível)
- Painel Esquerdo: "Quartos (10)" - grade de cards (5 colunas x 2 linhas),
  cada card com foto do quarto, número e status (bolinha + rótulo colorido)
- Painel Direito: "Calendário" - mês com navegação (◀ ▶); ao selecionar um
  quarto na grade, os DIAS do mês ficam pintados com a cor do status daquele
  quarto naquele dia (verde = disponível, vermelho = ocupado, cinza = indisponível)
- Rodapé: barra de informação + botão "Nova Reserva" (habilita só quando um
  quarto DISPONÍVEL está selecionado)

----------------------------------------------------------------------
NOTA IMPORTANTE SOBRE OS DADOS (ler antes de mexer) ---------------------
----------------------------------------------------------------------
O status "Indisponível" (limpeza/manutenção) AINDA NÃO EXISTE no banco:
`model_apto.py` só tem a coluna `vago` (0/1 = ocupado/disponível) e não
existe nenhuma tabela de manutenção/limpeza. Por isso, por decisão do
Wallace (14/11/2026), o status cinza está MOCKADO localmente nesta tela
através de `QUARTOS_INDISPONIVEIS_MOCK` logo abaixo. Quando o colega
responsável por `models`/`controls` adicionar suporte real a esse status
(ex.: uma coluna `status` em Apartamentos, ou uma tabela de manutenção),
troque `_status_quarto()` e `_status_dia()` para consultar o banco de
verdade e remova o mock.

Já o status verde/vermelho (disponível/ocupado) É real: vem de
`model_apto.listar_aptos()` (campo `vago`) e, no calendário, dia a dia,
de `model_reserva.listar_db_reservas()` (intervalo `data_entrada` /
`data_saida` de cada reserva em aberto daquele quarto).
"""

import calendar
from datetime import date, datetime, timedelta
from tkinter import messagebox
import customtkinter as ctk
from views.componentes import centralizar_janela

from views.componentes import (
    AZUL_ESCURO, AZUL_HOVER, LARANJA, LARANJA_HOVER, FUNDO_DIREITO,
    BORDA_CAMPO, TEXTO_CINZA, carregar_imagem, criar_barra_titulo
)

try:
    from views.view_menu_principal import TelaBase
except ImportError:
    class TelaBase(ctk.CTkFrame):
        def __init__(self, master, app=None, **kwargs):
            super().__init__(master, fg_color=FUNDO_DIREITO, corner_radius=0, **kwargs)
            self.app = app

        def ao_exibir(self):
            pass

# Import do Controller/Model de Reservas (se disponível)
try:
    from controls.control_reserva import CadastrarReserva
except Exception:
    def CadastrarReserva(*args, **kwargs):
        return False, "Controller de reservas não disponível."

try:
    from models.model_reserva import listar_db_reservas
except Exception:
    def listar_db_reservas():
        return []

# Import do Model de Apartamentos (se disponível)
try:
    from models.model_apto import listar_aptos, buscar_apto
except Exception:
    def listar_aptos(somente_vagos=False):
        return []

    def buscar_apto(numero):
        return None

FONTE = "Segoe UI"
BORDA_CARD = "#DCE4F0"
AZUL_CABECALHO = "#14376E"

# ----------------------------------------------------------------------
# CORES DE STATUS (legenda: Disponível / Ocupado / Indisponível)
# ----------------------------------------------------------------------
VERDE = "#2E9E5B"
VERDE_CLARO = "#E3F3E9"
VERMELHO = "#D9534F"
VERMELHO_CLARO = "#FBE6E5"
CINZA = "#9AA5B1"
CINZA_CLARO = "#ECEEF1"

STATUS_CORES = {
    "disponivel": (VERDE, VERDE_CLARO, "Disponível"),
    "ocupado": (VERMELHO, VERMELHO_CLARO, "Ocupado"),
    "indisponivel": (CINZA, CINZA_CLARO, "Indisponível"),
}

# ----------------------------------------------------------------------
# MOCK: quartos indisponíveis (limpeza/manutenção) -------------------
# Sem suporte real no banco ainda (ver nota no topo do arquivo).
# Troque/alimente esta lista quando houver uma fonte de dados real.
# ----------------------------------------------------------------------
QUARTOS_INDISPONIVEIS_MOCK = set()  # ex.: {4, 9}


# ----------------------------------------------------------------------
# FUNÇÕES DE DADOS (status do quarto e status por dia no calendário)
# ----------------------------------------------------------------------
def _carregar_quartos():
    """Devolve a lista de quartos a mostrar na grade (até 10).

    Cada item: {"numero": int, "status": "disponivel"|"ocupado"|"indisponivel", "id": int|None}
    Usa o banco real (model_apto) quando disponível; cai para um mock de
    10 quartos (1 a 10) se o banco ainda estiver vazio/inacessível.
    """
    quartos = []
    try:
        dados_banco = listar_aptos(somente_vagos=False)
    except Exception:
        dados_banco = []

    if dados_banco:
        # (id, tipo, numeracao, vago, preco_pessoa, limite_pessoa, ...)
        for linha in dados_banco:
            id_apto, _tipo, numeracao, vago = linha[0], linha[1], linha[2], linha[3]
            if numeracao in QUARTOS_INDISPONIVEIS_MOCK:
                status = "indisponivel"
            else:
                status = "disponivel" if vago else "ocupado"
            quartos.append({"numero": numeracao, "status": status, "id": id_apto})
        quartos.sort(key=lambda q: q["numero"])
    else:
        # Banco vazio: 10 quartos de exemplo, só para a tela não ficar em branco.
        for numero in range(1, 11):
            if numero in QUARTOS_INDISPONIVEIS_MOCK:
                status = "indisponivel"
            elif numero in (2, 7):
                status = "ocupado"
            else:
                status = "disponivel"
            quartos.append({"numero": numero, "status": status, "id": None})

    return quartos[:10]


def _status_dias_do_mes(quarto, ano, mes):
    """Devolve {dia: "disponivel"|"ocupado"|"indisponivel"} para cada dia do mês
    exibido no calendário, considerando o status do quarto selecionado.
    """
    qtd_dias = calendar.monthrange(ano, mes)[1]

    # Indisponível (mock): enquanto não há datas reais de manutenção/limpeza,
    # consideramos o mês inteiro indisponível para esse quarto.
    if quarto["status"] == "indisponivel":
        return {dia: "indisponivel" for dia in range(1, qtd_dias + 1)}

    status_por_dia = {dia: "disponivel" for dia in range(1, qtd_dias + 1)}

    if quarto["id"] is None:
        # Sem id real (modo mock) -> não há como cruzar com Reservas.
        return status_por_dia

    try:
        reservas = listar_db_reservas()
    except Exception:
        reservas = []

    # Linhas de Reservas: (id, id_cliente, id_apto, data_entrada, data_saida,
    #                      qt_pessoas, valor, status, checkin_feito)
    for r in reservas:
        if len(r) < 8:
            continue
        id_apto_reserva, data_entrada, data_saida, status_reserva = r[2], r[3], r[4], r[7]
        if id_apto_reserva != quarto["id"] or status_reserva == "cancelado":
            continue
        try:
            entrada = datetime.strptime(data_entrada, "%Y-%m-%d").date()
            saida = datetime.strptime(data_saida, "%Y-%m-%d").date()
        except ValueError:
            continue

        dia_cursor = date(ano, mes, 1)
        for dia in range(1, qtd_dias + 1):
            dia_cursor = date(ano, mes, dia)
            if entrada <= dia_cursor < saida:
                status_por_dia[dia] = "ocupado"

    return status_por_dia


# ----------------------------------------------------------------------
# POPUP DE CALENDÁRIO PARA ESCOLHER UMA DATA (usado no diálogo de Nova Reserva)
# ----------------------------------------------------------------------
class PopupCalendario(ctk.CTkToplevel):
    """Janelinha modal com calendário interativo para seleção de UMA data."""

    MESES = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

    def __init__(self, master, data_inicial=None, ao_selecionar=None):
        super().__init__(master)
        self.ao_selecionar = ao_selecionar

        if data_inicial:
            try:
                dt = datetime.strptime(data_inicial, "%d/%m/%Y").date()
                self.ano_atual = dt.year
                self.mes_atual = dt.month
                self.dia_selecionado = dt.day
            except Exception:
                hoje = date.today()
                self.ano_atual = hoje.year
                self.mes_atual = hoje.month
                self.dia_selecionado = hoje.day
        else:
            hoje = date.today()
            self.ano_atual = hoje.year
            self.mes_atual = hoje.month
            self.dia_selecionado = hoje.day

        self.title("Selecionar Data")
        centralizar_janela(self, 310, 330)
        self.resizable(False, False)
        self.configure(fg_color="white")

        if master is not None and master.winfo_viewable():
            self.transient(master)

        self._criar_ui()
        self.after(100, self._centralizar_e_focar)

    def _centralizar_e_focar(self):
        self.lift()
        self.focus_force()
        self.grab_set()

    def _criar_ui(self):
        nav = ctk.CTkFrame(self, fg_color=AZUL_CABECALHO, corner_radius=0, height=44)
        nav.pack(fill="x")
        nav.pack_propagate(False)

        ctk.CTkButton(
            nav, text="◀", width=32, height=32,
            fg_color="transparent", hover_color=AZUL_HOVER,
            font=(FONTE, 12, "bold"), command=self._mes_anterior
        ).pack(side="left", padx=8)

        self.lbl_mes_ano = ctk.CTkLabel(
            nav, text="", font=ctk.CTkFont(family=FONTE, size=14, weight="bold"),
            text_color="white"
        )
        self.lbl_mes_ano.pack(side="left", expand=True)

        ctk.CTkButton(
            nav, text="▶", width=32, height=32,
            fg_color="transparent", hover_color=AZUL_HOVER,
            font=(FONTE, 12, "bold"), command=self._mes_proximo
        ).pack(side="right", padx=8)

        semana = ctk.CTkFrame(self, fg_color="#F1F5F9", height=28, corner_radius=0)
        semana.pack(fill="x")
        for i, d in enumerate(self.DIAS_SEMANA):
            ctk.CTkLabel(
                semana, text=d, font=(FONTE, 11, "bold"),
                text_color=AZUL_ESCURO if i < 5 else LARANJA, width=42
            ).pack(side="left")

        self.frame_dias = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        self.frame_dias.pack(fill="both", expand=True, padx=8, pady=8)

        self._desenhar_dias()

    def _desenhar_dias(self):
        for w in self.frame_dias.winfo_children():
            w.destroy()

        self.lbl_mes_ano.configure(text=f"{self.MESES[self.mes_atual]} {self.ano_atual}")

        cal = calendar.monthcalendar(self.ano_atual, self.mes_atual)
        hoje = date.today()

        for r, sem in enumerate(cal):
            for c, dia in enumerate(sem):
                if dia == 0:
                    ctk.CTkLabel(self.frame_dias, text="", width=36, height=30).grid(
                        row=r, column=c, padx=2, pady=2)
                else:
                    e_selecionado = (dia == self.dia_selecionado)
                    e_hoje = (
                        dia == hoje.day and self.mes_atual == hoje.month
                        and self.ano_atual == hoje.year
                    )
                    fg = LARANJA if e_selecionado else ("#E2E8F0" if e_hoje else "transparent")
                    tc = "white" if e_selecionado else AZUL_ESCURO

                    ctk.CTkButton(
                        self.frame_dias, text=str(dia), width=36, height=30,
                        corner_radius=6, fg_color=fg,
                        hover_color=LARANJA_HOVER if e_selecionado else "#E2E8F0",
                        text_color=tc,
                        font=ctk.CTkFont(family=FONTE, size=12,
                                          weight="bold" if (e_selecionado or e_hoje) else "normal"),
                        command=lambda d=dia: self._escolher_dia(d)
                    ).grid(row=r, column=c, padx=2, pady=2)

    def _mes_anterior(self):
        if self.mes_atual == 1:
            self.mes_atual = 12
            self.ano_atual -= 1
        else:
            self.mes_atual -= 1
        self._desenhar_dias()

    def _mes_proximo(self):
        if self.mes_atual == 12:
            self.mes_atual = 1
            self.ano_atual += 1
        else:
            self.mes_atual += 1
        self._desenhar_dias()

    def _escolher_dia(self, dia):
        data_escolhida = f"{dia:02d}/{self.mes_atual:02d}/{self.ano_atual}"
        if self.ao_selecionar:
            self.ao_selecionar(data_escolhida)
        self.destroy()


# ----------------------------------------------------------------------
# DIÁLOGO: NOVA RESERVA (datas + qtd pessoas) para o quarto selecionado
# ----------------------------------------------------------------------
class DialogoNovaReserva(ctk.CTkToplevel):
    def __init__(self, master, quarto, ao_confirmar):
        super().__init__(master)
        self.quarto = quarto
        self.ao_confirmar = ao_confirmar

        self.title("Nova Reserva")
        centralizar_janela(self, 340, 360)
        self.resizable(False, False)
        self.configure(fg_color="white")
        if master is not None and master.winfo_viewable():
            self.transient(master)
        self.after(100, self._focar)

        barra = ctk.CTkFrame(self, fg_color=AZUL_CABECALHO, height=44, corner_radius=0)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        ctk.CTkLabel(
            barra, text=f"Nova Reserva — Quarto {quarto['numero']}",
            font=ctk.CTkFont(family=FONTE, size=14, weight="bold"), text_color="white"
        ).pack(side="left", padx=14)

        corpo = ctk.CTkFrame(self, fg_color="white")
        corpo.pack(fill="both", expand=True, padx=16, pady=14)

        hoje_str = date.today().strftime("%d/%m/%Y")
        saida_str = (date.today() + timedelta(days=1)).strftime("%d/%m/%Y")

        ctk.CTkLabel(corpo, text="Data de Entrada:", font=(FONTE, 12, "bold"),
                     text_color=AZUL_ESCURO).pack(anchor="w", pady=(0, 2))
        self.entry_entrada = self._campo_data(corpo, hoje_str)

        ctk.CTkLabel(corpo, text="Data de Saída:", font=(FONTE, 12, "bold"),
                     text_color=AZUL_ESCURO).pack(anchor="w", pady=(10, 2))
        self.entry_saida = self._campo_data(corpo, saida_str)

        ctk.CTkLabel(corpo, text="Quantidade de Pessoas:", font=(FONTE, 12, "bold"),
                     text_color=AZUL_ESCURO).pack(anchor="w", pady=(10, 2))
        self.entry_qt_pessoas = ctk.CTkEntry(
            corpo, font=ctk.CTkFont(family=FONTE, size=14, weight="bold"),
            fg_color="white", border_width=1, border_color=BORDA_CAMPO,
            text_color=AZUL_ESCURO, justify="center", height=36
        )
        self.entry_qt_pessoas.insert(0, "1")
        self.entry_qt_pessoas.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            corpo, text="Confirmar Reserva", font=(FONTE, 13, "bold"),
            fg_color=LARANJA, hover_color=LARANJA_HOVER, text_color="white",
            corner_radius=8, height=42, command=self._confirmar
        ).pack(fill="x", pady=(10, 0))

    def _focar(self):
        self.lift()
        self.focus_force()
        self.grab_set()

    def _campo_data(self, master, valor_inicial):
        moldura = ctk.CTkFrame(master, fg_color="white", corner_radius=8,
                                border_width=1, border_color=BORDA_CAMPO, height=38)
        moldura.pack(fill="x", pady=(0, 4))
        moldura.pack_propagate(False)

        entry = ctk.CTkEntry(moldura, font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
                              fg_color="white", border_width=0, text_color=AZUL_ESCURO)
        entry.insert(0, valor_inicial)
        entry.pack(side="left", fill="both", expand=True, padx=(10, 4), pady=3)

        ctk.CTkButton(
            moldura, text="📅", width=28, height=28, fg_color="transparent",
            hover_color="#E2E8F0", cursor="hand2", font=(FONTE, 14), text_color=AZUL_ESCURO,
            command=lambda e=entry: self._abrir_seletor(e)
        ).pack(side="right", padx=(0, 6), pady=3)
        return entry

    def _abrir_seletor(self, entry_alvo):
        def atualizar(data_formatada):
            entry_alvo.delete(0, "end")
            entry_alvo.insert(0, data_formatada)
        PopupCalendario(self, data_inicial=entry_alvo.get().strip(), ao_selecionar=atualizar)

    def _confirmar(self):
        self.ao_confirmar(
            self.entry_entrada.get().strip(),
            self.entry_saida.get().strip(),
            self.entry_qt_pessoas.get().strip(),
        )
        self.destroy()


# ----------------------------------------------------------------------
# TELA DE RESERVAS (mapa de quartos + calendário de status)
# ----------------------------------------------------------------------
class TelaReservas(TelaBase):
    """Tela de consulta de disponibilidade e reserva de quartos."""

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, app, **kwargs)
        self.numero_filtro = getattr(app, "apartamento_selecionado", None)
        if app is not None:
            app.apartamento_selecionado = None

        self._imagens_cache = []
        self.quartos = []
        self.cards_quartos = {}
        self.quarto_selecionado = None

        hoje = date.today()
        self.cal_ano = hoje.year
        self.cal_mes = hoje.month

        self._criar_cabecalho()
        self._criar_corpo()
        self._carregar_dados()

    def ao_exibir(self):
        numero = getattr(self.app, "apartamento_selecionado", None)
        if numero is not None:
            self.numero_filtro = numero
            self.app.apartamento_selecionado = None
        self._carregar_dados()

    # ------------------------------------------------------------------
    # CABEÇALHO: título + legenda de status
    # ------------------------------------------------------------------
    def _criar_cabecalho(self):
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=25, pady=(18, 10))

        img_cal = carregar_imagem("icone_reservas.png", (38, 38))
        if img_cal:
            self._imagens_cache.append(img_cal)
            lbl_ico = ctk.CTkLabel(cabecalho, text="", image=img_cal)
        else:
            lbl_ico = ctk.CTkLabel(cabecalho, text="🛏", font=(FONTE, 28), text_color=AZUL_ESCURO)
        lbl_ico.pack(side="left", padx=(0, 10))

        textos = ctk.CTkFrame(cabecalho, fg_color="transparent")
        textos.pack(side="left")
        ctk.CTkLabel(
            textos, text="Reserva de Quartos",
            font=ctk.CTkFont(family=FONTE, size=22, weight="bold"), text_color=AZUL_ESCURO
        ).pack(anchor="w")
        ctk.CTkLabel(
            textos, text="Visualize a disponibilidade e selecione um quarto",
            font=ctk.CTkFont(family=FONTE, size=13), text_color=TEXTO_CINZA
        ).pack(anchor="w")

        legenda = ctk.CTkFrame(cabecalho, fg_color="transparent")
        legenda.pack(side="right")
        for chave in ("disponivel", "ocupado", "indisponivel"):
            cor, _cor_clara, rotulo = STATUS_CORES[chave]
            item = ctk.CTkFrame(legenda, fg_color="transparent")
            item.pack(side="left", padx=(0, 14))
            ctk.CTkFrame(item, width=12, height=12, corner_radius=6, fg_color=cor).pack(side="left")
            ctk.CTkLabel(item, text=rotulo, font=(FONTE, 12), text_color=TEXTO_CINZA).pack(
                side="left", padx=(6, 0))

    # ------------------------------------------------------------------
    # CORPO: grade de quartos (esquerda) + calendário (direita)
    # ------------------------------------------------------------------
    def _criar_corpo(self):
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=25, pady=(0, 10))

        self._criar_painel_quartos(corpo)
        self._criar_painel_calendario(corpo)

        self._criar_rodape()

    # --- PAINEL ESQUERDO: GRADE DE QUARTOS ------------------------------
    def _criar_painel_quartos(self, master):
        self.card_quartos = ctk.CTkFrame(
            master, fg_color="white", corner_radius=12,
            border_width=1, border_color=BORDA_CARD
        )
        self.card_quartos.pack(side="left", fill="both", expand=True, padx=(0, 16))

        barra_tit = ctk.CTkFrame(self.card_quartos, height=40, fg_color=AZUL_CABECALHO, corner_radius=12)
        barra_tit.pack(fill="x")
        barra_tit.pack_propagate(False)

        self.lbl_titulo_quartos = ctk.CTkLabel(
            barra_tit, text="Quartos (0)",
            font=ctk.CTkFont(family=FONTE, size=14, weight="bold"), text_color="white"
        )
        self.lbl_titulo_quartos.pack(side="left", padx=14)

        self.grade_quartos = ctk.CTkFrame(self.card_quartos, fg_color="transparent")
        self.grade_quartos.pack(fill="both", expand=True, padx=12, pady=12)
        for col in range(5):
            self.grade_quartos.grid_columnconfigure(col, weight=1, uniform="q")

    # --- PAINEL DIREITO: CALENDÁRIO --------------------------------------
    def _criar_painel_calendario(self, master):
        self.card_calendario = ctk.CTkFrame(
            master, width=300, fg_color="white", corner_radius=12,
            border_width=1, border_color=BORDA_CARD
        )
        self.card_calendario.pack(side="left", fill="y")
        self.card_calendario.pack_propagate(False)

        barra_tit = ctk.CTkFrame(self.card_calendario, height=40, fg_color=AZUL_CABECALHO, corner_radius=12)
        barra_tit.pack(fill="x")
        barra_tit.pack_propagate(False)
        ctk.CTkLabel(
            barra_tit, text="Calendário",
            font=ctk.CTkFont(family=FONTE, size=14, weight="bold"), text_color="white"
        ).pack(side="left", padx=14)

        nav = ctk.CTkFrame(self.card_calendario, fg_color="transparent")
        nav.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkButton(
            nav, text="◀", width=28, height=28, fg_color="transparent",
            hover_color="#E2E8F0", text_color=AZUL_ESCURO,
            font=(FONTE, 12, "bold"), command=self._mes_anterior
        ).pack(side="left")

        self.lbl_mes_ano = ctk.CTkLabel(
            nav, text="", font=ctk.CTkFont(family=FONTE, size=14, weight="bold"), text_color=AZUL_ESCURO
        )
        self.lbl_mes_ano.pack(side="left", expand=True)

        ctk.CTkButton(
            nav, text="▶", width=28, height=28, fg_color="transparent",
            hover_color="#E2E8F0", text_color=AZUL_ESCURO,
            font=(FONTE, 12, "bold"), command=self._mes_proximo
        ).pack(side="right")

        semana = ctk.CTkFrame(self.card_calendario, fg_color="#F1F5F9")
        semana.pack(fill="x", padx=12)
        for i, d in enumerate(["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]):
            ctk.CTkLabel(
                semana, text=d, font=(FONTE, 11, "bold"), width=34,
                text_color=LARANJA if i == 0 or i == 6 else AZUL_ESCURO
            ).pack(side="left", expand=True)

        self.grade_dias = ctk.CTkFrame(self.card_calendario, fg_color="transparent")
        self.grade_dias.pack(fill="both", expand=True, padx=10, pady=10)
        for col in range(7):
            self.grade_dias.grid_columnconfigure(col, weight=1, uniform="d")

    # --- RODAPÉ: info + botão Nova Reserva -------------------------------
    def _criar_rodape(self):
        rodape = ctk.CTkFrame(self, fg_color="#EAF1FB", corner_radius=10)
        rodape.pack(fill="x", padx=25, pady=(0, 18))

        conteudo = ctk.CTkFrame(rodape, fg_color="transparent")
        conteudo.pack(fill="x", padx=14, pady=10)

        self.lbl_info_rodape = ctk.CTkLabel(
            conteudo, text="ℹ️  Selecione um quarto para visualizar o calendário e realizar a reserva.",
            font=(FONTE, 12), text_color=AZUL_ESCURO, anchor="w"
        )
        self.lbl_info_rodape.pack(side="left", fill="x", expand=True)

        self.btn_nova_reserva = ctk.CTkButton(
            conteudo, text="📅  Nova Reserva", font=(FONTE, 13, "bold"),
            fg_color=AZUL_CABECALHO, hover_color=AZUL_HOVER, text_color="white",
            corner_radius=8, height=36, state="disabled", command=self.ao_clicar_nova_reserva
        )
        self.btn_nova_reserva.pack(side="right")

    # ------------------------------------------------------------------
    # CARREGAR / DESENHAR DADOS
    # ------------------------------------------------------------------
    def _carregar_dados(self):
        self.quartos = _carregar_quartos()
        self.lbl_titulo_quartos.configure(text=f"Quartos ({len(self.quartos)})")

        if self.numero_filtro is not None:
            self.quarto_selecionado = next(
                (q for q in self.quartos if q["numero"] == self.numero_filtro), None
            )
        self._desenhar_grade_quartos()
        self._desenhar_calendario()
        self._atualizar_rodape()

    def _desenhar_grade_quartos(self):
        for w in self.grade_quartos.winfo_children():
            w.destroy()
        self.cards_quartos = {}

        for indice, quarto in enumerate(self.quartos):
            linha, coluna = divmod(indice, 5)
            card = self._criar_card_quarto(self.grade_quartos, quarto)
            card.grid(row=linha, column=coluna, padx=6, pady=6, sticky="nsew")
            self.cards_quartos[quarto["numero"]] = card

    def _criar_card_quarto(self, master, quarto):
        cor, _cor_clara, rotulo = STATUS_CORES[quarto["status"]]
        selecionado = self.quarto_selecionado is not None and self.quarto_selecionado["numero"] == quarto["numero"]

        card = ctk.CTkFrame(
            master, width=150, height=150, corner_radius=10,
            fg_color="white", border_width=2,
            border_color=AZUL_ESCURO if selecionado else BORDA_CARD,
            cursor="hand2"
        )
        card.pack_propagate(False)

        topo = ctk.CTkFrame(card, fg_color="transparent")
        topo.pack(fill="x", padx=8, pady=(8, 2))
        ctk.CTkLabel(
            topo, text=f"Quarto {quarto['numero']}", font=(FONTE, 13, "bold"),
            text_color=AZUL_ESCURO
        ).pack(side="left")
        if selecionado:
            ctk.CTkLabel(
                topo, text="✓", font=(FONTE, 12, "bold"), text_color="white",
                fg_color=AZUL_ESCURO, width=18, height=18, corner_radius=9
            ).pack(side="right")

        img_quarto = carregar_imagem("foto_quarto.png", (130, 72))
        if img_quarto:
            self._imagens_cache.append(img_quarto)
            lbl_foto = ctk.CTkLabel(card, text="", image=img_quarto, corner_radius=6)
        else:
            lbl_foto = ctk.CTkFrame(card, height=72, fg_color="#E2E8F0", corner_radius=6)
        lbl_foto.pack(fill="x", padx=8, pady=2)

        rodape_card = ctk.CTkFrame(card, fg_color="transparent")
        rodape_card.pack(fill="x", padx=8, pady=(4, 8))
        ctk.CTkFrame(rodape_card, width=10, height=10, corner_radius=5, fg_color=cor).pack(side="left")
        ctk.CTkLabel(rodape_card, text=rotulo, font=(FONTE, 11), text_color=TEXTO_CINZA).pack(
            side="left", padx=(6, 0))

        # Qualquer quarto pode ser selecionado para consulta; só os
        # disponíveis permitem reservar (ver _atualizar_rodape).
        for widget in (card, topo, lbl_foto, rodape_card):
            widget.bind("<Button-1>", lambda e, q=quarto: self._selecionar_quarto(q))
        return card

    def _selecionar_quarto(self, quarto):
        self.quarto_selecionado = quarto
        self._desenhar_grade_quartos()
        self._desenhar_calendario()
        self._atualizar_rodape()

    def _desenhar_calendario(self):
        for w in self.grade_dias.winfo_children():
            w.destroy()

        self.lbl_mes_ano.configure(
            text=f"{PopupCalendario.MESES[self.cal_mes]} {self.cal_ano}"
        )

        status_por_dia = {}
        if self.quarto_selecionado is not None:
            status_por_dia = _status_dias_do_mes(self.quarto_selecionado, self.cal_ano, self.cal_mes)

        # calendar.Calendar com firstweekday=6 -> semana começa no Domingo (como no print)
        cal = calendar.Calendar(firstweekday=6)
        semanas = cal.monthdayscalendar(self.cal_ano, self.cal_mes)

        for r, sem in enumerate(semanas):
            for c, dia in enumerate(sem):
                if dia == 0:
                    ctk.CTkFrame(self.grade_dias, fg_color="transparent", width=34, height=30).grid(
                        row=r, column=c, padx=2, pady=2)
                    continue

                status_dia = status_por_dia.get(dia)
                if status_dia:
                    cor_forte, cor_clara, _rotulo = STATUS_CORES[status_dia]
                    fg = cor_clara
                    tc = cor_forte
                else:
                    fg = "transparent"
                    tc = AZUL_ESCURO

                ctk.CTkLabel(
                    self.grade_dias, text=str(dia), width=34, height=30,
                    corner_radius=6, fg_color=fg, text_color=tc,
                    font=ctk.CTkFont(family=FONTE, size=12, weight="bold" if status_dia else "normal"),
                ).grid(row=r, column=c, padx=2, pady=2)

    def _mes_anterior(self):
        if self.cal_mes == 1:
            self.cal_mes = 12
            self.cal_ano -= 1
        else:
            self.cal_mes -= 1
        self._desenhar_calendario()

    def _mes_proximo(self):
        if self.cal_mes == 12:
            self.cal_mes = 1
            self.cal_ano += 1
        else:
            self.cal_mes += 1
        self._desenhar_calendario()

    def _atualizar_rodape(self):
        if self.quarto_selecionado is None:
            self.lbl_info_rodape.configure(
                text="ℹ️  Selecione um quarto para visualizar o calendário e realizar a reserva."
            )
            self.btn_nova_reserva.configure(state="disabled")
            return

        quarto = self.quarto_selecionado
        _cor, _cor_clara, rotulo = STATUS_CORES[quarto["status"]]
        if quarto["status"] == "disponivel":
            self.lbl_info_rodape.configure(
                text=f"ℹ️  Quarto {quarto['numero']} selecionado — {rotulo}. Escolha as datas em \"Nova Reserva\"."
            )
            self.btn_nova_reserva.configure(state="normal")
        else:
            self.lbl_info_rodape.configure(
                text=f"ℹ️  Quarto {quarto['numero']} está {rotulo.lower()} e não pode ser reservado agora."
            )
            self.btn_nova_reserva.configure(state="disabled")

    # ------------------------------------------------------------------
    # AÇÃO: Nova Reserva
    # ------------------------------------------------------------------
    def ao_clicar_nova_reserva(self):
        if self.quarto_selecionado is None or self.quarto_selecionado["status"] != "disponivel":
            return
        DialogoNovaReserva(self, self.quarto_selecionado, self._confirmar_reserva)

    def _confirmar_reserva(self, data_in_raw, data_out_raw, qt_pessoas_raw):
        data_in = self._converter_data(data_in_raw)
        data_out = self._converter_data(data_out_raw)
        if not data_in or not data_out:
            messagebox.showerror("Data Inválida", "Informe as datas no formato DD/MM/AAAA.", parent=self)
            return

        try:
            qt_pessoas = int(qt_pessoas_raw)
            if qt_pessoas <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Quantidade Inválida", "Informe uma quantidade de pessoas válida (mínimo 1).", parent=self
            )
            return

        quarto = self.quarto_selecionado
        id_apto = quarto["id"]
        if id_apto is None:
            messagebox.showwarning(
                "Quarto sem cadastro",
                "Este quarto é apenas um exemplo (mock) e não existe no banco ainda.",
                parent=self,
            )
            return

        mensagem = (
            f"Deseja confirmar a reserva do quarto {quarto['numero']}?\n\n"
            f"📅 Entrada: {data_in_raw}\n"
            f"📅 Saída:   {data_out_raw}\n"
            f"👥 Pessoas: {qt_pessoas}\n"
        )
        if not messagebox.askyesno("Confirmar Reserva", mensagem, parent=self):
            return

        id_cliente = getattr(self.app, "id_cliente_logado", None)
        if not id_cliente:
            messagebox.showwarning(
                "Sessão inválida",
                "Não foi possível identificar o cliente logado.\nFaça login novamente.",
                parent=self,
            )
            return

        sucesso, mensagem_retorno = CadastrarReserva(id_cliente, id_apto, data_in, data_out, qt_pessoas)
        if sucesso:
            messagebox.showinfo("Reserva Concluída", mensagem_retorno, parent=self)
            self._carregar_dados()
        else:
            messagebox.showerror("Erro na Reserva", mensagem_retorno, parent=self)

    @staticmethod
    def _converter_data(data_str):
        try:
            return datetime.strptime(data_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            return None


# ----------------------------------------------------------------------
# TESTE ISOLADO DA TELA: python -m views.view_reserva
# ----------------------------------------------------------------------
if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    janela = ctk.CTk()
    janela.title("Sistema de Reservas - Hotel")
    janela.geometry("1100x640")
    criar_barra_titulo(janela)

    tela = TelaReservas(janela)
    tela.pack(fill="both", expand=True)

    janela.mainloop()