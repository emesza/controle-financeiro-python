import os
from datetime import datetime

import matplotlib.pyplot as plt
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from database import conectar
import auth


def _dados_dir():
    base = os.getcwd()
    data_dir = os.path.join(base, "dados")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def _buscar_lancamentos_mes(year: int, month: int):
    """
    Retorna lançamentos do mês/ano do usuário logado:
    (data, tipo, descricao, valor, tipo_gasto, periodicidade)
    """
    uid = auth.usuario_logado()
    if not uid:
        raise RuntimeError("Usuário não está logado.")

    con = None
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute(
            """
            SELECT data, tipo, descricao, valor, tipo_gasto, periodicidade
            FROM gastos
            WHERE usuario_id=%s
              AND YEAR(data)=%s
              AND MONTH(data)=%s
            ORDER BY data ASC, id ASC
            """,
            (uid, int(year), int(month)),
        )
        return cur.fetchall()
    finally:
        if con:
            con.close()


def _resumo_pizza_saidas(lancamentos):
    """Só SAÍDAS por tipo_gasto, para pizza."""
    resumo = {"Essencial": 0.0, "Fixo": 0.0, "Supérfluo": 0.0, "Emergencial": 0.0}
    for data, mov, desc, valor, tipo_gasto, periodicidade in lancamentos:
        if mov != "Saída":
            continue
        tg = (tipo_gasto or "").strip()
        if tg in resumo:
            resumo[tg] += float(valor or 0)
    return resumo


def gerar_pizza_mes(year: int, month: int):
    lanc = _buscar_lancamentos_mes(year, month)
    resumo = _resumo_pizza_saidas(lanc)

    labels, values = [], []
    for k, v in resumo.items():
        if v > 0:
            labels.append(k)
            values.append(v)

    if not values:
        raise RuntimeError("Sem gastos (Saídas) nesse mês para gerar o gráfico.")

    tag = f"{int(year):04d}-{int(month):02d}"
    out = os.path.join(_dados_dir(), f"pizza_gastos_{tag}.png")

    plt.figure()
    plt.pie(values, labels=labels, autopct="%1.1f%%")
    plt.title(f"Gastos por tipo - {tag}")
    plt.savefig(out, dpi=200, bbox_inches="tight")
    plt.close()

    return out


def exportar_excel_mes(year: int, month: int):
    lanc = _buscar_lancamentos_mes(year, month)

    tag = f"{int(year):04d}-{int(month):02d}"
    out = os.path.join(_dados_dir(), f"relatorio_{tag}.xlsx")

    wb = Workbook()
    ws = wb.active
    ws.title = "Lançamentos"

    ws.append(["Data", "Movimento", "Descrição", "Valor", "Tipo de gasto", "Periodicidade"])

    total_entradas = 0.0
    total_saidas = 0.0

    for data, mov, desc, valor, tipo_gasto, periodicidade in lanc:
        data_str = data.strftime("%d/%m/%Y") if hasattr(data, "strftime") else str(data)
        v = float(valor or 0)

        if mov == "Entrada":
            total_entradas += v
        elif mov == "Saída":
            total_saidas += v

        ws.append([data_str, mov, desc, v, tipo_gasto or "", periodicidade or ""])

    ws2 = wb.create_sheet("Resumo")
    ws2.append(["Mês", tag])
    ws2.append(["Total Entradas", total_entradas])
    ws2.append(["Total Saídas", total_saidas])
    ws2.append(["Saldo", total_entradas - total_saidas])

    wb.save(out)
    return out


def gerar_pdf_mes(year: int, month: int):
    lanc = _buscar_lancamentos_mes(year, month)

    tag = f"{int(year):04d}-{int(month):02d}"
    out = os.path.join(_dados_dir(), f"relatorio_{tag}.pdf")

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(out, pagesize=A4)

    total_entradas = 0.0
    total_saidas = 0.0

    flow = []
    flow.append(Paragraph(f"<b>Relatório Financeiro - {tag}</b>", styles["Title"]))
    flow.append(Spacer(1, 12))

    if not lanc:
        flow.append(Paragraph("Nenhum lançamento neste mês.", styles["BodyText"]))
        doc.build(flow)
        return out

    for data, mov, desc, valor, tipo_gasto, periodicidade in lanc:
        data_str = data.strftime("%d/%m/%Y") if hasattr(data, "strftime") else str(data)
        v = float(valor or 0)

        if mov == "Entrada":
            total_entradas += v
        elif mov == "Saída":
            total_saidas += v

        extra = ""
        if tipo_gasto:
            extra = f" • {tipo_gasto}"
            if tipo_gasto == "Fixo" and periodicidade:
                extra += f" ({periodicidade})"

        flow.append(
            Paragraph(
                f"{data_str} • {mov}{extra} • {desc} — <b>R$ {v:.2f}</b>",
                styles["BodyText"],
            )
        )

    flow.append(Spacer(1, 12))
    flow.append(Paragraph(f"<b>Total Entradas:</b> R$ {total_entradas:.2f}", styles["BodyText"]))
    flow.append(Paragraph(f"<b>Total Saídas:</b> R$ {total_saidas:.2f}", styles["BodyText"]))
    flow.append(Paragraph(f"<b>Saldo:</b> R$ {total_entradas - total_saidas:.2f}", styles["BodyText"]))

    doc.build(flow)
    return out


def listar_meses_disponiveis(qtd=12):
    """
    Retorna lista de tuplas (label, year, month) dos últimos 'qtd' meses incluindo o atual.
    Ex: [("2026-01 (Jan)", 2026, 1), ("2025-12 (Dez)", 2025, 12), ...]
    """
    nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    now = datetime.now()
    y, m = now.year, now.month

    out = []
    for _ in range(int(qtd)):
        out.append((f"{y:04d}-{m:02d} ({nomes[m-1]})", y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return out

def listar_meses_com_movimento():
    """
    Retorna lista de tuplas (label, year, month) APENAS dos meses que possuem lançamentos
    para o usuário logado, em ordem do mais recente pro mais antigo.

    label exemplo: "2026-01 (JAN)"
    """
    uid = auth.usuario_logado()
    if not uid:
        raise RuntimeError("Usuário não está logado.")

    nomes = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

    con = None
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute(
            """
            SELECT YEAR(data) AS y, MONTH(data) AS m
            FROM gastos
            WHERE usuario_id=%s
            GROUP BY YEAR(data), MONTH(data)
            ORDER BY y DESC, m DESC
            """,
            (uid,),
        )
        rows = cur.fetchall()

        out = []
        for y, m in rows:
            out.append((f"{int(y):04d}-{int(m):02d} ({nomes[int(m)-1]})", int(y), int(m)))
        return out
    finally:
        if con:
            con.close()

