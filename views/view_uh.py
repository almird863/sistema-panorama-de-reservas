"""
view_uh.py
----------
Tela "Unidade Habitacional" do Sistema de Reservas - Hotel.
Substitui a antiga tela de Apartamentos.

Layout fiel ao protótipo da recepção (uh_hopede_checkin.png):
  - Cabeçalho: ícone de quarto/cama + título "Unidade Habitacional" +
    subtítulo "Gerencie os quartos do hotel" + onda decorativa lateral
  - Grid Superior (2 cards lado a lado):
      1. Card "Dados do Quarto":
         - Número do Quarto (Entry)
         - Categoria (ComboBox: Standard, Duplo, Luxo, Super Luxo, Suíte)
         - Status (ComboBox: Disponível, Ocupado, Limpeza, Indisponível)
         - Botões "Salvar" (💾) e "Limpar" (↻)
      2. Card "Calendário":
         - Navegação por mês (‹ Mês Ano ›)
         - Grade completa do mês com seleção de dia
  - Card Inferior: "Ocupação dos Quartos":
      - Tabela com: Número | Categoria | Status (com badge/bolinha) | Observação
      - Clique na linha preenche o formulário para edição rápida

Rodar isolado: python -m views.view_uh
"""

import calendar
from datetime import date, datetime
import sqlite3
import customtkinter as ctk
from tkinter import messagebox

