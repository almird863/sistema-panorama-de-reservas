"""
View de Reservas - Sistema de Reservas - Hotel
Compatível tanto como tela embutida (TelaBase no menu principal)
quanto executável de forma independente para testes.

----------------------------------------------------------------------
LEIA ANTES DE MEXER — como esse arquivo lida com dados neste momento
----------------------------------------------------------------------
A nossa parte no projeto (Wallace) é só VIEWS. O esquema de banco mudou
bastante nos últimos dias (branch `models`/`work`):

    Apartamentos  -> Unidade_Habitacional  (id, numeracao, status, ...)
    Reservas      -> Estadias              (checkin_data/checkout_data
                                             reais, sem mais reserva por
                                             data futura)

As controllers antigas (`controls/control_apto.py`, `controls/control_reserva.py`)
ainda apontam pros módulos antigos (`models.model_apto`, `models.model_reserva`),
que não existem mais, e ainda não existe nenhum `control_uh.py` /
`control_estadia.py` prontos para o novo esquema. Pra não travar esperando
isso e pra não mexer em código de outros colegas sem combinar, esta view
NÃO importa `models` nem `controls` de ninguém além da tentativa abaixo:
ela tenta importar um "control_uh" / "control_estadia" (hipotéticos,
ainda não existem) e, se não encontrar, cai automaticamente num MOCK local
(dados em memória, só pra tela funcionar e ser demonstrável).

Quando o colega responsável por controls criar esses arquivos com essas
assinaturas, a troca é automática — não precisa mexer nesta view:

    controls/control_uh.py
        ListarUH() -> lista de tuplas (id, numeracao, status, vista_mar,
                                        vista_rua, acessivel)
        AtualizarStatusUH(numeracao, novo_status) -> (bool, mensagem)

    controls/control_estadia.py
        CadastrarEstadia(nome_hospede, cpf_hospede, id_uh, qt_pessoas)
            -> (bool, mensagem)
        FazerCheckin(id_estadia) -> (bool, mensagem)
        FazerCheckout(id_estadia) -> (bool, mensagem)

Status possíveis em Unidade_Habitacional (ver models/model_uh.py):
    "Livre e limpa", "Em limpeza", "Hospede na casa", "Reservado", "Indisponível"

Essa tela resume esses 5 status em 3 cores pra bater com o protótipo:
    verde   (disponível)   <- "Livre e limpa"
    vermelho (ocupado)     <- "Hospede na casa", "Reservado"
    cinza   (indisponível) <- "Em limpeza", "Indisponível"

O calendário à direita, por enquanto, pinta o MÊS INTEIRO com a cor do
status atual do quarto — ainda não existe no banco nenhuma informação de
"dia a dia" (isso morreu quando data_entrada/data_saida virou
checkin_data/checkout_data reais). Quando existir um histórico real de
estadias por dia, dá pra pintar dia a dia de verdade; o ponto de troca é
a função `_status_dias_do_mes()` abaixo.
"""

import calendar
from datetime import date, datetime
import customtkinter as ctk
from tkinter import messagebox

