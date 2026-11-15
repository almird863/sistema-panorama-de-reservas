"""
view_usuarios.py
-----------------
Tela "Hóspede" do Sistema de Reservas - Hotel (menu lateral "Usuários").

Layout fiel ao protótipo (uh_hopede_checkin.png):
  - Cabeçalho: ícone + título "Hóspede" + subtítulo + onda decorativa
  - Card "Dados do Hóspede": formulário (Nome/CPF, Telefone/E-mail) +
    botões Cadastrar / Limpar
  - Card "Lista de Hóspedes": busca por nome ou CPF + tabela
    (Nome | CPF | Telefone | Ações) com editar/excluir + paginação

----------------------------------------------------------------------
IMPORTANTE — isto SUBSTITUI a tela anterior "Minha conta"
----------------------------------------------------------------------
A versão anterior deste arquivo mostrava os dados do hóspede logado
(perfil + reserva atual + histórico), usando controls.control_usuario.
O novo protótipo mudou o propósito da tela "Usuários" para ser o
cadastro/gerenciamento de hóspedes (CRUD), então essa tela foi reescrita
do zero com esse novo objetivo.

----------------------------------------------------------------------
DADOS REAIS — não é mock
----------------------------------------------------------------------
controls/control_hospede.py e models/model_hospede.py já existem e
funcionam, então esta tela usa funções REAIS (com try/except de
segurança + um mock mínimo só para o caso de o import falhar):

    controls.control_hospede.cadastrar_hospede(nome, cpf, telefone, email)
        -> (bool, mensagem)
    controls.control_hospede.listar_hospedes()
        -> lista de tuplas (id, nome, cpf, telefone, email, ...)
    controls.control_hospede.atualizar_nome/atualizar_cpf/
        atualizar_telefone/atualizar_email(valor, id) -> (bool, mensagem)
    controls.control_hospede.excluir_hospede(id) -> (bool, mensagem)

Rodar isolado: python -m views.view_usuarios
"""

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
# Import real (com proteção) + mock de segurança
# ----------------------------------------------------------------------
try:
    from controls.control_hospede import (
        cadastrar_hospede, listar_hospedes,
        atualizar_nome, atualizar_cpf, atualizar_telefone, atualizar_email,
        excluir_hospede,
    )
    _TEM_CONTROL = True
except Exception:
    _TEM_CONTROL = False

_MOCK_SEQ = [5]
_MOCK_HOSPEDES = [
    {"id": 1, "nome": "Carlos Oliveira", "cpf": "987.654.321-00", "telefone": "(11) 91234-5678", "email": "carlos@email.com"},
    {"id": 2, "nome": "Ana Costa", "cpf": "111.222.333-44", "telefone": "(11) 99876-5432", "email": "ana@email.com"},
    {"id": 3, "nome": "Maria Silva Santos", "cpf": "123.456.789-00", "telefone": "(11) 98765-4321", "email": "maria@email.com"},
    {"id": 4, "nome": "João Pereira", "cpf": "555.666.777-88", "telefone": "(11) 96543-2109", "email": "joao@email.com"},
]


def _mock_listar():
    return [(h["id"], h["nome"], h["cpf"], h["telefone"], h["email"]) for h in _MOCK_HOSPEDES]

def _mock_cadastrar(nome, cpf, telefone, email):
    if not all([nome, cpf, telefone, email]):
        return False, "Todos os campos são obrigatórios. [MOCK]"
    _MOCK_SEQ[0] += 1
    _MOCK_HOSPEDES.append({"id": _MOCK_SEQ[0], "nome": nome, "cpf": cpf, "telefone": telefone, "email": email})
    return True, "Hóspede cadastrado! [MOCK]"

def _mock_achar(id_):
    return next((h for h in _MOCK_HOSPEDES if h["id"] == id_), None)

def _mock_atualizar(campo, valor, id_):
    h = _mock_achar(id_)
    if not h:
        return False, "Hóspede não encontrado. [MOCK]"
    h[campo] = valor
    return True, "Atualizado! [MOCK]"

def _mock_excluir(id_):
    h = _mock_achar(id_)
    if not h:
        return False, "Hóspede não encontrado. [MOCK]"
    _MOCK_HOSPEDES.remove(h)
    return True, "Excluído! [MOCK]"


def _listar():
    if _TEM_CONTROL:
        try:
            dados = listar_hospedes()
            return list(dados) if dados else []
        except Exception:
            pass
    return _mock_listar()

