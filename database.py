import mysql.connector

DB_HOST = "localhost"
DB_NAME = "controle_financeiro"

# RECOMENDADO: use o usuário do app
DB_USER = "financeiro"
DB_PASSWORD = "financeiro123"

def conectar():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        auth_plugin="mysql_native_password",
    )