from views.componentes import (
    AZUL_ESCURO, AZUL_HOVER, LARANJA, LARANJA_HOVER, FUNDO_DIREITO,
    BORDA_CAMPO, TEXTO_CINZA, carregar_imagem, criar_barra_titulo,
    centralizar_janela,
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

# ----------------------------------------------------------------------
# Import "otimista" dos controls do novo esquema (ainda não existem).
# Se/quando existirem com essas assinaturas, passam a ser usados sem
# precisar mexer em mais nada aqui.
# ----------------------------------------------------------------------
try:
    from controls.control_uh import ListarUH, AtualizarStatusUH
    _TEM_CONTROL_UH = True
except Exception:
    _TEM_CONTROL_UH = False

try:
    from controls.control_estadia import CadastrarEstadia, FazerCheckin, FazerCheckout
    _TEM_CONTROL_ESTADIA = True
except Exception:
    _TEM_CONTROL_ESTADIA = False

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

# Status reais de Unidade_Habitacional -> grupo de cor usado na tela
STATUS_REAL_PARA_GRUPO = {
    "Livre e limpa": "disponivel",
    "Em limpeza": "indisponivel",
    "Hospede na casa": "ocupado",
    "Reservado": "ocupado",
    "Indisponível": "indisponivel",
}


# ----------------------------------------------------------------------
# MOCK: 10 Unidades Habitacionais em memória ---------------------------
# Usado só enquanto controls/control_uh.py e controls/control_estadia.py
# não existirem (ver nota no topo do arquivo). Dados somem ao reiniciar
# o programa — é só pra tela ficar demonstrável e testável isoladamente.
# ----------------------------------------------------------------------
_MOCK_UHS = [
    {"id": 1, "numeracao": 101, "status": "Livre e limpa"},
    {"id": 2, "numeracao": 102, "status": "Hospede na casa"},
    {"id": 3, "numeracao": 103, "status": "Livre e limpa"},
    {"id": 4, "numeracao": 104, "status": "Em limpeza"},
    {"id": 5, "numeracao": 105, "status": "Livre e limpa"},
    {"id": 6, "numeracao": 106, "status": "Reservado"},
    {"id": 7, "numeracao": 107, "status": "Hospede na casa"},
    {"id": 8, "numeracao": 108, "status": "Livre e limpa"},
    {"id": 9, "numeracao": 109, "status": "Indisponível"},
    {"id": 10, "numeracao": 110, "status": "Livre e limpa"},
]
_MOCK_PROXIMO_ID_ESTADIA = [1]


def _mock_listar_uh():
    """Formato igual ao esperado de controls.control_uh.ListarUH():
    lista de tuplas (id, numeracao, status, vista_mar, vista_rua, acessivel).
    """
    return [
        (u["id"], u["numeracao"], u["status"], 0, 0, 0)
        for u in _MOCK_UHS
    ]


def _mock_atualizar_status_uh(numeracao, novo_status):
    for u in _MOCK_UHS:
        if u["numeracao"] == numeracao:
            u["status"] = novo_status
            return True, f"Unidade Habitacional Nº{numeracao} atualizada para {novo_status}."
    return False, "Unidade não encontrada."


def _mock_cadastrar_estadia(nome_hospede, cpf_hospede, id_uh, qt_pessoas):
    for u in _MOCK_UHS:
        if u["id"] == id_uh:
            u["status"] = "Hospede na casa"
            id_estadia = _MOCK_PROXIMO_ID_ESTADIA[0]
            _MOCK_PROXIMO_ID_ESTADIA[0] += 1
            return True, f"[MOCK] Check-in de {nome_hospede} registrado (estadia #{id_estadia})."
    return False, "Unidade não encontrada."


def _mock_fazer_checkout(numeracao):
    for u in _MOCK_UHS:
        if u["numeracao"] == numeracao:
            u["status"] = "Em limpeza"
            return True, f"[MOCK] Check-out do quarto {numeracao} registrado (foi para limpeza)."
    return False, "Unidade não encontrada."


# ----------------------------------------------------------------------
# Funções de dados usadas pela tela — tentam o control real primeiro,
# caem pro mock automaticamente.
# ----------------------------------------------------------------------
def _carregar_quartos():
    """Devolve até 10 quartos: [{"numero", "status_real", "grupo", "id"}, ...]."""
    if _TEM_CONTROL_UH:
        try:
            linhas = ListarUH()
        except Exception:
            linhas = _mock_listar_uh()
    else:
        linhas = _mock_listar_uh()

    quartos = []
    for linha in linhas:
        id_uh, numeracao, status_real = linha[0], linha[1], linha[2]
        grupo = STATUS_REAL_PARA_GRUPO.get(status_real, "indisponivel")
        quartos.append({
            "id": id_uh, "numero": numeracao,
            "status_real": status_real, "grupo": grupo,
        })
    quartos.sort(key=lambda q: q["numero"])
    return quartos[:10]


def _status_dias_do_mes(quarto, ano, mes):
    """Status (grupo de cor) de cada dia do mês para o quarto selecionado.

    MOCK/simplificado: como o banco não guarda mais disponibilidade por
    data futura (ver nota no topo do arquivo), pintamos o mês inteiro com
    o status ATUAL do quarto. Troque aqui quando houver uma fonte real de
    disponibilidade dia a dia.
    """
    qtd_dias = calendar.monthrange(ano, mes)[1]
    return {dia: quarto["grupo"] for dia in range(1, qtd_dias + 1)}


# ----------------------------------------------------------------------
# POPUP DE CALENDÁRIO (navegação visual, sem seleção de data específica
# — aqui só serve pra mostrar o status por dia do quarto selecionado)
# ----------------------------------------------------------------------
class PopupCalendario(ctk.CTkToplevel):
    MESES = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]


