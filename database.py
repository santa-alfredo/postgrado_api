import cx_Oracle
import os

# Crear el pool globalmente (idealmente al iniciar la app)
pool = cx_Oracle.SessionPool(
    user=os.getenv("ORACLE_USER", "usuario"),
    password=os.getenv("ORACLE_PASSWORD", "clave"),
    dsn=cx_Oracle.makedsn(
        host=os.getenv("ORACLE_HOST", "localhost"),
        port=os.getenv("ORACLE_PORT", "1521"),
        sid=os.getenv("ORACLE_SID", "XE")  # o service_name="orcl"
    ),
    min=2,        # Conexiones mínimas abiertas
    max=10,       # Conexiones máximas
    increment=1,  # Cuántas conexiones nuevas abrir si se necesita
    encoding="UTF-8",
    threaded=True,  # Si usas threads (FastAPI lo hace internamente)
    getmode=cx_Oracle.SPOOL_ATTRVAL_WAIT
)

def get_connection():
    conn = pool.acquire()
    try:
        yield conn
    finally:
        conn.close()  # Regresa la conexión al pool
