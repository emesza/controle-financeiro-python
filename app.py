from datetime import date
import pandas as pd
import streamlit as st

from auth import login, criar_conta
from finance import (
    definir_meta,
    obter_meta,
    total_mes,
    resumo_tipos_mes,
    listar_gastos,
    salvar_gasto,
    excluir_gasto,
)
from reports import (
    exportar_excel_mes,
    gerar_pdf_mes,
    listar_meses_com_movimento,
)

st.set_page_config(page_title="Controle Financeiro", page_icon="💰", layout="centered")

if "usuario_id" not in st.session_state:
    st.session_state["usuario_id"] = None
if "usuario_nome" not in st.session_state:
    st.session_state["usuario_nome"] = ""


# ================= FUNÇÕES COM CACHE =================
@st.cache_data(ttl=120, show_spinner=False)
def carregar_dados_dashboard(uid: int):
    entradas, saidas = total_mes(uid)
    meta = obter_meta(uid)
    resumo = resumo_tipos_mes(uid)
    gastos = listar_gastos(uid, limite=30)
    return entradas, saidas, meta, resumo, gastos


@st.cache_data(ttl=120, show_spinner=False)
def carregar_meses(uid: int):
    return listar_meses_com_movimento(uid)


def limpar_cache_usuario():
    carregar_dados_dashboard.clear()
    carregar_meses.clear()


# ================= TELA DE LOGIN / CADASTRO =================
def tela_autenticacao():
    st.title("💰 Controle Financeiro")
    st.caption("Acesse sua conta ou crie um cadastro gratuito.")

    aba_login, aba_cadastro = st.tabs(["🔐 Entrar", "📝 Criar Conta"])

    with aba_login:
        with st.form("form_login"):
            apelido = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            entrar = st.form_submit_button("Entrar", use_container_width=True, type="primary")

            if entrar:
                ok, resultado = login(apelido, senha)
                if ok:
                    st.session_state["usuario_id"] = resultado
                    st.session_state["usuario_nome"] = apelido.strip()
                    st.rerun()
                else:
                    st.error(resultado)

    with aba_cadastro:
        with st.form("form_cadastro"):
            novo_apelido = st.text_input("Escolha um usuário")
            nova_senha = st.text_input("Escolha uma senha", type="password")
            cadastrar = st.form_submit_button("Criar Conta", use_container_width=True)

            if cadastrar:
                ok, msg = criar_conta(novo_apelido, nova_senha)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)


