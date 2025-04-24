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
        """, {"cllc_cdg": data.cllc_cdg})
        exists = cursor.fetchone() is not None

        if not exists:
            # Armar INSERT
            campos = ["cllc_cdg"]
            valores = [":cllc_cdg"]
            params = {"cllc_cdg": data.cllc_cdg}

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
        valores_sql = {"cllc_cdg": data.cllc_cdg}

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

        return {"message": "Ficha socioeconómica actualizada correctamente"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()