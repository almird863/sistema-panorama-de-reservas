"""
view_checkin.py
----------------
Tela de Check-in / Check-out do Sistema de Reservas - Hotel.

Layout fiel ao protótipo:
  - Cabeçalho: ícone + título/subtítulo + onda decorativa no canto direito
  - 3 cards de contagem lado a lado (Hóspedes no Hotel / Ocupados / Disponíveis)
  - Card "Check-ins de Hoje" — cabeçalho azul-escuro + badge verde + tabela
  - Card "Check-outs de Hoje" — cabeçalho azul-escuro + badge laranja + tabela
  - Botões de ação: ícone quadrado arredondado (✔ azul / seta laranja)

----------------------------------------------------------------------
MOCK — mesma estratégia de view_reserva.py
----------------------------------------------------------------------
Enquanto controls/control_estadia.py não existir, usa dados em memória.
Quando o colega criar o control com as assinaturas abaixo, a troca é
automática (o import no try/except resolve sozinho):

    controls/control_estadia.py
        ListarCheckinsDoDia()   -> [(id, nome, numero_uh, data_hora), ...]
        ListarCheckoutsDoDia()  -> [(id, nome, numero_uh, data_hora), ...]
        ConfirmarCheckin(id)    -> (bool, mensagem)
        RealizarCheckout(id)    -> (bool, mensagem)
        ContarHospedesNoHotel() -> int
        ContarUHsOcupadas()     -> int
        ContarUHsDisponiveis()  -> int

Rodar isolado: python -m views.view_checkin
"""

from datetime import date
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
# Import "otimista" — cai no mock se o control ainda não existir
# ----------------------------------------------------------------------
try:
    from controls.control_estadia import (
        ListarCheckinsDoDia, ListarCheckoutsDoDia,
        ConfirmarCheckin, RealizarCheckout,
        ContarHospedesNoHotel, ContarUHsOcupadas, ContarUHsDisponiveis,
    )
    _TEM_CONTROL = True
except Exception:
    _TEM_CONTROL = False

# ----------------------------------------------------------------------
# MOCK
# ----------------------------------------------------------------------
_HOJE = date.today().strftime("%d/%m/%Y")

_MOCK_CHECKINS = [
    {"id": 1, "hospede": "Carlos Oliveira", "quarto": 101, "data": f"{_HOJE} 09:00"},
    {"id": 2, "hospede": "Ana Costa",        "quarto": 202, "data": f"{_HOJE} 10:30"},
    {"id": 3, "hospede": "João Pereira",     "quarto": 301, "data": f"{_HOJE} 11:00"},
]
_MOCK_CHECKOUTS = [
    {"id": 4, "hospede": "Maria Silva Santos", "quarto": 201, "data": f"{_HOJE} 11:30"},
]


def _mock_listar_checkins():
    return [(r["id"], r["hospede"], r["quarto"], r["data"]) for r in _MOCK_CHECKINS]

def _mock_listar_checkouts():
    return [(r["id"], r["hospede"], r["quarto"], r["data"]) for r in _MOCK_CHECKOUTS]

def _mock_confirmar(id_):
    for i, r in enumerate(_MOCK_CHECKINS):
        if r["id"] == id_:
            _MOCK_CHECKINS.pop(i)
            return True, "Check-in confirmado! [MOCK]"
    return False, "Registro não encontrado. [MOCK]"

def _mock_checkout(id_):
    for i, r in enumerate(_MOCK_CHECKOUTS):
        if r["id"] == id_:
            _MOCK_CHECKOUTS.pop(i)
            return True, "Check-out realizado! [MOCK]"
    return False, "Registro não encontrado. [MOCK]"

def _mock_hospedes():    return 12
def _mock_ocupadas():    return 8
def _mock_disponiveis(): return 4

# Funções de acesso — real ou mock automaticamente
def _listar_checkins():
    if _TEM_CONTROL:
        try: return ListarCheckinsDoDia()
        except Exception: pass
    return _mock_listar_checkins()

def _listar_checkouts():
    if _TEM_CONTROL:
        try: return ListarCheckoutsDoDia()
        except Exception: pass
    return _mock_listar_checkouts()

def _confirmar_checkin(id_):
    if _TEM_CONTROL:
        try: return ConfirmarCheckin(id_)
        except Exception as e: return False, str(e)
    return _mock_confirmar(id_)

def _realizar_checkout(id_):
    if _TEM_CONTROL:
        try: return RealizarCheckout(id_)
        except Exception as e: return False, str(e)
    return _mock_checkout(id_)