# ================= APLICATIVO PRINCIPAL =================
def tela_principal():
    uid = st.session_state["usuario_id"]
    nome = st.session_state["usuario_nome"]

    col_titulo, col_sair = st.columns([4, 1])
    with col_titulo:
        st.title("📊 Painel Financeiro")
        st.caption(f"Olá, **{nome}**!")
    with col_sair:
        st.write("")
        if st.button("Sair", use_container_width=True):
            st.session_state["usuario_id"] = None
            st.session_state["usuario_nome"] = ""
            st.rerun()

    aba_dash, aba_novo, aba_rel = st.tabs(["🏠 Dashboard", "➕ Novo Lançamento", "📄 Relatórios"])

    # ---------------- ABA 1: DASHBOARD ----------------
    with aba_dash:
        entradas, saidas, meta, resumo, gastos = carregar_dados_dashboard(uid)
        saldo = entradas - saidas

        c1, c2, c3 = st.columns(3)
        c1.metric("💰 Entradas (Mês)", f"R$ {entradas:.2f}")
        c2.metric("💸 Saídas (Mês)", f"R$ {saidas:.2f}")
        c3.metric("📊 Saldo", f"R$ {saldo:.2f}")

        st.divider()

        st.subheader("🎯 Meta de Gastos do Mês")
        if meta and meta > 0:
            pct = min((saidas / meta) * 100, 100.0)
            restante = meta - saidas
            st.progress(pct / 100.0)

            if saidas > meta:
                st.error(f"Meta de **R$ {meta:.2f}** estourada em **R$ {abs(restante):.2f}**!")
            else:
                st.success(f"Usado: **R$ {saidas:.2f}** de **R$ {meta:.2f}** ({(saidas/meta)*100:.1f}%) — Restam **R$ {restante:.2f}**")

        with st.expander("Definir ou alterar meta mensal"):
            with st.form("form_meta"):
                nova_meta = st.number_input(
                    "Valor da meta (R$)",
                    min_value=0.0,
                    value=float(meta) if meta else 1000.0,
                    step=50.0,
                )
                if st.form_submit_button("Salvar Meta"):
                    definir_meta(uid, nova_meta)
                    limpar_cache_usuario()
                    st.rerun()

        st.divider()

        st.subheader("🧾 Gastos por Tipo (Mês Atual)")
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("💡 Essencial", f"R$ {resumo['Essencial']:.2f}")
        t2.metric("🏠 Fixo", f"R$ {resumo['Fixo']:.2f}")
        t3.metric("🎉 Supérfluo", f"R$ {resumo['Supérfluo']:.2f}")
        t4.metric("🧯 Emergencial", f"R$ {resumo['Emergencial']:.2f}")

        if sum(resumo.values()) > 0:
            df_chart = pd.DataFrame({
                "Tipo": list(resumo.keys()),
                "Valor (R$)": list(resumo.values()),
            }).set_index("Tipo")
            st.bar_chart(df_chart)

        st.divider()

        st.subheader("🕒 Últimos Lançamentos")
        if not gastos:
            st.info("Nenhum lançamento registrado ainda. Vá na aba **Novo Lançamento** para começar!")
        else:
            for g in gastos:
                gasto_id, dt, mov, cat, desc, val, tipo_gasto, periodicidade = g
                dt_str = dt.strftime("%d/%m/%Y") if hasattr(dt, "strftime") else str(dt)
                icone = "🟢" if mov == "Entrada" else "🔴"
                extra = f" • {tipo_gasto}" if tipo_gasto else ""
                if tipo_gasto == "Fixo" and periodicidade:
                    extra += f" ({periodicidade})"

                col_info, col_del = st.columns([6, 1])
                with col_info:
                    st.write(f"{icone} **{dt_str}** — {desc}{extra} — **R$ {float(val):.2f}**")
                with col_del:
                    if st.button("🗑️", key=f"del_{gasto_id}", help="Excluir lançamento"):
                        excluir_gasto(uid, gasto_id)
                        limpar_cache_usuario()
                        st.rerun()

    # ---------------- ABA 2: NOVO LANÇAMENTO ----------------
    with aba_novo:
        st.subheader("➕ Registrar Movimentação")

        movimento = st.radio("Tipo de movimento", ["Saída", "Entrada"], horizontal=True)

        tipo_gasto = None
        periodicidade = None

        if movimento == "Saída":
            tipo_gasto = st.selectbox(
                "Classificação do gasto",
                ["Essencial", "Fixo", "Supérfluo", "Emergencial"],
            )
            if tipo_gasto == "Fixo":
                periodicidade = st.selectbox(
                    "Periodicidade",
                    ["Mensal", "Semanal", "Diário", "Anual"],
                )

        with st.form("form_lancamento", clear_on_submit=True):
            data_lanc = st.date_input("Data", value=date.today(), format="DD/MM/YYYY")
            descricao = st.text_input("Descrição", placeholder="Ex: Mercado, Aluguel, Salário...")
            valor = st.number_input("Valor (R$)", min_value=0.01, step=1.0, format="%.2f")
            salvar = st.form_submit_button("Salvar Lançamento", type="primary", use_container_width=True)

            if salvar:
                try:
                    cat = tipo_gasto if movimento == "Saída" else "Receita"
                    salvar_gasto(
                        uid=uid,
                        movimento=movimento,
                        categoria=cat,
                        descricao=descricao,
                        valor=valor,
                        tipo_gasto=tipo_gasto,
                        periodicidade=periodicidade,
                        data_lancamento=data_lanc,
                    )
                    limpar_cache_usuario()
                    st.success("Lançamento salvo com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    # ---------------- ABA 3: RELATÓRIOS ----------------
    with aba_rel:
        st.subheader("📄 Exportar Relatórios Mensais")
        meses = carregar_meses(uid)

        if not meses:
            st.info("Você ainda não possui lançamentos para exportar.")
        else:
            opcoes = {label: (y, m) for label, y, m in meses}
            escolha = st.selectbox("Selecione o mês", list(opcoes.keys()))
            year, month = opcoes[escolha]
            tag = f"{year:04d}-{month:02d}"

            col_xl, col_pdf = st.columns(2)
            with col_xl:
                if st.button("Preparar Excel (.xlsx)", use_container_width=True):
                    st.session_state["excel_pronto"] = (tag, exportar_excel_mes(uid, year, month))
                if "excel_pronto" in st.session_state and st.session_state["excel_pronto"][0] == tag:
                    st.download_button(
                        label="⬇️ Baixar Excel (.xlsx)",
                        data=st.session_state["excel_pronto"][1],
                        file_name=f"relatorio_{tag}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        type="primary",
                    )

            with col_pdf:
                if st.button("Preparar PDF (.pdf)", use_container_width=True):
                    st.session_state["pdf_pronto"] = (tag, gerar_pdf_mes(uid, year, month))
                if "pdf_pronto" in st.session_state and st.session_state["pdf_pronto"][0] == tag:
                    st.download_button(
                        label="⬇️ Baixar PDF (.pdf)",
                        data=st.session_state["pdf_pronto"][1],
                        file_name=f"relatorio_{tag}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary",
                    )


if st.session_state["usuario_id"] is None:
    tela_autenticacao()
else:
    tela_principal()