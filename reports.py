import io
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from database import conectar


def _buscar_lancamentos_mes(uid: int, year: int, month: int):
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
        (int(uid), int(year), int(month)),
    )
    rows = cur.fetchall()
    cur.close()
    return rows


def exportar_excel_mes(uid: int, year: int, month: int) -> bytes:
    lanc = _buscar_lancamentos_mes(uid, year, month)
    tag = f"{int(year):04d}-{int(month):02d}"

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

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def gerar_pdf_mes(uid: int, year: int, month: int) -> bytes:
    lanc = _buscar_lancamentos_mes(uid, year, month)
    tag = f"{int(year):04d}-{int(month):02d}"

    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    total_entradas = 0.0
    total_saidas = 0.0

    flow = []
    flow.append(Paragraph(f"<b>Relatório Financeiro - {tag}</b>", styles["Title"]))
    flow.append(Spacer(1, 12))

    if not lanc:
        flow.append(Paragraph("Nenhum lançamento neste mês.", styles["BodyText"]))
        doc.build(flow)
        buffer.seek(0)
        return buffer.getvalue()

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
    buffer.seek(0)
    return buffer.getvalue()


def listar_meses_com_movimento(uid: int):
    nomes = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]

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
        (int(uid),),
    )
    rows = cur.fetchall()
    cur.close()

    out = []
    for y, m in rows:
        out.append((f"{int(y):04d}-{int(m):02d} ({nomes[int(m)-1]})", int(y), int(m)))
    return out