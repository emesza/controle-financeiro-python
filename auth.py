import bcrypt
from database import conectar


def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))


def login(apelido: str, senha: str) -> tuple[bool, int | str]:
    apelido = (apelido or "").strip()
    senha = (senha or "").strip()

    if not apelido or not senha:
        return False, "Preencha usuário e senha."

    try:
        con = conectar()
        cur = con.cursor()
        cur.execute(
            "SELECT id, senha FROM usuarios WHERE apelido=%s",
            (apelido,),
        )
        r = cur.fetchone()
        cur.close()
        if r and verificar_senha(senha, r[1]):
            return True, int(r[0])
        return False, "Usuário ou senha inválidos."
    except Exception as e:
        return False, f"Falha no login: {e}"


def criar_conta(apelido: str, senha: str) -> tuple[bool, str]:
    apelido = (apelido or "").strip()
    senha = (senha or "").strip()

    if not apelido or not senha:
        return False, "Preencha apelido e senha."

    try:
        con = conectar()
        cur = con.cursor()
        senha_hash = gerar_hash_senha(senha)
        cur.execute(
            "INSERT INTO usuarios (apelido, senha) VALUES (%s, %s)",
            (apelido, senha_hash),
        )
        cur.close()
        return True, "Conta criada com sucesso! Agora faça login."
    except Exception as e:
        if "Duplicate entry" in str(e):
            return False, "Este apelido já está em uso."
        return False, f"Não foi possível criar conta: {e}"