from fastapi import APIRouter, Request, Response, HTTPException, Depends, Body
from fastapi.responses import JSONResponse
from schemas import LoginForm, TokenForm, User
from utils import create_jwt, decode_jwt, COOKIE_NAME, verify_password
import os
from database import get_connection
import cx_Oracle
router = APIRouter(prefix="/auth", tags=["auth"])

# Simular base de datos
FAKE_DB = {
    "name": "11787",
    "email": "diana.calderon@est.umet.edu.ec",
    "password": "1234"  # Debes usar hash real
}

def get_user_from_token(request: Request) -> User | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    data = decode_jwt(token)
    if not data:
        return None
    return User(name=data["cllc_cdg"], email=data["email"])

@router.post("/login")
async def login(response: Response, form: LoginForm = Body(...), conn: cx_Oracle.Connection = Depends(get_connection)):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, password, username, email, cllc_nmb, cllc_ruc
            FROM appalumno.auth_user au
            JOIN sigac.cliente_local cl ON TO_CHAR(cl.cllc_cdg) = au.username
            JOIN sna.sna_matricula_postgrado pos on pos.cllc_cdg = cl.cllc_cdg
            where
                au.email = :email
                AND pos.map_pagado = 'S'
                AND pos.map_anulado = 'N'
                AND pos.map_eliminado = 'N'
            order by pos.pel_codigo DESC""", {"email": form.email}
        )
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # Desempaquetar los datos
        user_id, hashed_password, username, email, cllc_nmb, cllc_ruc = user
        if not verify_password(form.password, hashed_password) and False:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        token = create_jwt({"email": email, "cllc_cdg": username})
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            httponly=True,
            secure=os.getenv("SECURE_COOKIE", "false").lower() == "true",  # Requiere HTTPS (Cloudflare ✅) en desarrollo se debe usar False
            samesite="Lax",
            path="/"
        )
        return {"user": {"email": email, "name": username}}
    
    except cx_Oracle.DatabaseError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
    

@router.post("/set-token")
async def login_with_token(data: TokenForm, response: Response):
    payload = decode_jwt(data.token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    response.set_cookie(
        key=COOKIE_NAME,
        value=data.token,
        httponly=True,
        secure=True,
        samesite="Lax",
        path="/"
    )
    return {"message": "Token establecido"}

@router.get("/me")
async def me(request: Request):
    user = get_user_from_token(request)
    if not user:
        raise HTTPException(status_code=401, detail="No autenticado")
    return {"user": user}

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"message": "Sesión cerrada"}
