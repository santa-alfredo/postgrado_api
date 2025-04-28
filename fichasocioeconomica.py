from fastapi import APIRouter, Request, Response, HTTPException, Depends, Body
from fastapi.responses import StreamingResponse
from schemas import FichaSocioeconomicaSchema
import os, io
from database import get_connection
import cx_Oracle
from datetime import datetime
from auth import get_user_from_token
from schemas import User
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
import tempfile
from dotenv import load_dotenv
load_dotenv()

router = APIRouter(prefix="/ficha", tags=["ficha"])


BASE_URL = os.getenv("BASE_URL")

@router.post("/ficha-socioeconomica")
async def crear_ficha_socioeconomica(
    response: Response, 
    data: FichaSocioeconomicaSchema = Body(...),
    conn: cx_Oracle.Connection = Depends(get_connection),
    user: User = Depends(get_user_from_token)
):
    try:
        #! Periodo actual quemado
        periodo = 65
        
        # Mapeo como diccionario
        mapa_campos = {
            "fechaNacimiento": "fis_fecha_nac",
            "estadoCivil": "fis_estado_civil",
            "telefono": "fis_telefono",
            "promedio": "fis_calif_grado",
            "semestre": "fis_semestre_matricula",
            "situacionLaboral": "fis_situacion_lab",
            "relacionCompa": "fis_relac_companeros",
            "relacionDocente": "fis_relac_docentes",
            "relacionPadres": "fis_relac_padres",
            "estadoFamiliar": "fis_estado_civil_padres",
            "tieneDiscapacidad": "fis_discapacidad",
            "cambioResidencia": "fis_tuvo_camb_resi",
            "direccion": "fis_direccion",
            "provinciaId": "fis_provincia",
            "ciudadId": "fis_ciudad",
            "parroquiaId": "fis_parroquia",
            "discapacidad.tipo": "fis_tip_disc",
            "discapacidad.porcentaje": "fis_porc_disc",
        }
        
        cursor = conn.cursor()

        # Verifica existencia
        cursor.execute("""
            SELECT 1 FROM sna.sna_ficha_socioeconomica WHERE cllc_cdg = :cllc_cdg
        """, {"cllc_cdg": user.username})
        exists = cursor.fetchone() is not None

        if not exists:
            # Armar INSERT
            campos = ["cllc_cdg"]
            valores = [":cllc_cdg"]
            params = {"cllc_cdg": user.username, "fis_pel_codigo": periodo}

            # Usa el mismo mapa que para UPDATE, o haz uno para INSERT si prefieres
            for frontend_key, db_field in mapa_campos.items():
                if "." in frontend_key:
                    main_key, sub_key = frontend_key.split(".")
                    nested = getattr(data, main_key, None)
                    if nested and getattr(nested, sub_key, None) is not None:
                        campos.append(db_field)
                        valores.append(f":{db_field}")
                        params[db_field] = getattr(nested, sub_key)
                else:
                    value = getattr(data, frontend_key, None)
                    if value is not None:
                        campos.append(db_field)
                        valores.append(f":{db_field}")
                        params[db_field] = value

            insert_sql = f"""
                INSERT INTO sna.sna_ficha_socioeconomica ({", ".join(campos)})
                VALUES ({", ".join(valores)})
            """
            cursor.execute(insert_sql, params)
            conn.commit()

            return {"message": "Ficha socioeconómica insertada correctamente"}

        # Preparar valores para SQL UPDATE
        campos_sql = []
        campos_sql.append("fis_pel_codigo = :fis_pel_codigo")
        valores_sql = {"cllc_cdg": user.username, "fis_pel_codigo": periodo}

        for frontend_key, db_field in mapa_campos.items():
            if "." in frontend_key:
                main_key, sub_key = frontend_key.split(".")
                nested_obj = getattr(data, main_key, None)
                if nested_obj and getattr(nested_obj, sub_key, None) is not None:
                    campos_sql.append(f"{db_field} = :{db_field}")
                    valores_sql[db_field] = getattr(nested_obj, sub_key)
            else:
                valor = getattr(data, frontend_key, None)
                if valor is not None:
                    campos_sql.append(f"{db_field} = :{db_field}")
                    valores_sql[db_field] = valor
        if campos_sql:
            update_sql = f"""
                UPDATE sna.sna_ficha_socioeconomica
                SET {", ".join(campos_sql)}
                WHERE cllc_cdg = :cllc_cdg
            """
            cursor.execute(update_sql, valores_sql)
            conn.commit()

        return {
            "message": "Ficha socioeconómica actualizada correctamente",
            "ficha": {"id": user.username}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@router.get("/me")
async def get_ficha_socioeconomica(
    user: User = Depends(get_user_from_token),
    conn: cx_Oracle.Connection = Depends(get_connection)    
):
    try:
        #! Periodo actual quemado
        periodo = 65

        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM sna.sna_ficha_socioeconomica 
            WHERE cllc_cdg = :cllc_cdg
            order by fis_pel_codigo DESC
        """, {"cllc_cdg": user.username})
        row = cursor.fetchone()
        if row is None:
            return {
                "message": "No se encontró la ficha socioeconómica",
                "ficha": None,
                "periodo": False
            }
        ficha = dict(zip([col[0].lower() for col in cursor.description], row))
        return {
            "message": "Ficha socioeconómica encontrada",
            "ficha": {"id": user.username},
            "periodo": periodo == int(ficha["fis_pel_codigo"] or 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()


@router.get("/{cllc_cdg}/pdf")
async def get_ficha_socioeconomica_pdf(
    cllc_cdg: int,
    conn: cx_Oracle.Connection = Depends(get_connection)
):
    try:
        # Datos de ejemplo para la ficha socioeconómica
        estudiante = {
            "nombre": "Juan Pérez Gómez",
            "cedula": "1234567890",
            "edad": 20,
            "direccion": "Av. Principal 123, Quito",
            "telefono": "0991234567",
            "correo": "juan.perez@ejemplo.com",
            "nivel_academico": "Tercer año de Ingeniería",
            "institucion": "Universidad Central",
            "discapacidad": "Ninguna",
            "enfermedad_cronica": "Asma",
            "trabaja": True,
            "empresa": "Tech Solutions",
            "cargo": "Asistente de Desarrollo",
            "sueldo_estudiante": 500,
            "negocio_propio": False
        }

        miembros_hogar = [
            {"nombre": "María Gómez", "parentesco": "Madre", "edad": 45, "instruccion": "Bachiller", "ocupacion": "Secretaria", "sueldo": 600},
            {"nombre": "Pedro Pérez", "parentesco": "Padre", "edad": 50, "instruccion": "Universitaria", "ocupacion": "Contador", "sueldo": 1200},
            {"nombre": "Ana Pérez", "parentesco": "Hermana", "edad": 15, "instruccion": "Secundaria", "ocupacion": "Estudiante", "sueldo": 0}
        ]

        gastos_basicos = {
            "salud": 100,
            "vestimenta": 50,
            "transporte": 80,
            "energia": 60,
            "agua": 30,
            "internet": 40
        }

        # Calcular ingresos totales
        ingresos_totales = sum(miembro["sueldo"] for miembro in miembros_hogar)
        if estudiante["trabaja"]:
            ingresos_totales += estudiante["sueldo_estudiante"]

        # Calcular gastos totales
        gastos_totales = sum(gastos_basicos.values())

        # Calcular balance
        balance = ingresos_totales - gastos_totales
        #! Periodo actual quemado
        periodo = 65

        # cursor = conn.cursor()
        # cursor.execute("""
        #     SELECT * FROM sna.sna_ficha_socioeconomica 
        #     WHERE cllc_cdg = :cllc_cdg AND fis_pel_codigo = :fis_pel_codigo
        # """, {"cllc_cdg": cllc_cdg, "fis_pel_codigo": periodo})
        # row = cursor.fetchone()
        # if row is None:
        #     raise HTTPException(status_code=404, detail="Ficha socioeconómica no encontrada")
        
        # # Convertir la fila a diccionario
        # ficha = dict(zip([col[0].lower() for col in cursor.description], row))
        
        # Configurar el entorno de Jinja2
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('ficha_socioeconomica.html')
        
        # Renderizar la plantilla con los datos
        html_content = template.render({"estudiante": estudiante, "miembros_hogar": miembros_hogar, "gastos_basicos": gastos_basicos, "ingresos_totales": ingresos_totales, "gastos_totales": gastos_totales, "balance": balance, "logo_url": f"{BASE_URL}/static/logo/logo_umet.png", "foto_url": f"{BASE_URL}/static/logo/avatar.png"})
        
         # Crear el PDF en memoria
        pdf_stream = io.BytesIO()
        HTML(string=html_content).write_pdf(pdf_stream)
        
        # Volver al principio del flujo de datos (importante para que StreamingResponse funcione correctamente)
        pdf_stream.seek(0)
        
        # Devolver el archivo PDF como flujo de datos
        return StreamingResponse(
            pdf_stream,
            media_type="application/pdf",
            headers={"Content-Disposition": "inline; filename=ficha_socioeconomica.pdf"}
        )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando el PDF: {str(e)}")
    finally:
        print("finally")
        # cursor.close()