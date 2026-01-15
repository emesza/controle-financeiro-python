from tkinter import messagebox
from database import conectar

usuario_atual = None

def usuario_logado():
    return usuario_atual

def login(apelido, senha):
    global usuario_atual

    apelido = (apelido or "").strip()
    senha = (senha or "").strip()

    if not apelido or not senha:
        messagebox.showerror("Erro", "Preencha usuário e senha.")
        return False

    con = None
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute(
            "SELECT id FROM usuarios WHERE apelido=%s AND senha=%s",
            (apelido, senha),
        )
        r = cur.fetchone()
        if r:
            usuario_atual = int(r[0])
            return True
        messagebox.showerror("Erro", "Usuário ou senha inválidos.")
        return False
    except Exception as e:
        messagebox.showerror("Erro", f"Falha no login: {e}")
        return False
    finally:
        if con:
            con.close()

def criar_conta(apelido, senha):
    apelido = (apelido or "").strip()
    senha = (senha or "").strip()

    if not apelido or not senha:
        messagebox.showerror("Erro", "Preencha apelido e senha.")
        return

    con = None
    try:
        con = conectar()
        cur = con.cursor()
        cur.execute(
            "INSERT INTO usuarios (apelido, senha) VALUES (%s,%s)",
            (apelido, senha),
        )
        con.commit()
        messagebox.showinfo("OK", "Conta criada! Agora faça login.")
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível criar conta: {e}")
    finally:
        if con:
            con.close()

def logout():
    global usuario_atual
    usuario_atual = None