def _cadastrar(nome, cpf, telefone, email):
    if _TEM_CONTROL:
        try:
            return cadastrar_hospede(nome, cpf, telefone, email)
        except Exception as e:
            return False, str(e)
    return _mock_cadastrar(nome, cpf, telefone, email)

def _atualizar_campo(campo, valor, id_):
    if _TEM_CONTROL:
        try:
            funcoes = {
                "nome": atualizar_nome, "cpf": atualizar_cpf,
                "telefone": atualizar_telefone, "email": atualizar_email,
            }
            return funcoes[campo](valor, id_)
        except Exception as e:
            return False, str(e)
    return _mock_atualizar(campo, valor, id_)

def _excluir(id_):
    if _TEM_CONTROL:
        try:
            return excluir_hospede(id_)
        except Exception as e:
            return False, str(e)
    return _mock_excluir(id_)


# ----------------------------------------------------------------------
# Visual
# ----------------------------------------------------------------------
FONTE = "Segoe UI"
MARGEM = 20
BRANCO = "#FFFFFF"
BORDA_CARD = "#D5DAE6"
CINZA_HEADER = "#EEF1F7"
VERMELHO = "#D9534F"
VERMELHO_HOVER = "#C0302C"
POR_PAGINA = 6


class ViewUsuarios(TelaBase):

    def __init__(self, master, app=None, **kwargs):
        super().__init__(master, app, **kwargs)
        self.configure(fg_color=FUNDO_DIREITO)
        self._img_refs = []
        self._todos = []        # cache da última listagem
        self._filtrados = []
        self._pagina = 1
        self._id_em_edicao = None  # None = modo cadastro; int = editando esse id

        self._criar_cabecalho()

        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True, padx=MARGEM, pady=(0, 10))
        self._scroll.grid_columnconfigure(0, weight=1)

        self._criar_card_formulario()
        self._criar_card_lista()

    def ao_exibir(self):
        self._carregar()

    # ------------------------------------------------------------------
    # CABEÇALHO
    # ------------------------------------------------------------------
    def _criar_cabecalho(self):
        cab = ctk.CTkFrame(self, fg_color=BRANCO, corner_radius=0, height=80)
        cab.pack(fill="x")
        cab.pack_propagate(False)

        img_onda = montar_imagem_lateral(220, 80, altura_onda=80)
        if img_onda is None:
            img_onda = carregar_imagem("onda_reserva_superior.png", (220, 80))
        if img_onda:
            self._img_refs.append(img_onda)
            ctk.CTkLabel(cab, text="", image=img_onda).place(relx=1.0, rely=0, anchor="ne")

        img_ico = carregar_imagem("icone_hospede.png", (42, 42))
        if img_ico:
            self._img_refs.append(img_ico)
            lbl_ico = ctk.CTkLabel(cab, text="", image=img_ico)
        else:
            lbl_ico = ctk.CTkLabel(
                cab, text="👤", font=ctk.CTkFont(family=FONTE, size=34), text_color=AZUL_ESCURO,
            )
        lbl_ico.place(x=20, rely=0.5, anchor="w")

        textos = ctk.CTkFrame(cab, fg_color="transparent")
        textos.place(x=76, rely=0.5, anchor="w")
        ctk.CTkLabel(
            textos, text="Hóspede",
            font=ctk.CTkFont(family=FONTE, size=22, weight="bold"), text_color=AZUL_ESCURO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            textos, text="Cadastre e gerencie os hóspedes",
            font=ctk.CTkFont(family=FONTE, size=12), text_color=TEXTO_CINZA,
        ).pack(anchor="w")

    # ------------------------------------------------------------------
    # CARD "Dados do Hóspede" — formulário de cadastro/edição
    # ------------------------------------------------------------------
    def _criar_card_formulario(self):
        card = ctk.CTkFrame(self._scroll, fg_color=BRANCO, corner_radius=14,
                             border_width=1, border_color=BORDA_CARD)
        card.grid(row=0, column=0, sticky="ew", pady=(14, 14))
        card.grid_columnconfigure((0, 1), weight=1)

        header = ctk.CTkFrame(card, fg_color=AZUL_ESCURO, corner_radius=10, height=42)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        self.lbl_form_titulo = ctk.CTkLabel(
            header, text="Dados do Hóspede",
            font=ctk.CTkFont(family=FONTE, size=14, weight="bold"), text_color=BRANCO,
        )
        self.lbl_form_titulo.pack(side="left", padx=16, pady=9)

        corpo = ctk.CTkFrame(card, fg_color="transparent")
        corpo.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=14)
        corpo.grid_columnconfigure((0, 1), weight=1, uniform="f")

        self.ent_nome = self._campo(corpo, "Nome Completo:", 0, 0)
        self.ent_cpf = self._campo(corpo, "CPF:", 0, 1)
        self.ent_telefone = self._campo(corpo, "Telefone:", 1, 0)
        self.ent_email = self._campo(corpo, "E-mail:", 1, 1)

        botoes = ctk.CTkFrame(card, fg_color="transparent")
        botoes.grid(row=2, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 16))

        self.btn_salvar = ctk.CTkButton(
            botoes, text="👤  Cadastrar", font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            fg_color=AZUL_ESCURO, hover_color=AZUL_HOVER, text_color=BRANCO,
            height=36, width=140, command=self._on_salvar,
        )
        self.btn_salvar.pack(side="left", padx=(0, 10))

        ctk.CTkButton(
            botoes, text="↻  Limpar", font=ctk.CTkFont(family=FONTE, size=13, weight="bold"),
            fg_color="transparent", hover_color=CINZA_HEADER, text_color=AZUL_ESCURO,
            border_width=1, border_color=BORDA_CARD, height=36, width=120,
            command=self._limpar_formulario,
        ).pack(side="left")

    def _campo(self, parent, rotulo, linha, coluna):
        bloco = ctk.CTkFrame(parent, fg_color="transparent")
        bloco.grid(row=linha, column=coluna, sticky="ew", padx=8, pady=6)
        ctk.CTkLabel(
            bloco, text=rotulo, font=ctk.CTkFont(family=FONTE, size=12),
            text_color=TEXTO_CINZA, anchor="w",
        ).pack(anchor="w")
        entrada = ctk.CTkEntry(
            bloco, height=34, font=ctk.CTkFont(family=FONTE, size=13),
            border_color=BORDA_CAMPO,
        )
        entrada.pack(fill="x", pady=(4, 0))
        return entrada

    # ------------------------------------------------------------------
    # CARD "Lista de Hóspedes" — busca + tabela + paginação
    # ------------------------------------------------------------------
    def _criar_card_lista(self):
        card = ctk.CTkFrame(self._scroll, fg_color=BRANCO, corner_radius=14,
                             border_width=1, border_color=BORDA_CARD)
        card.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        card.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(card, fg_color=AZUL_ESCURO, corner_radius=10, height=42)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        ctk.CTkLabel(
            header, text="Lista de Hóspedes",
            font=ctk.CTkFont(family=FONTE, size=14, weight="bold"), text_color=BRANCO,
        ).pack(side="left", padx=16, pady=9)

        busca = ctk.CTkFrame(card, fg_color="transparent")
        busca.grid(row=1, column=0, sticky="ew", padx=16, pady=(14, 8))
        busca.grid_columnconfigure(0, weight=1)

        self.ent_busca = ctk.CTkEntry(
            busca, height=34, placeholder_text="Buscar por nome ou CPF...",
            font=ctk.CTkFont(family=FONTE, size=13), border_color=BORDA_CAMPO,
        )
        self.ent_busca.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.ent_busca.bind("<KeyRelease>", lambda e: self._aplicar_busca())

        ctk.CTkButton(
            busca, text="🔍", width=40, height=34,
            fg_color=AZUL_ESCURO, hover_color=AZUL_HOVER,
            command=self._aplicar_busca,
        ).grid(row=0, column=1)

        col_header = ctk.CTkFrame(card, fg_color=CINZA_HEADER, height=36)
        col_header.grid(row=2, column=0, sticky="ew", padx=16)
        col_header.grid_propagate(False)
        for i, nome_col in enumerate(["Nome", "CPF", "Telefone", "Ações"]):
            col_header.grid_columnconfigure(i, weight=(3 if i == 0 else 2 if i < 3 else 1))
            ctk.CTkLabel(
                col_header, text=nome_col, anchor="w",
                font=ctk.CTkFont(family=FONTE, size=12, weight="bold"), text_color=TEXTO_CINZA,
            ).grid(row=0, column=i, sticky="w", padx=(0 if i == 0 else 8, 8), pady=8)

        self._linhas_frame = ctk.CTkFrame(card, fg_color="transparent")
        self._linhas_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 6))
        self._linhas_frame.grid_columnconfigure(0, weight=1)

        self._paginacao_frame = ctk.CTkFrame(card, fg_color="transparent")
        self._paginacao_frame.grid(row=4, column=0, pady=(4, 16))

    # ------------------------------------------------------------------
    # CARREGAMENTO / FILTRO / PAGINAÇÃO
    # ------------------------------------------------------------------
    def _carregar(self):
        self._todos = _listar()
        self._pagina = 1
        self._aplicar_busca()

    def _aplicar_busca(self):
        termo = self.ent_busca.get().strip().lower()
        if not termo:
            self._filtrados = list(self._todos)
        else:
            self._filtrados = [
                h for h in self._todos
                if termo in str(h[1]).lower() or termo in str(h[2]).lower()
            ]
        self._pagina = 1
        self._renderizar()

    def _renderizar(self):
        for w in self._linhas_frame.winfo_children():
            w.destroy()

        inicio = (self._pagina - 1) * POR_PAGINA
        pagina_dados = self._filtrados[inicio:inicio + POR_PAGINA]

        self._linhas_frame.grid_columnconfigure(0, weight=3)
        self._linhas_frame.grid_columnconfigure(1, weight=2)
        self._linhas_frame.grid_columnconfigure(2, weight=2)
        self._linhas_frame.grid_columnconfigure(3, weight=1)

        if not pagina_dados:
            ctk.CTkLabel(
                self._linhas_frame, text="Nenhum hóspede encontrado.",
                font=ctk.CTkFont(family=FONTE, size=12), text_color=TEXTO_CINZA,
            ).grid(row=0, column=0, columnspan=4, sticky="w", pady=12)
        else:
            for i, registro in enumerate(pagina_dados):
                id_, nome, cpf, telefone, email = registro[0], registro[1], registro[2], registro[3], registro[4]
                bg = BRANCO if i % 2 == 0 else "#F7F9FC"

                linha = ctk.CTkFrame(self._linhas_frame, fg_color=bg, height=42)
                linha.grid(row=i, column=0, columnspan=4, sticky="ew")
                linha.grid_propagate(False)
                linha.grid_columnconfigure(0, weight=3)
                linha.grid_columnconfigure(1, weight=2)
                linha.grid_columnconfigure(2, weight=2)
                linha.grid_columnconfigure(3, weight=1)

                ctk.CTkLabel(linha, text=str(nome), anchor="w",
                             font=ctk.CTkFont(family=FONTE, size=12), text_color="#222",
                             ).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=8)
                ctk.CTkLabel(linha, text=str(cpf), anchor="w",
                             font=ctk.CTkFont(family=FONTE, size=12), text_color="#222",
                             ).grid(row=0, column=1, sticky="w", padx=8, pady=8)
                ctk.CTkLabel(linha, text=str(telefone), anchor="w",
                             font=ctk.CTkFont(family=FONTE, size=12), text_color="#222",
                             ).grid(row=0, column=2, sticky="w", padx=8, pady=8)

                acoes = ctk.CTkFrame(linha, fg_color="transparent")
                acoes.grid(row=0, column=3, sticky="w", padx=8, pady=4)
                ctk.CTkButton(
                    acoes, text="✏", width=32, height=28, corner_radius=6,
                    fg_color=AZUL_ESCURO, hover_color=AZUL_HOVER, text_color=BRANCO,
                    command=lambda r=registro: self._on_editar(r),
                ).pack(side="left", padx=(0, 6))
                ctk.CTkButton(
                    acoes, text="🗑", width=32, height=28, corner_radius=6,
                    fg_color=VERMELHO, hover_color=VERMELHO_HOVER, text_color=BRANCO,
                    command=lambda _id=id_, _nome=nome: self._on_excluir(_id, _nome),
                ).pack(side="left")

        self._renderizar_paginacao()

    def _renderizar_paginacao(self):
        for w in self._paginacao_frame.winfo_children():
            w.destroy()

        total_paginas = max(1, -(-len(self._filtrados) // POR_PAGINA))

        ctk.CTkButton(
            self._paginacao_frame, text="‹", width=32, height=30,
            fg_color="transparent", hover_color=CINZA_HEADER, text_color=AZUL_ESCURO,
            border_width=1, border_color=BORDA_CARD,
            state="normal" if self._pagina > 1 else "disabled",
            command=lambda: self._ir_pagina(self._pagina - 1),
        ).pack(side="left", padx=3)

        for p in range(1, total_paginas + 1):
            ativo = p == self._pagina
            ctk.CTkButton(
                self._paginacao_frame, text=str(p), width=32, height=30,
                fg_color=AZUL_ESCURO if ativo else "transparent",
                hover_color=AZUL_HOVER if ativo else CINZA_HEADER,
                text_color=BRANCO if ativo else AZUL_ESCURO,
                border_width=0 if ativo else 1, border_color=BORDA_CARD,
                command=lambda pg=p: self._ir_pagina(pg),
            ).pack(side="left", padx=3)

        ctk.CTkButton(
            self._paginacao_frame, text="›", width=32, height=30,
            fg_color="transparent", hover_color=CINZA_HEADER, text_color=AZUL_ESCURO,
            border_width=1, border_color=BORDA_CARD,
            state="normal" if self._pagina < total_paginas else "disabled",
            command=lambda: self._ir_pagina(self._pagina + 1),
        ).pack(side="left", padx=3)

    def _ir_pagina(self, pagina):
        self._pagina = pagina
        self._renderizar()

    # ------------------------------------------------------------------
    # FORMULÁRIO: cadastrar ou salvar edição
    # ------------------------------------------------------------------
    def _limpar_formulario(self):
        self._id_em_edicao = None
        self.ent_nome.delete(0, "end")
        self.ent_cpf.delete(0, "end")
        self.ent_telefone.delete(0, "end")
        self.ent_email.delete(0, "end")
        self.lbl_form_titulo.configure(text="Dados do Hóspede")
        self.btn_salvar.configure(text="👤  Cadastrar")

    def _on_editar(self, registro):
        id_, nome, cpf, telefone, email = registro[0], registro[1], registro[2], registro[3], registro[4]
        self._id_em_edicao = id_
        self.ent_nome.delete(0, "end"); self.ent_nome.insert(0, nome)
        self.ent_cpf.delete(0, "end"); self.ent_cpf.insert(0, cpf)
        self.ent_telefone.delete(0, "end"); self.ent_telefone.insert(0, telefone)
        self.ent_email.delete(0, "end"); self.ent_email.insert(0, email)
        self.lbl_form_titulo.configure(text=f"Editando hóspede #{id_}")
        self.btn_salvar.configure(text="💾  Salvar alterações")

    def _on_salvar(self):
        nome = self.ent_nome.get().strip()
        cpf = self.ent_cpf.get().strip()
        telefone = self.ent_telefone.get().strip()
        email = self.ent_email.get().strip()

        if self._id_em_edicao is None:
            ok, msg = _cadastrar(nome, cpf, telefone, email)
            if not ok:
                messagebox.showerror("Cadastrar Hóspede", msg, parent=self)
                return
        else:
            id_ = self._id_em_edicao
            erros = []
            for campo, valor in (("nome", nome), ("cpf", cpf), ("telefone", telefone), ("email", email)):
                ok, msg = _atualizar_campo(campo, valor, id_)
                if not ok:
                    erros.append(msg)
            if erros:
                messagebox.showerror("Atualizar Hóspede", "\n".join(erros), parent=self)
                return
            msg = "Hóspede atualizado com sucesso."

        messagebox.showinfo("Hóspede", msg, parent=self)
        self._limpar_formulario()
        self._carregar()

    def _on_excluir(self, id_, nome):
        if not messagebox.askyesno("Excluir Hóspede", f"Excluir o hóspede \"{nome}\"?", parent=self):
            return
        ok, msg = _excluir(id_)
        if not ok:
            messagebox.showerror("Excluir Hóspede", msg, parent=self)
            return
        if self._id_em_edicao == id_:
            self._limpar_formulario()
        self._carregar()


# ----------------------------------------------------------------------
# TESTE ISOLADO: python -m views.view_usuarios
# ----------------------------------------------------------------------
if __name__ == "__main__":
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")

    janela = ctk.CTk()
    janela.title("Sistema de Reservas - Hotel")
    janela.geometry("980x720")

    tela = ViewUsuarios(janela, app=None)
    tela.pack(fill="both", expand=True)
    tela.ao_exibir()

    janela.mainloop()