def _hospedes():
    if _TEM_CONTROL:
        try: return ContarHospedesNoHotel()
        except Exception: pass
    return _mock_hospedes()

def _ocupadas():
    if _TEM_CONTROL:
        try: return ContarUHsOcupadas()
        except Exception: pass
    return _mock_ocupadas()

def _disponiveis():
    if _TEM_CONTROL:
        try: return ContarUHsDisponiveis()
        except Exception: pass
    return _mock_disponiveis()

# ----------------------------------------------------------------------
# Constantes visuais
# ----------------------------------------------------------------------
FONTE        = "Segoe UI"
MARGEM       = 20
VERDE        = "#2E9E5B"
VERDE_CLARO  = "#E3F3E9"
LARANJA_CLARO = "#FFF0D6"
BORDA_CARD   = "#D5DAE6"
CINZA_HEADER = "#EEF1F7"
BRANCO       = "#FFFFFF"
AZUL_BTN     = "#1B3A7A"


# ======================================================================
# TELA
# ======================================================================
class TelaCheckin(TelaBase):

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, app, **kwargs)
        self.configure(fg_color=FUNDO_DIREITO)
        self._img_refs = []   # guarda referências de imagens (evita GC)

        self._criar_cabecalho()
        self._criar_cards_contagem()

        # área rolável para as tabelas
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self._scroll.pack(fill="both", expand=True, padx=MARGEM, pady=(0, 10))
        self._scroll.grid_columnconfigure(0, weight=1)

        self._criar_tabela_secao(
            parent=self._scroll,
            titulo="Check-ins de Hoje",
            cor_badge=VERDE,
            fg_badge=VERDE_CLARO,
            col_data="Entrada",
            attr_badge="lbl_badge_ci",
            attr_linhas="linhas_ci",
            texto_btn="✔",
            cor_btn=AZUL_BTN,
            hover_btn=AZUL_HOVER,
            callback=self._on_checkin,
            row=0,
        )
        self._criar_tabela_secao(
            parent=self._scroll,
            titulo="Check-outs de Hoje",
            cor_badge=LARANJA,
            fg_badge=LARANJA_CLARO,
            col_data="Saída",
            attr_badge="lbl_badge_co",
            attr_linhas="linhas_co",
            texto_btn="⇥",
            cor_btn=LARANJA,
            hover_btn=LARANJA_HOVER,
            callback=self._on_checkout,
            row=1,
        )

    def ao_exibir(self):
        self._atualizar()

    # ------------------------------------------------------------------
    # CABEÇALHO — ícone + título + onda decorativa
    # ------------------------------------------------------------------
    def _criar_cabecalho(self):
        cab = ctk.CTkFrame(self, fg_color=BRANCO, corner_radius=0, height=80)
        cab.pack(fill="x")
        cab.pack_propagate(False)

        # onda decorativa no canto direito (mesma usada no menu principal)
        img_onda = montar_imagem_lateral(220, 80, altura_onda=80)
        if img_onda is None:
            # fallback: bloco com gradiente laranja
            img_onda = carregar_imagem("onda_reserva_superior.png", (220, 80))
        if img_onda:
            self._img_refs.append(img_onda)
            ctk.CTkLabel(cab, text="", image=img_onda).place(relx=1.0, rely=0, anchor="ne")

        # ícone
        img_ico = carregar_imagem("icone_checkin.png", (42, 42))
        if img_ico:
            self._img_refs.append(img_ico)
            lbl_ico = ctk.CTkLabel(cab, text="", image=img_ico)
        else:
            lbl_ico = ctk.CTkLabel(
                cab, text="🗓",
                font=ctk.CTkFont(family=FONTE, size=34),
                text_color=AZUL_ESCURO,
            )
        lbl_ico.place(x=20, rely=0.5, anchor="w")

        textos = ctk.CTkFrame(cab, fg_color="transparent")
        textos.place(x=76, rely=0.5, anchor="w")

        ctk.CTkLabel(
            textos,
            text="Check-in / Check-out",
            font=ctk.CTkFont(family=FONTE, size=22, weight="bold"),
            text_color=AZUL_ESCURO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            textos,
            text="Gerencie a entrada e saída dos hóspedes",
            font=ctk.CTkFont(family=FONTE, size=12),
            text_color=TEXTO_CINZA,
        ).pack(anchor="w")

    # ------------------------------------------------------------------
    # 3 CARDS DE CONTAGEM
    # ------------------------------------------------------------------
    def _criar_cards_contagem(self):
        faixa = ctk.CTkFrame(self, fg_color="transparent")
        faixa.pack(fill="x", padx=MARGEM, pady=(14, 10))
        faixa.grid_columnconfigure((0, 1, 2), weight=1, uniform="cnt")

        specs = [
            # (emoji_fallback, nome_ico, titulo, cor_numero, attr_label)
            ("👥", "icone_hospedes.png", "Hóspedes no Hotel", AZUL_ESCURO, "lbl_hospedes"),
            ("🛌",  "icone_ocupado.png",  "Ocupados",          AZUL_ESCURO, "lbl_ocupados"),
            ("🛌"
            "",  "icone_livre.png",    "Disponíveis",       AZUL_ESCURO, "lbl_disponiveis"),
        ]
        for col, (emoji, ico_arq, titulo, cor_num, attr) in enumerate(specs):
            card = ctk.CTkFrame(
                faixa, fg_color=BRANCO, corner_radius=14,
                border_width=1, border_color=BORDA_CARD,
            )
            card.grid(
                row=0, column=col,
                padx=(0 if col == 0 else 10, 0),
                sticky="nsew", ipady=10,
            )

            # ícone
            img = carregar_imagem(ico_arq, (38, 38))
            if img:
                self._img_refs.append(img)
                ctk.CTkLabel(card, text="", image=img).pack(pady=(16, 4))
            else:
                ctk.CTkLabel(
                    card, text=emoji,
                    font=ctk.CTkFont(family=FONTE, size=30),
                    text_color=AZUL_ESCURO,
                ).pack(pady=(16, 4))

            # número
            lbl_num = ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(family=FONTE, size=36, weight="bold"),
                text_color=cor_num,
            )
            lbl_num.pack()
            setattr(self, attr, lbl_num)

            # título
            ctk.CTkLabel(
                card, text=titulo,
                font=ctk.CTkFont(family=FONTE, size=12),
                text_color=TEXTO_CINZA,
            ).pack(pady=(2, 16))

    # ------------------------------------------------------------------
    # CARD COM TABELA (check-in ou check-out)
    # ------------------------------------------------------------------
    def _criar_tabela_secao(
        self, parent, titulo, cor_badge, fg_badge, col_data,
        attr_badge, attr_linhas, texto_btn, cor_btn, hover_btn,
        callback, row,
    ):
        card = ctk.CTkFrame(
            parent, fg_color=BRANCO, corner_radius=14,
            border_width=1, border_color=BORDA_CARD,
        )
        card.grid(row=row, column=0, sticky="ew", pady=(0, 14))
        card.grid_columnconfigure(0, weight=1)

        # --- Cabeçalho azul-escuro ---
        header = ctk.CTkFrame(card, fg_color=AZUL_ESCURO, corner_radius=10, height=46)
        header.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text=titulo,
            font=ctk.CTkFont(family=FONTE, size=14, weight="bold"),
            text_color=BRANCO,
        ).grid(row=0, column=0, sticky="w", padx=16, pady=10)

        badge = ctk.CTkLabel(
            header, text="0",
            font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
            text_color=BRANCO,
            fg_color=cor_badge,
            corner_radius=12,
            width=30, height=24,
        )
        badge.grid(row=0, column=1, sticky="e", padx=16, pady=10)
        setattr(self, attr_badge, badge)

        # --- Cabeçalho das colunas ---
        col_header = ctk.CTkFrame(card, fg_color=CINZA_HEADER, corner_radius=0, height=36)
        col_header.grid(row=1, column=0, sticky="ew")
        col_header.grid_propagate(False)
        col_header.grid_columnconfigure(0, weight=3)
        col_header.grid_columnconfigure(1, weight=1)
        col_header.grid_columnconfigure(2, weight=2)
        col_header.grid_columnconfigure(3, weight=1)

        for idx, nome_col in enumerate(["Hóspede", "Quarto", col_data, "Ações"]):
            ctk.CTkLabel(
                col_header, text=nome_col,
                font=ctk.CTkFont(family=FONTE, size=12, weight="bold"),
                text_color=TEXTO_CINZA, anchor="w",
            ).grid(row=0, column=idx, sticky="w",
                   padx=(16 if idx == 0 else 8, 8), pady=8)

        # --- Área de linhas de dados ---
        linhas_frame = ctk.CTkFrame(card, fg_color="transparent")
        linhas_frame.grid(row=2, column=0, sticky="ew", padx=0, pady=(0, 6))
        linhas_frame.grid_columnconfigure(0, weight=1)
        setattr(self, attr_linhas, {
            "frame": linhas_frame,
            "col_data": col_data,
            "texto_btn": texto_btn,
            "cor_btn": cor_btn,
            "hover_btn": hover_btn,
            "callback": callback,
        })

    # ------------------------------------------------------------------
    # RENDERIZAR LINHAS DA TABELA
    # ------------------------------------------------------------------
    def _renderizar(self, attr_linhas, dados):
        cfg = getattr(self, attr_linhas)
        frame: ctk.CTkFrame = cfg["frame"]

        for w in frame.winfo_children():
            w.destroy()

        frame.grid_columnconfigure(0, weight=3)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(2, weight=2)
        frame.grid_columnconfigure(3, weight=1)

        if not dados:
            ctk.CTkLabel(
                frame,
                text="Nenhum registro para hoje.",
                font=ctk.CTkFont(family=FONTE, size=12),
                text_color=TEXTO_CINZA,
            ).grid(row=0, column=0, columnspan=4, sticky="w", padx=16, pady=12)
            return

        for i, (id_, hospede, quarto, data) in enumerate(dados):
            bg = BRANCO if i % 2 == 0 else "#F7F9FC"

            linha = ctk.CTkFrame(frame, fg_color=bg, corner_radius=0, height=42)
            linha.grid(row=i, column=0, columnspan=4, sticky="ew")
            linha.grid_propagate(False)
            linha.grid_columnconfigure(0, weight=3)
            linha.grid_columnconfigure(1, weight=1)
            linha.grid_columnconfigure(2, weight=2)
            linha.grid_columnconfigure(3, weight=1)

            ctk.CTkLabel(
                linha, text=str(hospede), anchor="w",
                font=ctk.CTkFont(family=FONTE, size=12),
                text_color="#222",
            ).grid(row=0, column=0, sticky="w", padx=(16, 8), pady=8)

            ctk.CTkLabel(
                linha, text=str(quarto), anchor="w",
                font=ctk.CTkFont(family=FONTE, size=12),
                text_color="#222",
            ).grid(row=0, column=1, sticky="w", padx=8, pady=8)

            ctk.CTkLabel(
                linha, text=str(data), anchor="w",
                font=ctk.CTkFont(family=FONTE, size=12),
                text_color="#222",
            ).grid(row=0, column=2, sticky="w", padx=8, pady=8)

            ctk.CTkButton(
                linha,
                text=cfg["texto_btn"],
                width=36, height=30,
                font=ctk.CTkFont(family=FONTE, size=16, weight="bold"),
                fg_color=cfg["cor_btn"],
                hover_color=cfg["hover_btn"],
                text_color=BRANCO,
                corner_radius=8,
                command=lambda _id=id_: cfg["callback"](_id),
            ).grid(row=0, column=3, sticky="w", padx=8, pady=6)

    # ------------------------------------------------------------------
    # ATUALIZAÇÃO GERAL
    # ------------------------------------------------------------------
    def _atualizar(self):
        self.lbl_hospedes.configure(text=str(_hospedes()))
        self.lbl_ocupados.configure(text=str(_ocupadas()))
        self.lbl_disponiveis.configure(text=str(_disponiveis()))

        checkins  = _listar_checkins()
        checkouts = _listar_checkouts()

        self.lbl_badge_ci.configure(text=str(len(checkins)))
        self.lbl_badge_co.configure(text=str(len(checkouts)))

        self._renderizar("linhas_ci", checkins)
        self._renderizar("linhas_co", checkouts)

    # ------------------------------------------------------------------
    # CALLBACKS
    # ------------------------------------------------------------------
    def _on_checkin(self, id_):
        ok, msg = _confirmar_checkin(id_)
        if ok:
            self._atualizar()
        else:
            messagebox.showerror("Erro no Check-in", msg, parent=self)

    def _on_checkout(self, id_):
        ok, msg = _realizar_checkout(id_)
        if ok:
            self._atualizar()
        else:
            messagebox.showerror("Erro no Check-out", msg, parent=self)


# ----------------------------------------------------------------------
# TESTE ISOLADO: python -m views.view_checkin
# ----------------------------------------------------------------------
if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    janela = ctk.CTk()
    janela.title("Sistema de Reservas - Hotel")
    janela.geometry("900x680")

    tela = TelaCheckin(janela, app=None)
    tela.pack(fill="both", expand=True)
    tela.ao_exibir()

    janela.mainloop()
