from datetime import date
from database import conectar


# ================== METAS ==================

def definir_meta(uid: int, valor: float):
    con = conectar()
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO metas (usuario_id, valor)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE valor = VALUES(valor)
        """,
        (int(uid), float(valor)),
    )
    cur.close()


def obter_meta(uid: int):
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT valor FROM metas WHERE usuario_id=%s", (int(uid),))
    r = cur.fetchone()
    cur.close()
    return float(r[0]) if r else None


# ================== FINANÇAS ==================

def total_mes(uid: int, year: int | None = None, month: int | None = None):
    hoje = date.today()
    y = year or hoje.year
    m = month or hoje.month

    con = conectar()
    cur = con.cursor()
    cur.execute(
        """
        SELECT
          COALESCE(SUM(CASE WHEN tipo='Entrada' THEN valor ELSE 0 END), 0) AS entradas,
          COALESCE(SUM(CASE WHEN tipo='Saída' THEN valor ELSE 0 END), 0) AS saidas
        FROM gastos
        WHERE usuario_id=%s
          AND MONTH(data)=%s
          AND YEAR(data)=%s
        """,
        (int(uid), int(m), int(y)),
    )
    e, s = cur.fetchone()
    cur.close()
    return float(e or 0), float(s or 0)


def resumo_tipos_mes(uid: int, year: int | None = None, month: int | None = None):
    hoje = date.today()
    y = year or hoje.year
    m = month or hoje.month

    base = {
        "Essencial": 0.0,
        "Fixo": 0.0,
        "Supérfluo": 0.0,
        "Emergencial": 0.0,
    }

    con = conectar()
    cur = con.cursor()
    cur.execute(
        """
        SELECT COALESCE(tipo_gasto, ''), COALESCE(SUM(valor), 0)
        FROM gastos
        WHERE usuario_id=%s
          AND tipo='Saída'
          AND MONTH(data)=%s
          AND YEAR(data)=%s
        GROUP BY tipo_gasto
        """,
        (int(uid), int(m), int(y)),
    )
    for tg, total in cur.fetchall():
        tg = (tg or "").strip()
        if tg in base:
            base[tg] = float(total or 0)
    cur.close()
    return base


def listar_gastos(uid: int, limite: int = 50):
    con = conectar()
    cur = con.cursor()
    cur.execute(
        """
        SELECT id, data, tipo, categoria, descricao, valor, tipo_gasto, periodicidade
        FROM gastos
        WHERE usuario_id=%s
        ORDER BY data DESC, id DESC
        LIMIT %s
        """,
        (int(uid), int(limite)),
    )
    rows = cur.fetchall()
    cur.close()
    return rows


def salvar_gasto(
    uid: int,
    movimento: str,
    categoria: str,
    descricao: str,
    valor: float,
    tipo_gasto: str | None = None,
    periodicidade: str | None = None,
    data_lancamento: date | None = None,
):
    movimento = (movimento or "").strip()
    categoria = (categoria or "").strip() or "Outros"
    descricao = (descricao or "").strip() or "Sem descrição"
    tipo_gasto = (tipo_gasto or "").strip() or None
    periodicidade = (periodicidade or "").strip() or None
    dt = data_lancamento or date.today()

    if movimento not in ("Entrada", "Saída"):
        raise ValueError("Movimento inválido (use Entrada ou Saída).")

    if movimento == "Entrada":
        tipo_gasto = None
        periodicidade = None
    elif tipo_gasto != "Fixo":
        periodicidade = None

    con = conectar()
    cur = con.cursor()
    cur.execute(
        """
        INSERT INTO gastos (usuario_id, data, tipo, categoria, descricao, valor, tipo_gasto, periodicidade)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (int(uid), dt, movimento, categoria, descricao, float(valor), tipo_gasto, periodicidade),
    )
    cur.close()


def excluir_gasto(uid: int, gasto_id: int):
    con = conectar()
    cur = con.cursor()
    cur.execute(
        "DELETE FROM gastos WHERE id=%s AND usuario_id=%s",
        (int(gasto_id), int(uid)),
    )
    cur.close()