# ----------------------------------------------------------------------
# DIÁLOGO: FAZER CHECK-IN no quarto selecionado
# ----------------------------------------------------------------------
class DialogoCheckin(ctk.CTkToplevel):
    def __init__(self, master, quarto, ao_confirmar):
        super().__init__(master)
        self.quarto = quarto
        self.ao_confirmar = ao_confirmar

        self.title("Fazer Check-in")
        centralizar_janela(self, 340, 320)
        self.resizable(False, False)
        self.configure(fg_color="white")
        if master is not None and master.winfo_viewable():
            self.transient(master)
        self.after(100, self._focar)

        barra = ctk.CTkFrame(self, fg_color=AZUL_CABECALHO, height=44, corner_radius=0)
        barra.pack(fill="x")
        barra.pack_propagate(False)
        ctk.CTkLabel(
            barra, text=f"Check-in — Quarto {quarto['numero']}",
            font=ctk.CTkFont(family=FONTE, size=14, weight="bold"), text_color="white"
        ).pack(side="left", padx=14)

        corpo = ctk.CTkFrame(self, fg_color="white")
        corpo.pack(fill="both", expand=True, padx=16, pady=14)

        ctk.CTkLabel(corpo, text="Nome do Hóspede:", font=(FONTE, 12, "bold"),
                     text_color=AZUL_ESCURO).pack(anchor="w", pady=(0, 2))
        self.entry_nome = ctk.CTkEntry(
            corpo, font=ctk.CTkFont(family=FONTE, size=13),
            fg_color="white", border_width=1, border_color=BORDA_CAMPO, height=36
        )
        self.entry_nome.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(corpo, text="CPF:", font=(FONTE, 12, "bold"),
                     text_color=AZUL_ESCURO).pack(anchor="w", pady=(0, 2))
        self.entry_cpf = ctk.CTkEntry(
            corpo, font=ctk.CTkFont(family=FONTE, size=13),
            fg_color="white", border_width=1, border_color=BORDA_CAMPO, height=36
        )
        self.entry_cpf.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(corpo, text="Quantidade de Pessoas:", font=(FONTE, 12, "bold"),
                     text_color=AZUL_ESCURO).pack(anchor="w", pady=(0, 2))
        self.entry_qt_pessoas = ctk.CTkEntry(
            corpo, font=ctk.CTkFont(family=FONTE, size=14, weight="bold"),
            fg_color="white", border_width=1, border_color=BORDA_CAMPO,
            text_color=AZUL_ESCURO, justify="center", height=36
        )
        self.entry_qt_pessoas.insert(0, "1")
        self.entry_qt_pessoas.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            corpo, text="Confirmar Check-in", font=(FONTE, 13, "bold"),
            fg_color=LARANJA, hover_color=LARANJA_HOVER, text_color="white",
            corner_radius=8, height=42, command=self._confirmar
        ).pack(fill="x", pady=(10, 0))

    def _focar(self):
        self.lift()
        self.focus_force()
        self.grab_set()

    def _confirmar(self):
        self.ao_confirmar(
            self.entry_nome.get().strip(),
            self.entry_cpf.get().strip(),
            self.entry_qt_pessoas.get().strip(),
        )
        self.destroy()


