from fastapi import APIRouter, Request, Response, HTTPException, Depends, Body
from schemas import FichaSocioeconomicaSchema
import os
from database import get_connection
import cx_Oracle
from datetime import datetime
router = APIRouter(prefix="/ficha", tags=["ficha"])

@router.post("/ficha-socioeconomica")
async def crear_ficha_socioeconomica(
    response: Response, 
    data: FichaSocioeconomicaSchema = Body(...),
    conn: cx_Oracle.Connection = Depends(get_connection)
):
    try:
        cursor = conn.cursor()

        # Verifica existencia
        cursor.execute("""
            SELECT 1 FROM sna.sna_ficha_socioeconomica WHERE cllc_cdg = :cllc_cdg
        """, {"cllc_cdg": data['cllc_cdg']})
        exists = cursor.fetchone() is not None

        if not exists:
            raise HTTPException(status_code=404, detail="Ficha no existe. Agrega lógica de inserción si es necesario.")

        # Mapeo como diccionario
        mapa_campos = {
            "fechaNacimiento": ("fis_fecha_nac", "date"),
            "estadoCivil": ("fis_estado_civil", "str"),
            "telefono": ("fis_telefono", "str"),
            "promedio": ("fis_calif_grado", "float"),
            "semestre": ("fis_semestre_matricula", "int"),
            "situacionLaboral": ("fis_situacion_lab", "str"),
            "relacionCompa": ("fis_relac_companeros", "str"),
            "relacionDocente": ("fis_relac_docentes", "str"),
            "relacionPadres": ("fis_relac_padres", "str"),
            "estadoFamiliar": ("fis_estado_civil_padres", "str"),
            "tieneDiscapacidad": ("fis_discapacidad", "str"),
            "cambioResidencia": ("fis_tuvo_camb_resi", "bool"),
            "direccion": ("fis_direccion", "str"),
            "provinciaId": ("fis_provincia", "str"),
            "ciudadId": ("fis_ciudad", "str"),
            "parroquiaId": ("fis_parroquia", "str"),
            "discapacidad.tipo": ("fis_tip_disc", "str"),
            "discapacidad.porcentaje": ("fis_porc_disc", "int"),
        }

        # Preparar valores para SQL
        campos_sql = []
        valores_sql = {"cllc_cdg": data["cllc_cdg"]}

        for frontend_key, (db_field, tipo) in mapa_campos.items():
            if "." in frontend_key:
                # Campo anidado
                main_key, sub_key = frontend_key.split(".")
                if main_key in data and isinstance(data[main_key], dict) and sub_key in data[main_key]:
                    campos_sql.append(f"{db_field} = :{db_field}")
                    valores_sql[db_field] = data[main_key][sub_key]
            else:
                if tipo == "date":
                    valor = datetime.strptime(data[frontend_key], "%Y-%m-%d")
                    campos_sql.append(f"{db_field} = :{db_field}")
                    valores_sql[db_field] = valor
                    continue
                if frontend_key in data:
                    campos_sql.append(f"{db_field} = :{db_field}")
                    valores_sql[db_field] = data[frontend_key]
        if campos_sql:
            update_sql = f"""
                UPDATE sna.sna_ficha_socioeconomica
                SET {", ".join(campos_sql)}
                WHERE cllc_cdg = :cllc_cdg
            """
            cursor.execute(update_sql, valores_sql)
            conn.commit()

        return {"message": "Ficha socioeconómica actualizada correctamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()