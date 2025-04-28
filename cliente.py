from fastapi import APIRouter, Request, Response, HTTPException, Depends, Body
from schemas import Cliente
import os
from database import get_connection
import cx_Oracle
from auth import get_user_from_token
from schemas import User

router = APIRouter(prefix="/cliente", tags=["cliente"])

@router.get("/me")
async def cliente_obtener(
    conn: cx_Oracle.Connection = Depends(get_connection),
    user: User = Depends(get_user_from_token)
):
    try:
        cursor = conn.cursor()
        sql = """
        select cllc_cdg, cllc_ruc, cllc_nmb, cllc_email, cllc_celular
        from sigac.cliente_local
        where cllc_cdg = :cllc_cdg
        """
        cursor.execute(sql, {"cllc_cdg": user.username})
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
    