from views.componentes import (
    AZUL_ESCURO, AZUL_HOVER, LARANJA, LARANJA_HOVER,
    FUNDO_DIREITO, BORDA_CAMPO, TEXTO_CINZA,
    carregar_imagem, montar_imagem_lateral,
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
# CORES E ESTILOS VISUAIS
# ----------------------------------------------------------------------
FONTE = "Segoe UI"
BRANCO = "#FFFFFF"
BORDA_CARD = "#D5DAE6"
CINZA_HEADER = "#EEF1F7"
AZUL_CABECALHO = "#14376E"

VERDE = "#2E9E5B"
VERDE_CLARO = "#E3F3E9"
VERMELHO = "#D9534F"
VERMELHO_CLARO = "#FBE6E5"
LARANJA_STATUS = "#F59A1B"
LARANJA_CLARO = "#FEF3E2"
CINZA_STATUS = "#9AA5B1"
CINZA_CLARO = "#ECEEF1"

STATUS_CONFIG = {
    "Disponível": {"cor": VERDE, "bg": VERDE_CLARO, "icone": "🟢"},
    "Ocupado": {"cor": VERMELHO, "bg": VERMELHO_CLARO, "icone": "🔴"},
    "Limpeza": {"cor": LARANJA_STATUS, "bg": LARANJA_CLARO, "icone": "🟠"},
    "Indisponível": {"cor": CINZA_STATUS, "bg": CINZA_CLARO, "icone": "⚪"},
}

CATEGORIAS = ["Standard", "Duplo", "Luxo", "Super Luxo", "Suíte"]
STATUS_OPCOES = ["Disponível", "Ocupado", "Limpeza", "Indisponível"]


# ----------------------------------------------------------------------
# DADOS INICIAIS / MOCK DOS 10 QUARTOS (Cenário Real do Hotel)
# ----------------------------------------------------------------------
QUARTOS_PADRAO = [
    {"numero": 101, "categoria": "Standard", "status": "Disponível", "observacao": "—"},
    {"numero": 102, "categoria": "Standard", "status": "Ocupado", "observacao": "Hóspede: Silva"},
    {"numero": 103, "categoria": "Standard", "status": "Disponível", "observacao": "—"},
    {"numero": 104, "categoria": "Duplo", "status": "Disponível", "observacao": "—"},
    {"numero": 105, "categoria": "Duplo", "status": "Limpeza", "observacao": "Higienização"},
    {"numero": 201, "categoria": "Luxo", "status": "Disponível", "observacao": "—"},
    {"numero": 202, "categoria": "Luxo", "status": "Limpeza", "observacao": "Troca de enxoval"},
    {"numero": 203, "categoria": "Luxo", "status": "Ocupado", "observacao": "Hóspede: Santos"},
    {"numero": 204, "categoria": "Super Luxo", "status": "Disponível", "observacao": "—"},
    {"numero": 205, "categoria": "Suíte", "status": "Disponível", "observacao": "—"},
]


# ----------------------------------------------------------------------
# CAMADA DE DADOS: BANCO SQLITE COM FALLBACK RESILIENTE
# ----------------------------------------------------------------------
def _carregar_quartos_db():
    """Tenta carregar os quartos e ocupação real do banco de dados SQLite."""
    quartos = [dict(q) for q in QUARTOS_PADRAO]
    try:
        conn = sqlite3.connect("databank/sistema-hotelaria.db")
        cur = conn.cursor()

        # 1. Tenta sincronizar status com a tabela Unidade_Habitacional
        try:
            cur.execute("SELECT numeracao, status FROM Unidade_Habitacional")
            rows = cur.fetchall()
            if rows:
                mapa_status = {
                    "Livre e limpa": "Disponível",
                    "Em limpeza": "Limpeza",
                    "Hospede na casa": "Ocupado",
                    "Reservado": "Ocupado",
                    "Indisponível": "Indisponível",
                }
                for num, st in rows:
                    st_normalizado = mapa_status.get(st, st)
                    for q in quartos:
                        if q["numero"] == num:
                            q["status"] = st_normalizado
        except Exception:
            pass

        # 2. Tenta buscar hóspede ativo da estadia/reserva para a coluna Observação
        try:
            cur.execute("""
                SELECT e.id_uh, h.nome FROM Estadias e
                JOIN Hospedes h ON e.id_hospede = h.id
                WHERE e.status IN ('check-in feito', 'em aberto')
            """)
            estadias = cur.fetchall()
            for id_uh, nome_hospede in estadias:
                sobrenome = nome_hospede.strip().split()[-1] if nome_hospede else "Hóspede"
                for q in quartos:
                    if q["numero"] == id_uh:
                        q["status"] = "Ocupado"
                        q["observacao"] = f"Hóspede: {sobrenome}"
        except Exception:
            pass

        conn.close()
    except Exception:
        pass
    return quartos


def _salvar_status_quarto_db(numero, categoria, status):
    """Atualiza o status e categoria da UH no banco de dados."""
    try:
        conn = sqlite3.connect("databank/sistema-hotelaria.db")
        cur = conn.cursor()

        # Normaliza para a convenção da tabela Unidade_Habitacional
        status_map = {
            "Disponível": "Livre e limpa",
            "Limpeza": "Em limpeza",
            "Ocupado": "Hospede na casa",
            "Indisponível": "Indisponível",
        }
        st_db = status_map.get(status, "Livre e limpa")

        try:
            cur.execute("""
                UPDATE Unidade_Habitacional
                SET status = ?, ultima_att_dia = date('now', 'localtime'), ultima_att_hora = time('now', 'localtime')
                WHERE numeracao = ?
            """, (st_db, numero))
            conn.commit()
        except Exception:
            pass

        conn.close()
        return True, "Quarto atualizado com sucesso."
    except Exception as e:
        return False, str(e)


# ----------------------------------------------------------------------
# CLASSE PRINCIPAL: TelaUH
# ----------------------------------------------------------------------
class TelaUH(TelaBase):
    """
    Tela de Unidade Habitacional (antiga Apartamentos).
    """

    MESES = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    DIAS_SEMANA = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, app, **kwargs)
        self.configure(fg_color=FUNDO_DIREITO)
        self._img_refs = []
        self._quartos = []

        # Estado do calendário
        hoje = date.today()
        self.ano_atual = hoje.year
        self.mes_atual = hoje.month
        self.dia_selecionado = hoje.day

        self._criar_cabecalho()

        # Scroll geral
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self._scroll.grid_columnconfigure(0, weight=1)

        # 1. Grid superior (Dados do Quarto + Calendário)
        self._criar_secao_superior()

        # 2. Card inferior (Ocupação dos Quartos)
        self._criar_card_ocupacao()

    def ao_exibir(self):
        """Atualiza a lista de quartos toda vez que a tela for exibida."""
        self._carregar_dados()

    # ------------------------------------------------------------------
    # CABEÇALHO
    # ------------------------------------------------------------------
    def _criar_cabecalho(self):
        cab = ctk.CTkFrame(self, fg_color=BRANCO, corner_radius=0, height=80)
        cab.pack(fill="x")
        cab.pack_propagate(False)

        # Onda decorativa superior direita
        img_onda = montar_imagem_lateral(220, 80, altura_onda=80)
        if img_onda is None:
            img_onda = carregar_imagem("onda_reserva_superior.png", (220, 80))
        if img_onda:
            self._img_refs.append(img_onda)
            ctk.CTkLabel(cab, text="", image=img_onda).place(relx=1.0, rely=0, anchor="ne")

        # Ícone de quarto/cama
        img_ico = carregar_imagem("icone_cama.png", (42, 42)) or carregar_imagem("icone_cama_btn.png", (42, 42))
        if img_ico:
            self._img_refs.append(img_ico)
            lbl_ico = ctk.CTkLabel(cab, text="", image=img_ico)
        else:
            lbl_ico = ctk.CTkLabel(cab, text="🛏", font=(FONTE, 32), text_color=AZUL_ESCURO)
        lbl_ico.place(x=20, rely=0.5, anchor="w")

        textos = ctk.CTkFrame(cab, fg_color="transparent")
        textos.place(x=76, rely=0.5, anchor="w")
        ctk.CTkLabel(
            textos, text="Unidade Habitacional",
            font=ctk.CTkFont(family=FONTE, size=22, weight="bold"),
            text_color=AZUL_ESCURO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            textos, text="Gerencie os quartos do hotel",
            font=ctk.CTkFont(family=FONTE, size=12),
            text_color=TEXTO_CINZA,
        ).pack(anchor="w")

    # ------------------------------------------------------------------
    # SEÇÃO SUPERIOR: DADOS DO QUARTO (ESQUERDA) + CALENDÁRIO (DIREITA)
    # ------------------------------------------------------------------
    def _criar_secao_superior(self):
        grade_topo = ctk.CTkFrame(self._scroll, fg_color="transparent")
        grade_topo.grid(row=0, column=0, sticky="ew", pady=(14, 14))
        grade_topo.grid_columnconfigure(0, weight=1, uniform="topo")
        grade_topo.grid_columnconfigure(1, weight=1, uniform="topo")

        self._criar_card_formulario(grade_topo)
        self._criar_card_calendario(grade_topo)

    # --- CARD 1: DADOS DO QUARTO --------------------------------------
    def _criar_card_formulario(self, parent):
        card = ctk.CTkFrame(parent, fg_color=BRANCO, corner_radius=14,
                             border_width=1, border_color=BORDA_CARD)
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Topo azul
        header = ctk.CTkFrame(card, fg_color=AZUL_CABECALHO, corner_radius=10, height=42)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="Dados do Quarto",
            font=ctk.CTkFont(family=FONTE, size=14, weight="bold"),
            text_color=BRANCO,
        ).pack(side="left", padx=16)

        # Campos
        corpo = ctk.CTkFrame(card, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=16, pady=12)

        # 1. Número do Quarto
        ctk.CTkLabel(
            corpo, text="Número do Quarto:",
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            text_color=AZUL_ESCURO, anchor="w"
        ).pack(fill="x", pady=(2, 4))

        self.ent_numero = ctk.CTkEntry(
            corpo, height=36, font=ctk.CTkFont(family=FONTE, size=13),
            border_color=BORDA_CAMPO, corner_radius=8
        )
        self.ent_numero.insert(0, "101")
        self.ent_numero.pack(fill="x", pady=(0, 10))

        # 2. Categoria
        ctk.CTkLabel(
            corpo, text="Categoria:",
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            text_color=AZUL_ESCURO, anchor="w"
        ).pack(fill="x", pady=(2, 4))

        self.cb_categoria = ctk.CTkComboBox(
            corpo, values=CATEGORIAS, height=36,
            font=ctk.CTkFont(family=FONTE, size=13),
            dropdown_font=ctk.CTkFont(family=FONTE, size=13),
            fg_color=BRANCO, border_color=BORDA_CAMPO,
            button_color="#E2E8F0", button_hover_color="#CBD5E1",
            text_color="#1E293B", corner_radius=8
        )
        self.cb_categoria.set("Standard")
        self.cb_categoria.pack(fill="x", pady=(0, 10))

        # 3. Status
        ctk.CTkLabel(
            corpo, text="Status:",
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            text_color=AZUL_ESCURO, anchor="w"
        ).pack(fill="x", pady=(2, 4))

        self.cb_status = ctk.CTkComboBox(
            corpo, values=[f"{STATUS_CONFIG[s]['icone']} {s}" for s in STATUS_OPCOES],
            height=36,
            font=ctk.CTkFont(family=FONTE, size=13),
            dropdown_font=ctk.CTkFont(family=FONTE, size=13),
            fg_color=BRANCO, border_color=BORDA_CAMPO,
            button_color="#E2E8F0", button_hover_color="#CBD5E1",
            text_color="#1E293B", corner_radius=8
        )
        self.cb_status.set("🟢 Disponível")
        self.cb_status.pack(fill="x", pady=(0, 16))

        # Botões Salvar e Limpar
        botoes = ctk.CTkFrame(corpo, fg_color="transparent")
        botoes.pack(fill="x", pady=(4, 6))

        self.btn_salvar = ctk.CTkButton(
            botoes, text="💾  Salvar", height=38,
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            fg_color=AZUL_ESCURO, hover_color=AZUL_HOVER, text_color=BRANCO,
            corner_radius=8, command=self._on_salvar
        )
        self.btn_salvar.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_limpar = ctk.CTkButton(
            botoes, text="↻  Limpar", height=38,
            font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            fg_color="transparent", hover_color=CINZA_HEADER, text_color=AZUL_ESCURO,
            border_width=1, border_color=BORDA_CARD, corner_radius=8,
            command=self._on_limpar
        )
        self.btn_limpar.pack(side="left", fill="x", expand=True)

    # --- CARD 2: CALENDÁRIO -------------------------------------------
    def _criar_card_calendario(self, parent):
        card = ctk.CTkFrame(parent, fg_color=BRANCO, corner_radius=14,
                             border_width=1, border_color=BORDA_CARD)
        card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Topo azul
        header = ctk.CTkFrame(card, fg_color=AZUL_CABECALHO, corner_radius=10, height=42)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="📅  Calendário",
            font=ctk.CTkFont(family=FONTE, size=14, weight="bold"),
            text_color=BRANCO,
        ).pack(side="left", padx=16)

        conteudo = ctk.CTkFrame(card, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=14, pady=10)

        # Barra de Navegação de Mês/Ano (‹ Novembro 2026 ›)
        nav = ctk.CTkFrame(conteudo, fg_color="transparent", height=34)
        nav.pack(fill="x", pady=(0, 6))

        btn_ant = ctk.CTkButton(
            nav, text="‹", width=28, height=28,
            fg_color="transparent", hover_color=CINZA_HEADER,
            text_color=AZUL_ESCURO, font=(FONTE, 16, "bold"),
            command=self._mes_anterior
        )
        btn_ant.pack(side="left")

        self.lbl_mes_ano = ctk.CTkLabel(
            nav, text="", font=ctk.CTkFont(family=FONTE, size=14, weight="bold"),
            text_color=AZUL_ESCURO
        )
        self.lbl_mes_ano.pack(side="left", expand=True)

        btn_prox = ctk.CTkButton(
            nav, text="›", width=28, height=28,
            fg_color="transparent", hover_color=CINZA_HEADER,
            text_color=AZUL_ESCURO, font=(FONTE, 16, "bold"),
            command=self._mes_proximo
        )
        btn_prox.pack(side="right")

        # Cabeçalho dos dias da semana (Dom, Seg, Ter...)
        semana = ctk.CTkFrame(conteudo, fg_color="transparent", height=24)
        semana.pack(fill="x", pady=(0, 4))
        for col, d in enumerate(self.DIAS_SEMANA):
            semana.grid_columnconfigure(col, weight=1)
            ctk.CTkLabel(
                semana, text=d, font=(FONTE, 11, "bold"),
                text_color=TEXTO_CINZA
            ).grid(row=0, column=col)

        # Grade com os dias do mês
        self.frame_dias = ctk.CTkFrame(conteudo, fg_color="transparent")
        self.frame_dias.pack(fill="both", expand=True)
        for col in range(7):
            self.frame_dias.grid_columnconfigure(col, weight=1)

        self._renderizar_dias_calendario()

    def _renderizar_dias_calendario(self):
        for w in self.frame_dias.winfo_children():
            w.destroy()

        self.lbl_mes_ano.configure(
            text=f"{self.MESES[self.mes_atual]} {self.ano_atual}"
        )

        # Calendar com domingo como primeiro dia (calendar.setfirstweekday(6))
        cal = calendar.Calendar(firstweekday=6)
        matriz = cal.monthdayscalendar(self.ano_atual, self.mes_atual)

        for r, sem in enumerate(matriz):
            for c, dia in enumerate(sem):
                if dia == 0:
                    lbl = ctk.CTkLabel(self.frame_dias, text="", height=28)
                    lbl.grid(row=r, column=c, padx=1, pady=1, sticky="nsew")
                else:
                    ativo = (dia == self.dia_selecionado)
                    fg = AZUL_ESCURO if ativo else "transparent"
                    tc = BRANCO if ativo else "#222222"
                    hover = AZUL_HOVER if ativo else CINZA_HEADER

                    btn = ctk.CTkButton(
                        self.frame_dias, text=str(dia),
                        height=28, width=28, corner_radius=6,
                        fg_color=fg, hover_color=hover, text_color=tc,
                        font=ctk.CTkFont(family=FONTE, size=11, weight="bold" if ativo else "normal"),
                        command=lambda d=dia: self._selecionar_dia(d)
                    )
                    btn.grid(row=r, column=c, padx=1, pady=1, sticky="nsew")

    def _mes_anterior(self):
        if self.mes_atual == 1:
            self.mes_atual = 12
            self.ano_atual -= 1
        else:
            self.mes_atual -= 1
        self._renderizar_dias_calendario()

    def _mes_proximo(self):
        if self.mes_atual == 12:
            self.mes_atual = 1
            self.ano_atual += 1
        else:
            self.mes_atual += 1
        self._renderizar_dias_calendario()

    def _selecionar_dia(self, dia):
        self.dia_selecionado = dia
        self._renderizar_dias_calendario()

    # ------------------------------------------------------------------
    # CARD INFERIOR: OCUPAÇÃO DOS QUARTOS (TABELA)
    # ------------------------------------------------------------------
    def _criar_card_ocupacao(self):
        card = ctk.CTkFrame(self._scroll, fg_color=BRANCO, corner_radius=14,
                             border_width=1, border_color=BORDA_CARD)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        card.grid_columnconfigure(0, weight=1)

        # Topo azul do card com ícone de cama
        header = ctk.CTkFrame(card, fg_color=AZUL_CABECALHO, corner_radius=10, height=42)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(
            header, text="🛏  Ocupação dos Quartos",
            font=ctk.CTkFont(family=FONTE, size=14, weight="bold"),
            text_color=BRANCO,
        ).pack(side="left", padx=16)

        # Cabeçalho das Colunas
        col_header = ctk.CTkFrame(card, fg_color=CINZA_HEADER, height=36)
        col_header.grid(row=1, column=0, sticky="ew", padx=14, pady=(12, 0))
        col_header.grid_propagate(False)

        colunas = [("Número", 1), ("Categoria", 2), ("Status", 2), ("Observação", 3)]
        for i, (nome, peso) in enumerate(colunas):
            col_header.grid_columnconfigure(i, weight=peso)
            ctk.CTkLabel(
                col_header, text=nome, anchor="w",
                font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
                text_color=TEXTO_CINZA
            ).grid(row=0, column=i, sticky="w", padx=(14 if i == 0 else 8, 8), pady=8)

        # Container das Linhas da Tabela
        self.frame_linhas = ctk.CTkFrame(card, fg_color="transparent")
        self.frame_linhas.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))
        self.frame_linhas.grid_columnconfigure(0, weight=1)

        # Carrega dados
        self._carregar_dados()

    # ------------------------------------------------------------------
    # RENDERIZAÇÃO DA TABELA DE OCUPAÇÃO
    # ------------------------------------------------------------------
    def _carregar_dados(self):
        self._quartos = _carregar_quartos_db()
        self._renderizar_tabela()

    def _renderizar_tabela(self):
        for w in self.frame_linhas.winfo_children():
            w.destroy()

        for i, q in enumerate(self._quartos):
            bg = BRANCO if i % 2 == 0 else "#F8FAFC"

            linha = ctk.CTkFrame(self.frame_linhas, fg_color=bg, height=44, corner_radius=6)
            linha.grid(row=i, column=0, sticky="ew", pady=1)
            linha.grid_propagate(False)

            linha.grid_columnconfigure(0, weight=1)
            linha.grid_columnconfigure(1, weight=2)
            linha.grid_columnconfigure(2, weight=2)
            linha.grid_columnconfigure(3, weight=3)

            # 1. Número
            ctk.CTkLabel(
                linha, text=str(q["numero"]), anchor="w",
                font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
                text_color=AZUL_ESCURO
            ).grid(row=0, column=0, sticky="w", padx=(14, 8), pady=10)

            # 2. Categoria
            ctk.CTkLabel(
                linha, text=q["categoria"], anchor="w",
                font=ctk.CTkFont(family=FONTE, size=13),
                text_color="#1E293B"
            ).grid(row=0, column=1, sticky="w", padx=8, pady=10)

            # 3. Status com Badge
            cfg = STATUS_CONFIG.get(q["status"], STATUS_CONFIG["Disponível"])
            status_badge = ctk.CTkFrame(linha, fg_color="transparent")
            status_badge.grid(row=0, column=2, sticky="w", padx=8, pady=6)

            ctk.CTkLabel(
                status_badge, text=cfg["icone"],
                font=ctk.CTkFont(family=FONTE, size=10)
            ).pack(side="left", padx=(0, 4))

            ctk.CTkLabel(
                status_badge, text=q["status"],
                font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
                text_color=cfg["cor"]
            ).pack(side="left")

            # 4. Observação
            ctk.CTkLabel(
                linha, text=q["observacao"], anchor="w",
                font=ctk.CTkFont(family=FONTE, size=12),
                text_color="#475569" if q["observacao"] != "—" else "#94A3B8"
            ).grid(row=0, column=3, sticky="w", padx=8, pady=10)

            # Clique na linha seleciona para editar no formulário
            linha.bind("<Button-1>", lambda e, quarto=q: self._selecionar_quarto_tabela(quarto))
            for filho in linha.winfo_children():
                filho.bind("<Button-1>", lambda e, quarto=q: self._selecionar_quarto_tabela(quarto))

    def _selecionar_quarto_tabela(self, quarto):
        """Ao clicar na linha da tabela, preenche os campos do formulário para edição."""
        self.ent_numero.delete(0, "end")
        self.ent_numero.insert(0, str(quarto["numero"]))
        self.cb_categoria.set(quarto["categoria"])

        cfg = STATUS_CONFIG.get(quarto["status"], STATUS_CONFIG["Disponível"])
        self.cb_status.set(f"{cfg['icone']} {quarto['status']}")

    # ------------------------------------------------------------------
    # AÇÕES DO FORMULÁRIO (SALVAR / LIMPAR)
    # ------------------------------------------------------------------
    def _on_salvar(self):
        num_str = self.ent_numero.get().strip()
        if not num_str or not num_str.isdigit():
            messagebox.showwarning("Atenção", "Informe um número de quarto válido.", parent=self)
            return

        numero = int(num_str)
        categoria = self.cb_categoria.get().strip()

        status_cru = self.cb_status.get().strip()
        # Remove eventuais emojis (🟢, 🔴...) para pegar o texto puro
        status = status_cru.replace("🟢", "").replace("🔴", "").replace("🟠", "").replace("⚪", "").strip()
        if status not in STATUS_CONFIG:
            status = "Disponível"

        # Atualiza o quarto na memória e tenta persistir no SQLite
        encontrou = False
        for q in self._quartos:
            if q["numero"] == numero:
                q["categoria"] = categoria
                q["status"] = status
                encontrou = True
                break

        if not encontrou:
            self._quartos.append({
                "numero": numero,
                "categoria": categoria,
                "status": status,
                "observacao": "—"
            })
            self._quartos.sort(key=lambda x: x["numero"])

        ok, msg = _salvar_status_quarto_db(numero, categoria, status)
        self._renderizar_tabela()

        messagebox.showinfo("Sucesso", f"Unidade Habitacional Nº {numero} atualizada com sucesso!", parent=self)

    def _on_limpar(self):
        self.ent_numero.delete(0, "end")
        self.cb_categoria.set("Standard")
        self.cb_status.set("🟢 Disponível")


# Alias de retrocompatibilidade para módulos antigos que importam TelaApartamentos
TelaApartamentos = TelaUH


# ----------------------------------------------------------------------
# TESTE ISOLADO DA TELA: python -m views.view_uh
# ----------------------------------------------------------------------
if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    janela = ctk.CTk()
    janela.title("Sistema de Reservas - Hotel")
    janela.geometry("1020x680")

    tela = TelaUH(janela)
    tela.pack(fill="both", expand=True)
    tela.ao_exibir()

    janela.mainloop()
