import ttkbootstrap as tb
from tkinter import messagebox, simpledialog

from auth import login, criar_conta, logout
from finance import (
    salvar_gasto,
    listar_gastos,
    total_mes,
    excluir_gasto,
    definir_meta,
    obter_meta,
    resumo_tipos_mes,
)

from reports import (
    exportar_excel_mes,
    gerar_pdf_mes,
    gerar_pizza_mes,
    listar_meses_com_movimento,
)


def U(s: str) -> str:
    return (s or "").upper()


PLACEHOLDER_DESC = U("Descrição (opcional)")

TIPO_ICON = {
    "Essencial": "💡",
    "Fixo": "🏠",
    "Supérfluo": "🎉",
    "Emergencial": "🧯",
}


def iniciar():
    root = tb.Window(title=U("Controle Financeiro"), themename="darkly", size=(520, 790))

    # ================= ÁREA ROLÁVEL =================
    def criar_area_rolavel(janela):
        container = tb.Frame(janela)
        container.pack(fill="both", expand=True)

        canvas = tb.Canvas(container, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tb.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)

        area_interna = tb.Frame(canvas)
        win_id = canvas.create_window((0, 0), window=area_interna, anchor="nw")

        def ajustar_scroll(_=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def ajustar_largura(event):
            canvas.itemconfig(win_id, width=event.width)

        area_interna.bind("<Configure>", ajustar_scroll)
        canvas.bind("<Configure>", ajustar_largura)

        # Scroll mouse (Windows)
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)

        return area_interna

    area = criar_area_rolavel(root)

    def limpar():
        for w in area.winfo_children():
            w.destroy()

    # ================= LOGIN =================
    def tela_login():
        limpar()
        tb.Label(area, text=U("🔐 Login"), font=("Segoe UI", 20, "bold")).pack(pady=12)

        user = tb.Entry(area, width=34)
        user.pack(pady=6)

        senha = tb.Entry(area, show="*", width=34)
        senha.pack(pady=6)

        def entrar():
            ok = login(user.get(), senha.get())
            if ok:
                tela_home()

        tb.Button(area, text=U("Entrar"), width=32, bootstyle="primary", command=entrar).pack(pady=10)
        tb.Button(area, text=U("Criar Conta"), width=32, bootstyle="secondary", command=tela_criar).pack(pady=3)

    def tela_criar():
        limpar()
        tb.Label(area, text=U("Criar Conta"), font=("Segoe UI", 20, "bold")).pack(pady=12)

        user = tb.Entry(area, width=34)
        user.pack(pady=6)

        senha = tb.Entry(area, show="*", width=34)
        senha.pack(pady=6)

        def criar():
            criar_conta(user.get(), senha.get())
            tela_login()

        tb.Button(area, text=U("Criar"), width=32, bootstyle="success", command=criar).pack(pady=10)
        tb.Button(area, text=U("Voltar"), width=32, command=tela_login).pack(pady=3)

    # ================= RELATÓRIOS =================
    def tela_relatorios():
        limpar()

        tb.Label(area, text=U("📄 Relatórios"), font=("Segoe UI", 20, "bold")).pack(pady=(8, 6))
        tb.Label(area, text=U("Escolha o mês e o formato do arquivo."), font=("Segoe UI", 11)).pack(pady=(0, 10))

        try:
            meses = listar_meses_com_movimento()
        except Exception as e:
            messagebox.showerror(U("Erro"), str(e))
            meses = []

        if not meses:
            box_empty = tb.Labelframe(area, text=U("⚠️ Sem dados"), bootstyle="warning", padding=12)
            box_empty.pack(padx=14, pady=10, fill="x")
            tb.Label(box_empty, text=U("Nenhum lançamento encontrado para gerar relatórios.")).pack(anchor="w")
            tb.Button(area, text=U("Voltar"), width=32, command=tela_home).pack(pady=10)
            return

        labels = [x[0] for x in meses]
        mapa = {x[0]: (x[1], x[2]) for x in meses}

        box = tb.Labelframe(area, text=U("⚙️ Configurações"), bootstyle="warning", padding=12)
        box.pack(padx=14, pady=10, fill="x")

        linha_mes = tb.Frame(box)
        linha_mes.pack(fill="x", pady=6)
        tb.Label(linha_mes, text=U("MÊS:"), font=("Segoe UI", 11, "bold")).pack(side="left")

        mes_cb = tb.Combobox(linha_mes, values=labels, state="readonly", width=22)
        mes_cb.set(labels[0])
        mes_cb.pack(side="left", padx=10)

        tb.Label(box, text=U("FORMATO:"), font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(10, 4))

        formato = tb.StringVar(value="PIZZA")
        formatos = tb.Frame(box)
        formatos.pack(fill="x")

        tb.Radiobutton(formatos, text=U("📊 Pizza (PNG)"), value="PIZZA", variable=formato).pack(side="left", padx=6)
        tb.Radiobutton(formatos, text=U("📄 PDF"), value="PDF", variable=formato).pack(side="left", padx=6)
        tb.Radiobutton(formatos, text=U("📈 Excel"), value="EXCEL", variable=formato).pack(side="left", padx=6)

        status_box = tb.Labelframe(area, text=U("✅ Resultado"), bootstyle="warning", padding=12)
        status_box.pack(padx=14, pady=(0, 10), fill="x")

        status_var = tb.StringVar(value=U("Nenhum arquivo gerado ainda."))
        tb.Label(status_box, textvariable=status_var, wraplength=470).pack(anchor="w")

        def gerar():
            try:
                label = mes_cb.get()
                year, month = mapa[label]

                f = formato.get()
                if f == "PIZZA":
                    path = gerar_pizza_mes(year, month)
                elif f == "PDF":
                    path = gerar_pdf_mes(year, month)
                else:
                    path = exportar_excel_mes(year, month)

                status_var.set(U(f"Arquivo gerado com sucesso:\n{path}"))
            except Exception as e:
                messagebox.showerror(U("Erro"), str(e))

        botoes = tb.Frame(area)
        botoes.pack(pady=10)

        tb.Button(botoes, text=U("Gerar"), width=18, bootstyle="success", command=gerar).pack(side="left", padx=8, ipady=4)
        tb.Button(botoes, text=U("Voltar"), width=18, bootstyle="secondary", command=tela_home).pack(side="left", padx=8, ipady=4)

    # ======== CARD PREMIUM (clicável) ========
    def criar_card_acao(parent, icon_txt, titulo, subtitulo, bootstyle, command):
        card = tb.Labelframe(parent, bootstyle=bootstyle, padding=14)
        card.pack(side="left", expand=True, fill="both", padx=8)

        lbl_icon = tb.Label(card, text=icon_txt, font=("Segoe UI", 22, "bold"))
        lbl_icon.pack()

        lbl_title = tb.Label(card, text=U(titulo), font=("Segoe UI", 12, "bold"))
        lbl_title.pack(pady=(4, 0))

        lbl_sub = tb.Label(card, text=U(subtitulo), font=("Segoe UI", 9))
        lbl_sub.pack()

        def clique(_=None):
            command()

        card.bind("<Button-1>", clique)
        lbl_icon.bind("<Button-1>", clique)
        lbl_title.bind("<Button-1>", clique)
        lbl_sub.bind("<Button-1>", clique)

        for w in (card, lbl_icon, lbl_title, lbl_sub):
            w.configure(cursor="hand2")

        return card

    # ================= DASHBOARD =================
    def tela_home():
        limpar()

        tb.Label(area, text=U("📊 Dashboard Financeiro"), font=("Segoe UI", 20, "bold")).pack(pady=12)

        try:
            entradas, saidas = total_mes()
            saldo = entradas - saidas
        except Exception as e:
            messagebox.showerror(U("Erro no dashboard"), str(e))
            entradas, saidas, saldo = 0.0, 0.0, 0.0

        # ===== META + PROGRESSO =====
        try:
            meta = obter_meta()
        except Exception as e:
            meta = None
            messagebox.showerror(U("Erro"), U(f"Falha ao carregar meta: {e}"))

        def definir_meta_ui(valor_atual=None):
            try:
                novo = simpledialog.askfloat(
                    U("Meta mensal"),
                    U("Defina sua meta de gastos para este mês (ex: 1200.00):"),
                    initialvalue=float(valor_atual) if valor_atual else None,
                    minvalue=0.0
                )
                if novo is None:
                    return
                definir_meta(novo)
                tela_home()
            except Exception as e:
                messagebox.showerror(U("Erro"), U(f"Não foi possível definir meta: {e}"))

        meta_box = tb.Labelframe(area, text=U("🎯 Meta de gastos do mês"), bootstyle="warning", padding=12)
        meta_box.pack(padx=14, pady=(8, 10), fill="x")

        if not meta or meta <= 0:
            tb.Label(meta_box, text=U("Nenhuma meta definida."), font=("Segoe UI", 11)).pack(anchor="w")
            tb.Button(meta_box, text=U("Definir meta"), bootstyle="warning",
                      command=lambda: definir_meta_ui()).pack(pady=6, anchor="w")
        else:
            usado_pct = min(max((saidas / meta) * 100, 0), 200)
            restante = meta - saidas

            if saidas > meta:
                estilo = "danger"
                status = U(f"😈 Meta estourada em R$ {abs(restante):.2f}")
            else:
                estilo = "success"
                status = U(f"😇 Restam R$ {restante:.2f}")

            tb.Label(meta_box, text=U(f"Meta: R$ {meta:.2f} | Gastos: R$ {saidas:.2f}"),
                     font=("Segoe UI", 11)).pack(anchor="w")
            pb = tb.Progressbar(meta_box, maximum=100, value=min(usado_pct, 100), bootstyle=estilo)
            pb.pack(fill="x", pady=6)
            tb.Label(meta_box, text=U(f"{usado_pct:.1f}% usado — {status}"),
                     font=("Segoe UI", 11, "bold")).pack(anchor="w")

            tb.Button(meta_box, text=U("Editar meta"), bootstyle="warning-outline",
                      command=lambda: definir_meta_ui(meta)).pack(pady=6, anchor="w")

        # Card grande central: SALDO
        card_saldo = tb.Labelframe(area, text=U("📊 Saldo"), bootstyle="info", padding=14)
        card_saldo.pack(padx=14, pady=(0, 10), fill="x")
        tb.Label(card_saldo, text=U(f"R$ {saldo:.2f}"), font=("Segoe UI", 22, "bold")).pack(pady=8)

        # Entradas e Saídas embaixo
        linha = tb.Frame(area)
        linha.pack(padx=14, pady=(0, 10), fill="x")

        card_entradas = tb.Labelframe(linha, text=U("💰 Entradas"), bootstyle="success", padding=12)
        card_entradas.pack(side="left", expand=True, fill="both", padx=(0, 8))
        tb.Label(card_entradas, text=U(f"R$ {entradas:.2f}"), font=("Segoe UI", 14, "bold")).pack(pady=10)

        card_saidas = tb.Labelframe(linha, text=U("💸 Saídas"), bootstyle="danger", padding=12)
        card_saidas.pack(side="left", expand=True, fill="both", padx=(8, 0))
        tb.Label(card_saidas, text=U(f"R$ {saidas:.2f}"), font=("Segoe UI", 14, "bold")).pack(pady=10)

        # ===== RESUMO POR TIPO =====
        try:
            resumo = resumo_tipos_mes()
        except Exception as e:
            resumo = {"Essencial": 0.0, "Fixo": 0.0, "Supérfluo": 0.0, "Emergencial": 0.0}
            messagebox.showerror(U("Erro"), U(f"Falha ao carregar resumo por tipo: {e}"))

        resumo_box = tb.Labelframe(area, text=U("🧾 Gastos por tipo (mês)"), bootstyle="warning", padding=10)
        resumo_box.pack(padx=14, pady=(0, 10), fill="x")

        grid = tb.Frame(resumo_box)
        grid.pack(fill="x")
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        def mini_card(parent, tipo, valor, r, c):
            ico = TIPO_ICON.get(tipo, "")
            box = tb.Labelframe(parent, text=U(f"{ico} {tipo}"), bootstyle="warning", padding=10)
            box.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")
            tb.Label(box, text=U(f"R$ {valor:.2f}"), font=("Segoe UI", 12, "bold")).pack()

        mini_card(grid, "Essencial", resumo.get("Essencial", 0.0), 0, 0)
        mini_card(grid, "Fixo", resumo.get("Fixo", 0.0), 0, 1)
        mini_card(grid, "Supérfluo", resumo.get("Supérfluo", 0.0), 1, 0)
        mini_card(grid, "Emergencial", resumo.get("Emergencial", 0.0), 1, 1)

        # ===== CARDS PREMIUM (no lugar dos botões) =====
        cards_row = tb.Frame(area)
        cards_row.pack(padx=14, pady=(6, 6), fill="x")

        criar_card_acao(
            cards_row,
            "＋",
            "NOVO LANÇAMENTO",
            "REGISTRAR ENTRADA OU SAÍDA",
            "success",
            tela_gastos
        )
        criar_card_acao(
            cards_row,
            "📄",
            "RELATÓRIOS",
            "EXPORTAR PDF / EXCEL / PIZZA",
            "warning",
            tela_relatorios
        )

        tb.Separator(area).pack(fill="x", pady=10)
        tb.Label(area, text=U("Últimos lançamentos"), font=("Segoe UI", 12, "bold")).pack(pady=6)

        try:
            gastos = listar_gastos(10)
        except Exception as e:
            messagebox.showerror(U("Erro ao listar gastos"), str(e))
            gastos = []

        if not gastos:
            tb.Label(area, text=U("Nenhum lançamento ainda.")).pack(pady=6)
        else:
            lista = tb.Frame(area)
            lista.pack(fill="x", padx=10)

            for g in gastos:
                gasto_id, data, mov, cat, desc, val, tipo_gasto, periodicidade = g
                data_str = data.strftime("%d/%m") if hasattr(data, "strftime") else str(data)

                extra = ""
                if tipo_gasto:
                    extra = f" • {TIPO_ICON.get(tipo_gasto,'')} {U(tipo_gasto)}"
                    if tipo_gasto == "Fixo" and periodicidade:
                        extra += f" ({U(periodicidade)})"

                linha_item = tb.Frame(lista)
                linha_item.pack(fill="x", pady=2)

                tb.Label(
                    linha_item,
                    text=U(f"{data_str} • {mov}{extra} • {desc} — R$ {float(val):.2f}"),
                    anchor="w",
                ).pack(side="left", fill="x", expand=True)

                def make_delete_callback(_id):
                    def _cb():
                        if messagebox.askyesno(U("Excluir"), U("Tem certeza que deseja excluir este lançamento?")):
                            try:
                                excluir_gasto(_id)
                                tela_home()
                            except Exception as e:
                                messagebox.showerror(U("Erro"), U(f"Não foi possível excluir: {e}"))
                    return _cb

                tb.Button(
                    linha_item,
                    text="✕",
                    width=3,
                    bootstyle="danger",
                    command=make_delete_callback(gasto_id),
                ).pack(side="right", padx=6)

        tb.Button(
            area,
            text=U("Logout"),
            width=32,
            bootstyle="danger",
            command=lambda: (logout(), tela_login())
        ).pack(pady=12)

    # ================= LANÇAMENTOS =================
    def tela_gastos():
        limpar()
        tb.Label(area, text=U("Novo Lançamento"), font=("Segoe UI", 20, "bold")).pack(pady=12)

        movimento = tb.Combobox(area, values=[U("Entrada"), U("Saída")], state="readonly", width=30)
        movimento.set(U("Saída"))
        movimento.pack(pady=6)

        tipo_gasto = tb.Combobox(
            area,
            values=[U("Essencial"), U("Fixo"), U("Supérfluo"), U("Emergencial")],
            state="readonly",
            width=30
        )
        tipo_gasto.set(U("Essencial"))
        tipo_gasto.pack(pady=6)

        periodicidade_frame = tb.Frame(area)
        periodicidade_cb = tb.Combobox(
            periodicidade_frame,
            values=[U("Diário"), U("Semanal"), U("Mensal"), U("Anual")],
            state="readonly",
            width=30
        )
        periodicidade_cb.set(U("Mensal"))

        def atualizar_periodicidade(_=None):
            if tipo_gasto.get() == U("Fixo"):
                periodicidade_frame.pack(after=tipo_gasto, pady=6)
                periodicidade_cb.pack()
            else:
                periodicidade_cb.pack_forget()
                periodicidade_frame.pack_forget()

        tipo_gasto.bind("<<ComboboxSelected>>", atualizar_periodicidade)
        atualizar_periodicidade()

        descricao = tb.Entry(area, width=33)
        descricao.insert(0, PLACEHOLDER_DESC)
        descricao.pack(pady=6)

        def on_focus_in(_):
            if descricao.get() == PLACEHOLDER_DESC:
                descricao.delete(0, "end")

        def on_focus_out(_):
            if not descricao.get().strip():
                descricao.delete(0, "end")
                descricao.insert(0, PLACEHOLDER_DESC)

        descricao.bind("<FocusIn>", on_focus_in)
        descricao.bind("<FocusOut>", on_focus_out)

        valor = tb.Entry(area, width=33)
        valor.insert(0, "0.00")
        valor.pack(pady=6)

        def salvar():
            try:
                v = float(valor.get().replace(",", "."))
            except:
                messagebox.showerror(U("Erro"), U("Valor inválido. Ex: 25.90"))
                return

            desc = descricao.get().strip()
            if desc == PLACEHOLDER_DESC or not desc:
                desc = U("Sem descrição")

            tg_map = {"ESSENCIAL": "Essencial", "FIXO": "Fixo", "SUPÉRFLUO": "Supérfluo", "EMERGENCIAL": "Emergencial"}
            tg = tg_map.get(tipo_gasto.get(), tipo_gasto.get())

            per = periodicidade_cb.get() if tipo_gasto.get() == U("Fixo") else None
            if per:
                per_map = {"DIÁRIO": "Diário", "SEMANAL": "Semanal", "MENSAL": "Mensal", "ANUAL": "Anual"}
                per = per_map.get(per, per)

            mov = "Entrada" if movimento.get() == U("Entrada") else "Saída"
            categoria_salva = tg

            try:
                salvar_gasto(mov, categoria_salva, desc, v, tg, per)
            except Exception as e:
                messagebox.showerror(U("Erro"), U(f"Falha ao salvar: {e}"))
                return

            tela_home()

        tb.Button(area, text=U("Salvar"), width=32, bootstyle="success", command=salvar).pack(pady=10)
        tb.Button(area, text=U("Voltar"), width=32, command=tela_home).pack(pady=3)

    tela_login()
    root.mainloop()