# ----------------------------------------------------------------------
# TELA DE RESERVAS (mapa de quartos por status + calendário)
# ----------------------------------------------------------------------
class TelaReservas(TelaBase):
    """Tela de consulta de disponibilidade e check-in/check-out de quartos."""

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
            master, width=340, height=460, fg_color="white", corner_radius=12,
            border_width=1, border_color=BORDA_CARD
        )
        self.card_calendario.pack(side="left", anchor="n")
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

    # --- RODAPÉ: info + botão de ação -----------------------------------
    def _criar_rodape(self):
        rodape = ctk.CTkFrame(self, fg_color="#EAF1FB", corner_radius=10)
        rodape.pack(fill="x", padx=25, pady=(0, 18))

        conteudo = ctk.CTkFrame(rodape, fg_color="transparent")
        conteudo.pack(fill="x", padx=14, pady=10)

        self.lbl_info_rodape = ctk.CTkLabel(
            conteudo, text="ℹ️  Selecione um quarto para visualizar o status e realizar o check-in.",
            font=(FONTE, 12), text_color=AZUL_ESCURO, anchor="w"
        )
        self.lbl_info_rodape.pack(side="left", fill="x", expand=True)

        self.btn_acao = ctk.CTkButton(
            conteudo, text="✔  Fazer Check-in", font=(FONTE, 13, "bold"),
            fg_color=AZUL_CABECALHO, hover_color=AZUL_HOVER, text_color="white",
            corner_radius=8, height=36, state="disabled", command=self.ao_clicar_acao
        )
        self.btn_acao.pack(side="right")

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
        cor, _cor_clara, rotulo = STATUS_CORES[quarto["grupo"]]
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
        rodape_card.pack(fill="x", padx=8, pady=(4, 2))
        ctk.CTkFrame(rodape_card, width=10, height=10, corner_radius=5, fg_color=cor).pack(side="left")
        ctk.CTkLabel(rodape_card, text=rotulo, font=(FONTE, 11), text_color=TEXTO_CINZA).pack(
            side="left", padx=(6, 0))

        ctk.CTkLabel(
            card, text=quarto["status_real"], font=(FONTE, 9), text_color="#8A93A6"
        ).pack(fill="x", padx=8, pady=(0, 6))

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

        # firstweekday=6 -> semana começa no Domingo (como no protótipo)
        cal = calendar.Calendar(firstweekday=6)
        semanas = cal.monthdayscalendar(self.cal_ano, self.cal_mes)

        for r, sem in enumerate(semanas):
            for c, dia in enumerate(sem):
                if dia == 0:
                    ctk.CTkFrame(self.grade_dias, fg_color="transparent", width=34, height=30).grid(
                        row=r, column=c, padx=2, pady=2)
                    continue

                grupo_dia = status_por_dia.get(dia)
                if grupo_dia:
                    cor_forte, cor_clara, _rotulo = STATUS_CORES[grupo_dia]
                    fg, tc = cor_clara, cor_forte
                else:
                    fg, tc = "transparent", AZUL_ESCURO

                ctk.CTkLabel(
                    self.grade_dias, text=str(dia), width=34, height=30,
                    corner_radius=6, fg_color=fg, text_color=tc,
                    font=ctk.CTkFont(family=FONTE, size=12, weight="bold" if grupo_dia else "normal"),
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
                text="ℹ️  Selecione um quarto para visualizar o status e realizar o check-in."
            )
            self.btn_acao.configure(state="disabled")
            return

        quarto = self.quarto_selecionado
        _cor, _cor_clara, rotulo = STATUS_CORES[quarto["grupo"]]

        if quarto["grupo"] == "disponivel":
            self.lbl_info_rodape.configure(
                text=f"ℹ️  Quarto {quarto['numero']} selecionado — {quarto['status_real']}. "
                     f"Pronto para check-in."
            )
            self.btn_acao.configure(text="✔  Fazer Check-in", state="normal")
        elif quarto["status_real"] == "Hospede na casa":
            self.lbl_info_rodape.configure(
                text=f"ℹ️  Quarto {quarto['numero']} está com hóspede. Pode registrar o check-out."
            )
            self.btn_acao.configure(text="🚪  Fazer Check-out", state="normal")
        else:
            self.lbl_info_rodape.configure(
                text=f"ℹ️  Quarto {quarto['numero']} está {rotulo.lower()} ({quarto['status_real']}) "
                     f"e não está disponível para check-in agora."
            )
            self.btn_acao.configure(state="disabled")

    # ------------------------------------------------------------------
    # AÇÃO: Check-in / Check-out
    # ------------------------------------------------------------------
    def ao_clicar_acao(self):
        quarto = self.quarto_selecionado
        if quarto is None:
            return

        if quarto["grupo"] == "disponivel":
            DialogoCheckin(self, quarto, self._confirmar_checkin)
        elif quarto["status_real"] == "Hospede na casa":
            self._confirmar_checkout(quarto)

    def _confirmar_checkin(self, nome_hospede, cpf_hospede, qt_pessoas_raw):
        if not nome_hospede:
            messagebox.showerror("Dados incompletos", "Informe o nome do hóspede.", parent=self)
            return
        try:
            qt_pessoas = int(qt_pessoas_raw)
            if qt_pessoas <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Quantidade inválida", "Informe uma quantidade de pessoas válida (mínimo 1).", parent=self
            )
            return

        quarto = self.quarto_selecionado
        if _TEM_CONTROL_ESTADIA:
            try:
                sucesso, mensagem = CadastrarEstadia(nome_hospede, cpf_hospede, quarto["id"], qt_pessoas)
            except Exception as erro:
                sucesso, mensagem = False, f"Erro ao registrar check-in: {erro}"
        else:
            sucesso, mensagem = _mock_cadastrar_estadia(nome_hospede, cpf_hospede, quarto["id"], qt_pessoas)

        if sucesso:
            messagebox.showinfo("Check-in realizado", mensagem, parent=self)
            self._carregar_dados()
        else:
            messagebox.showerror("Erro no check-in", mensagem, parent=self)

    def _confirmar_checkout(self, quarto):
        if not messagebox.askyesno(
            "Confirmar Check-out", f"Confirmar check-out do quarto {quarto['numero']}?", parent=self
        ):
            return

        if _TEM_CONTROL_ESTADIA:
            try:
                sucesso, mensagem = FazerCheckout(quarto["id"])
            except Exception as erro:
                sucesso, mensagem = False, f"Erro ao registrar check-out: {erro}"
        else:
            sucesso, mensagem = _mock_fazer_checkout(quarto["numero"])

        if sucesso:
            messagebox.showinfo("Check-out realizado", mensagem, parent=self)
            self._carregar_dados()
        else:
            messagebox.showerror("Erro no check-out", mensagem, parent=self)


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
