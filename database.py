import os
import mysql.connector
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def _get_credencial(chave: str, padrao: str | None = None):
    valor = os.getenv(chave)
    if valor:
        return valor
    try:
        if chave in st.secrets:
            return str(st.secrets[chave])
    except Exception:
        pass
    return padrao


@st.cache_resource
def _conexao_persistente():
    return mysql.connector.connect(
        host=_get_credencial("DB_HOST"),
        port=int(_get_credencial("DB_PORT", "4000")),
        user=_get_credencial("DB_USER"),
        password=_get_credencial("DB_PASSWORD"),
        database=_get_credencial("DB_NAME"),
        ssl_verify_cert=True,
        autocommit=True,
    )


def conectar():
    con = _conexao_persistente()
    try:
        con.ping(reconnect=True, attempts=3, delay=1)
    except Exception:
        st.cache_resource.clear()
        con = _conexao_persistente()
    return con