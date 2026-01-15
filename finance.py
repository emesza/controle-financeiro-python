from database import conectar
import auth

def _require_login():
    uid = auth.usuario_logado()
    if not uid:
        raise RuntimeError("Usuário não está logado.")
    return uid

def _garantir_colunas_gastos():
    con = None
    try:
        con = conectar()
        cur = con.cursor()
        try:
            cur.execute("ALTER TABLE gastos ADD COLUMN tipo_gasto VARCHAR(20) NULL")
        except Exception:
            pass
        try:
            cur.execute("ALTER TABLE gastos ADD COLUMN periodicidade VARCHAR(10) NULL")
        except Exception:
            pass
        con.commit()
    finally:
        if con:
            con.close()

# ================== METAS ==================

def _criar_tabela_metas_se_precisar():
    con = None
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS metas (
                usuario_id INT PRIMARY KEY,
                valor DECIMAL(10,2) NOT NULL
            )
            """
        )
        con.commit()
    finally:
        if con:
            con.close()

def definir_meta(valor: float):
    uid = _require_login()
    _criar_tabela_metas_se_precisar()

    con = None
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO metas (usuario_id, valor)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE valor = VALUES(valor)
            """,
            (uid, float(valor)),
        )
        con.commit()
    finally:
        if con:
            con.close()

def obter_meta():
    uid = _require_login()
    _criar_tabela_metas_se_precisar()

    con = None
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute("SELECT valor FROM metas WHERE usuario_id=%s", (uid,))
        r = cur.fetchone()
        return float(r[0]) if r else None
    finally:
        if con:
            con.close()

# ================== FINANÇAS ==================

def total_mes():
    uid = _require_login()

    con = None
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute(
            """
            SELECT
              COALESCE(SUM(CASE WHEN tipo='Entrada' THEN valor ELSE 0 END), 0) AS entradas,
              COALESCE(SUM(CASE WHEN tipo='Saída' THEN valor ELSE 0 END), 0) AS saidas
            FROM gastos
            WHERE usuario_id=%s
              AND MONTH(data)=MONTH(CURDATE())
              AND YEAR(data)=YEAR(CURDATE())
            """,
            (uid,),
        )
        e, s = cur.fetchone()
        return float(e or 0), float(s or 0)
    finally:
        if con:
            con.close()

def resumo_tipos_mes():
    """
    Retorna um dict com os totais de SAÍDA do mês por tipo_gasto:
    { "Essencial": 123.45, "Fixo": 0.0, "Supérfluo": 10.0, "Emergencial": 0.0 }
    """
    uid = _require_login()
    _garantir_colunas_gastos()

    base = {
        "Essencial": 0.0,
        "Fixo": 0.0,
        "Supérfluo": 0.0,
        "Emergencial": 0.0,
    }

    con = None
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute(
            """
            SELECT COALESCE(tipo_gasto, ''), COALESCE(SUM(valor), 0)
            FROM gastos
            WHERE usuario_id=%s
              AND tipo='Saída'
              AND MONTH(data)=MONTH(CURDATE())
              AND YEAR(data)=YEAR(CURDATE())
            GROUP BY tipo_gasto
            """,
            (uid,),
        )
        for tg, total in cur.fetchall():
            tg = (tg or "").strip()
            if tg in base:
                base[tg] = float(total or 0)
        return base
    finally:
        if con:
            con.close()

def listar_gastos(limite=10):
    uid = _require_login()
    _garantir_colunas_gastos()

    con = None
    try:
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
            (uid, int(limite)),
        )
        return cur.fetchall()
    finally:
        if con:
            con.close()

def salvar_gasto(movimento, categoria, descricao, valor, tipo_gasto=None, periodicidade=None):
    uid = _require_login()
    _garantir_colunas_gastos()

    movimento = (movimento or "").strip()
    categoria = (categoria or "").strip() or "Outros"
    descricao = (descricao or "").strip() or "Sem descrição"
    tipo_gasto = (tipo_gasto or "").strip() or None
    periodicidade = (periodicidade or "").strip() or None

    if movimento not in ("Entrada", "Saída"):
        raise ValueError("Movimento inválido (use Entrada ou Saída).")

    if tipo_gasto != "Fixo":
        periodicidade = None

    con = None
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute(
            """
            INSERT INTO gastos (usuario_id, data, tipo, categoria, descricao, valor, tipo_gasto, periodicidade)
            VALUES (%s, CURDATE(), %s, %s, %s, %s, %s, %s)
            """,
            (uid, movimento, categoria, descricao, float(valor), tipo_gasto, periodicidade),
        )
        con.commit()
    finally:
        if con:
            con.close()

def excluir_gasto(gasto_id: int):
    uid = _require_login()

    con = None
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute(
            "DELETE FROM gastos WHERE id=%s AND usuario_id=%s",
            (int(gasto_id), uid),
        )
        con.commit()
    finally:
        if con:
            con.close()
