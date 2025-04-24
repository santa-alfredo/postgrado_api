from fastapi import APIRouter, Request, Response, HTTPException, Depends, Body
from schemas import Cliente
import os
from database import get_connection
import cx_Oracle
router = APIRouter(prefix="/cliente", tags=["cliente"])

@router.get("/{cllc_cdg}")
async def cliente_obtener(
    cllc_cdg: int,
    conn: cx_Oracle.Connection = Depends(get_connection)
):
    try:
        cursor = conn.cursor()
        sql = """
        select cllc_cdg, cllc_ruc, cllc_nmb, cllc_email, cllc_celular
        from sigac.cliente_local
        where cllc_cdg = :cllc_cdg
        """
        cursor.execute(sql, {"cllc_cdg": cllc_cdg})
        row = cursor.fetchone()
        if row is None:
            return {
                "message": "Cliente no encontrado",
                "data": None
            }
        data = dict(zip([col[0].lower() for col in cursor.description], row))
        return {
            "message": "Cliente encontrado",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
    