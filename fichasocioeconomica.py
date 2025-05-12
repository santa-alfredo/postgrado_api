from fastapi import APIRouter, Request, Response, HTTPException, Depends, Body, Query
from fastapi.responses import StreamingResponse
from schemas import FichaSocioeconomicaSchema
import os, io, base64
from database import get_connection
import cx_Oracle
from datetime import datetime
from auth import get_user_from_token
from schemas import User
from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
import tempfile
from dotenv import load_dotenv
from typing import Optional
from pathlib import Path

load_dotenv()

router = APIRouter(prefix="/ficha", tags=["ficha"])


BASE_URL = os.getenv("BASE_URL")

def generar_update_sql(data, mapa_campos: dict, tabla: str, where_cond: str, extras: dict = {}) -> tuple[str, dict]:
    campos_sql = []
    valores_sql = dict(extras)  # Agrega extras como cllc_cdg, fis_pel_codigo, etc.

    for frontend_key, db_field in mapa_campos.items():
        if "." in frontend_key:
            main_key, sub_key = frontend_key.split(".")
            nested_obj = getattr(data, main_key, None)
            if nested_obj:
                valor = getattr(nested_obj, sub_key, None)
                if valor is not None:
                    campos_sql.append(f"{db_field} = :{db_field}")
                    valores_sql[db_field] = valor
        else:
            valor = getattr(data, frontend_key, None)
            if valor is not None:
                campos_sql.append(f"{db_field} = :{db_field}")
                valores_sql[db_field] = valor

    if not campos_sql:
        return None, None

    update_sql = f"""
        UPDATE {tabla}
        SET {", ".join(campos_sql)}
        WHERE {where_cond}
    """
    return update_sql, valores_sql


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
        mapeo_ficha = {
            "fechaNacimiento": "fis_fecha_nac",
            "estadoCivil": "fis_estado_civil",
            "telefono": "fis_celular",
            "nacionalidad": "fis_nacionalidad",
            "genero": "fis_sexo",
            "generoIdentidad": "fis_genero",
            "orientacionSexual": "fis_orientacio_sexual",
            
            "tieneDiscapacidad": "fis_discapacidad",
            "discapacidad.tipo": "fis_tip_disc",
            "discapacidad.porcentaje": "fis_porc_disc",
            "discapacidad.carnet": "fis_nro_carnet",
            "discapacidad.tieneDiagnosticoPresuntivo": "fis_diagnostico_p",
            "enfermedadCronica.nombre": "fis_enfer_present",

            
            "relacionCompa": "fis_relac_companeros",
            "relacionDocente": "fis_relac_docentes",
            "relacionPadres": "fis_relac_padres",
            "relacionPareja": "fis_relac_pareja",
            "integracionUmet": "fis_integrado_umet",

            "cambioResidencia": "fis_tuvo_camb_resi",
            "direccion": "fis_direccion",
            "pais.label": "fis_pais_dom",
            "provincia.label": "fis_provincia",
            "ciudad.label": "fis_ciudad",
            "parroquia.label": "fis_parroquia",
            
            "colegio.label": "fis_cole_graduo",
            "colegio.tipoLabel": "fis_cole_tipo",
            "promedio": "fis_calif_grado",

            "carrera": "fis_carrera_matricula",
            "semestre": "fis_semestre_matricula",
            "beca": "fis_beca",
            "estudioOtraUniversidad": "fis_est_otr_u",
            "otraUniversidad.razon": "fis_raz_camb_u",

            "situacionLaboral": "fis_situacion_lab",
            "trabaja" : "fis_situacion_laboral",
            "dependenciaEconomica": "fis_dependencia_economica",
            "laboral.dependiente": "fis_eco_depende",
            "estadoFamiliar": "fis_vive_con",
            "laboral.empresa": "fis_nombre_emp",
            "laboral.sueldo": "fis_sueldo",
            "laborarl.cargo":"fis_cargo",
            "internet": "fis_tiene_internet",
            "computadora": "fis_tiene_compu",
            "cabezaHogar": "fis_cabeza_familia",
            "tipoCasa": "fis_casa",
            "origenRecursos": "fis_orig_recur_sust",
            "origenEstudios": "fis_orig_rec_est",
            "academicoPadre": "fis_instruccion_padre",
            "academicoMadre": "fis_instruccion_madre",
            "sueldoPadre": "fis_sueldo_padre",
            "sueldoMadre": "fis_sueldo_madre",
            "numeroHijos":"fis_num_hijos",
            "numeroFamiliar": "fis_cant_fam",
            "personasTrabajan": "fis_nro_pers_trab",
            "ocupacionPadre":"fis_instruccion_padre",
            "situacionLaboralPadre": "fis_situ_lab_padres",
            "ocupacionMadre":"fis_instruccion_madre",
            "situacionLaboralMadre": "fis_situ_lab_madre",
            
            "etnia": "fis_recono_etnico",
            "indigenaNacionalidad": "nac_codigo",

            "contactoParentesco": "fis_parentesco_emerg",
            "contactoNombre": "fis_nombre_emerg",
            "contactoCelular": "fis_celular_emerg",
        }
        cursor = conn.cursor()

        # Verifica existencia de Ficha
        cursor.execute("""
            SELECT 1 FROM sna.sna_ficha_socioeconomica WHERE cllc_cdg = :cllc_cdg
        """, {"cllc_cdg": user.username})
        exists = cursor.fetchone() is not None
        
        # Consultar la edad desde SNA_ALUMNO
        cursor.execute("""
            SELECT TRUNC(MONTHS_BETWEEN(SYSDATE, alu_fecha_nacimiento) / 12) AS edad
            FROM sna.sna_alumno
            WHERE cllc_cdg = :cllc_cdg """, {"cllc_cdg": user.username})
        row = cursor.fetchone()

        # Si no existe edad actualizar con data
        if (row is None or row[0] is None) and data.fechaNacimiento:
            # actualizar la fecha de nacimiento 
            cursor.execute("""
                UPDATE sna.sna_alumno
                SET alu_fecha_nacimiento = :fecha_nac
                WHERE cllc_cdg = :cllc_cdg
            """, {
                "fecha_nac": data.fechaNacimiento,
                "cllc_cdg": user.username
            })
            conn.commit()
            # 3. Volver a consultar la edad ya actualizada
            cursor.execute("""
                SELECT TRUNC(MONTHS_BETWEEN(SYSDATE, alu_fecha_nacimiento) / 12) AS edad
                FROM sna.sna_alumno
                WHERE cllc_cdg = :cllc_cdg
            """, {"cllc_cdg": user.username})
            row = cursor.fetchone()

        edad = row[0] if row else 0

        if not exists:
            raise Exception("No tiene una ficha pre-creada")
        

        mapeo_alumno = {
            "estadoCivil":"cod_estado",
            "pais.value":"area_codigo_pais_dom",
            "provincia.value":"area_codigo_provincia_dom",
            "ciudad.value":"area_codigo_ciudad_dom",
            "parroquia.value":"area_codigo_parroquia_dom",
            "fechaNacimiento":"alu_fecha_nacimiento",
            "etnia": "alu_autoreconocimiento_etn",
            "indigenaNacionalidad":"nac_codigo",
        }

        # Generar y ejecutar actualización de alumno
        sql_alumno, valores_alumno = generar_update_sql(
            data,
            mapa_campos=mapeo_alumno,
            tabla="sna.sna_alumno",
            where_cond="cllc_cdg = :cllc_cdg",
            extras={"cllc_cdg": user.username}
        )
        if sql_alumno:
            cursor.execute(sql_alumno, valores_alumno)
            conn.commit()

        mapeo_cliente = {
            "direccion":"cllc_calle",
            "telefono":"cllc_celular",
            "email":"cllc_email",
            "contactoNombre":"cllc_pers_contacto",
            "contactoCelular":"cllc_contacto",
            "fechaNacimiento":"cllc_fecha_nac",
        }

        # Generar y ejecutar actualización de cliente
        sql_cliente, valores_cliente = generar_update_sql(
            data,
            mapa_campos=mapeo_cliente,
            tabla="sigac.cliente_local",
            where_cond="cllc_cdg = :cllc_cdg",
            extras={"cllc_cdg": user.username}
        )
        if sql_cliente:
            cursor.execute(sql_cliente, valores_cliente)
            conn.commit()

        if data.miembros:
            miembros_dicts = []
            for m in data.miembros:
                miembros_dicts.append({
                    'cllc_cdg': user.username,
                    'pel_codigo': periodo,
                    'parentesco': m.parentesco,
                    'rango_edad': m.edad,
                    'rango_sueldo': m.sueldo,
                    'instruccion': m.ocupacion
                })

            sql = """
                INSERT INTO sna.SNA_MIEMBROS_HOGAR (
                    cllc_cdg, pel_codigo, parentesco, rango_edad, rango_sueldo, instruccion
                ) VALUES (
                    :cllc_cdg, :pel_codigo, :parentesco, :rango_edad, :rango_sueldo, :instruccion
                )
            """
            cursor.executemany(sql, miembros_dicts)
        
        # Preparar valores para SQL UPDATE
        campos_sql = []
        campos_sql.append("fis_pel_codigo = :fis_pel_codigo")
        campos_sql.append("fis_edad = :fis_edad")
        valores_sql = {"cllc_cdg": user.username, "fis_pel_codigo": periodo, 'fis_edad':edad}

        for frontend_key, db_field in mapeo_ficha.items():
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
            "ficha": {"id": user.username},
            "periodo": True
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

        def fetch_ficha():
            cursor.execute("""
                SELECT fi.*, cl.cllc_nmb, cl.cllc_ruc, cl.cllc_email_univ, cl.cllc_email, al.alu_fecha_nacimiento as cllc_fecha_nac,
                    al.alu_genero, cl.cllc_celular
                FROM sna.sna_ficha_socioeconomica fi
                JOIN sigac.cliente_local cl ON cl.cllc_cdg = fi.cllc_cdg
                JOIN sna.sna_alumno al ON al.cllc_cdg = fi.cllc_cdg
                WHERE cl.cllc_cdg = :cllc_cdg
                ORDER BY fis_pel_codigo DESC
            """, {"cllc_cdg": user.username})
            row = cursor.fetchone()
            return dict(zip([col[0].lower() for col in cursor.description], row)) if row else None
        
        ficha = fetch_ficha()
        if not ficha:
            # si no existe la ficha socioeconomica, se crea una nueva
            cursor.callproc("sna.sna_inserta_fic_soc2", [
                int(user.username)
            ])
            # se obtiene la ficha socioeconomica
            ficha = fetch_ficha()
            if not ficha:
                raise HTTPException(status_code=404, detail="Ficha socioeconómica no encontrada")
        
        if isinstance(ficha["cllc_fecha_nac"], datetime):
            ficha["cllc_fecha_nac"] = ficha["cllc_fecha_nac"].strftime("%Y-%m-%d")

        #! Obtener beca
        cursor.execute("""
            SELECT DISTINCT tb.tib_descripcion
                FROM SNA.SNA_BECA B,sna.sna_tipo_beca tb
                WHERE B.CLLC_CDG = :cllc_cdg 
                AND B.PEL_CODIGO = :pel_codigo
                AND B.BEC_ELIMINADO = 'N'
                AND B.BEC_APROBACION_VICERRECTOR = 'A'
                AND B.SED_CODIGO_PREFACTURA IN (1,2,3)
                AND B.tib_codigo_concede  = tb.tib_codigo
                and  ROWNUM = 1
        """, {"cllc_cdg": user.username, "pel_codigo": periodo})
        row = cursor.fetchone()
        beca = row[0] if row else ""
        # Select para encontrar la carrera del estudiante
        cursor.execute("""
            SELECT ip.car_codigo_postgrado,prp_titulo_proyecto
            FROM sna.sna_inscripcion_postgrado ip,sna.sna_proyecto_postgrado pp
            WHERE ip.cllc_cdg = :cllc_cdg
            AND ip.inp_pagado = 'S'
            AND ip.inp_aprobado = 'S'
            AND ip.inp_eliminado = 'N'
            AND ip.prp_numero_postgrado = pp.prp_numero
            AND ip.fac_codigo_postgrado = pp.fac_codigo
            AND ip.car_codigo_postgrado = pp.car_codigo
            AND  ROWNUM = 1
        """, {"cllc_cdg": user.username})
        row = cursor.fetchone()
        carrera = {"id": str(row[0]), "nombre": row[1]} if row else {"id": "", "nombre": ""}

        # consulta colegio
        colegio = {"value": "", "label": ficha['fis_cole_graduo'] or "", "tipoValue": "", "tipoLabel": ficha['fis_cole_tipo'] or ""}
        #! Formatear la ficha
        ficha = {
            "nombres": ficha["cllc_nmb"],
            "cedula": ficha["cllc_ruc"],
            "periodo": ficha["fis_pel_codigo"],
            "email": ficha["cllc_email_univ"] or ficha["cllc_email"],
            "fechaNacimiento": ficha["cllc_fecha_nac"],
            "genero": ficha["alu_genero"],
            "estadoCivil": ficha["fis_estado_civil"],
            "nacionalidad": ficha["fis_nacionalidad"] or "593",
            "telefono": ficha["cllc_celular"],
            "colegio": colegio,
            "tipoColegio": ficha["fis_cole_tipo"] or 0,
            "indigenaNacionalidad": str(ficha.get("nac_codigo", 34)),
            "beca": beca,
            "carrera": carrera,
            "promedio": ficha["fis_calif_grado"] or 0,
            "direccion": ficha["fis_direccion"] or "",
            "etnia": ficha["fis_recono_etnico"] or "",
            "anioGraduacion": ficha["fis_especialidad"] or 2000,
            "semestre": str(ficha.get("fis_semestre_matricula",0)) or "",
            "pais": {
                "value": "999999",
                "label": ficha["fis_pais_dom"] or ""
            },
            "provincia": {
                "value": "999999",
                "label": ficha["fis_provincia"] or ""
            },
            "ciudad": {
                "value": "999999",
                "label": ficha["fis_ciudad"] or ""
            },
            "parroquia": {
                "value": "999999",
                "label": ficha["fis_parroquia"] or ""
            },
            "tipoCasa":ficha['fis_casa'] or "",
            "internet": ficha['fis_tiene_internet'],
            "computadora": ficha['fis_tiene_compu'],
            "origenRecursos": ficha['fis_orig_recur_sust'],
            "origenEstudios": ficha['fis_orig_rec_est'],
            "relacionCompa": ficha['fis_relac_companeros'],
            "integracionUmet": ficha['fis_integrado_umet'],
            "relacionDocente": ficha['fis_relac_docentes'],
            "relacionPadres": ficha['fis_relac_padres'],
            "relacionPareja": ficha['fis_relac_pareja'],
        }
        return {
            "message": "Ficha socioeconómica encontrada",
            "ficha": ficha,
            "periodo": periodo == int(ficha["periodo"] or 0)
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
        periodo = 65
        # Datos de ejemplo para la ficha socioeconómica
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fi.*, cl.cllc_nmb, cllc_ruc, cllc_email FROM sna.sna_ficha_socioeconomica fi
            JOIN sigac.cliente_local cl on cl.cllc_cdg = fi.cllc_cdg
            WHERE cl.cllc_cdg = :cllc_cdg 
            AND fis_pel_codigo = :fis_pel_codigo
        """, {"cllc_cdg": cllc_cdg, "fis_pel_codigo": periodo})
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Ficha socioeconómica no encontrada")
        
        # Convertir la fila a diccionario
        ficha = dict(zip([col[0].lower() for col in cursor.description], row))

        cursor.execute("""
            SELECT * FROM sna.sna_miembros_hogar
            WHERE cllc_cdg = :cllc_cdg AND pel_codigo = :fis_pel_codigo
        """, {'cllc_cdg': cllc_cdg, 'fis_pel_codigo': periodo})
        columns = [col[0].lower() for col in cursor.description]
        rows = cursor.fetchall()
        if rows is None:
            miembros_hogar=[]
        miembros_hogar = [dict(zip(columns, row)) for row in rows]        
        
        # Configurar el entorno de Jinja2
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('ficha_socioeconomica.html')
        
        # Renderizar la plantilla con los datos
        html_content = template.render({"ficha": ficha, "miembros_hogar": miembros_hogar, "foto_url": f"{BASE_URL}/static/logo/avatar.png"})
        
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

@router.get("/colegio")
def search_colegios(
    search: Optional[str] = Query(default="", min_length=0),
    tipo: Optional[str] = Query(default=None),
    conn: cx_Oracle.Connection = Depends(get_connection)  # ✅ correcto aquí
):
    try:
        cursor = conn.cursor()
        base_query = """
            SELECT 
                ie.ine_codigo, 
                ie.ine_descripcion, 
                tie.tie_descripcion,
                tie.tie_codigo
            FROM 
                sna.sna_institucion_educativa ie
            JOIN 
                sna.sna_tipo_institucion_educativa tie 
                ON ie.tie_codigo = tie.tie_codigo
            WHERE 
                ie.ine_tipo_institucion <> 'UNIVERSIDAD'
                AND LOWER(ie.ine_descripcion) LIKE :search
        """
        params = {"search": f"%{search.lower()}%"}

        # if tipo:
        #     base_query += " AND LOWER(tie.tie_descripcion) = :tipo"
        #     params["tipo"] = 'particular'

        cursor.execute(base_query, params)
        rows = cursor.fetchall()

        columns = [col[0].lower() for col in cursor.description]
        colegios = [dict(zip(columns, row)) for row in rows]

        return colegios

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error buscando colegios: {str(e)}")
    finally:
        cursor.close()

@router.get("/colegio/{ine_codigo}")
def get_colegio(
    ine_codigo: int,
    conn: cx_Oracle.Connection = Depends(get_connection)
):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ie.ine_codigo, ie.ine_descripcion, tie.tie_codigo, tie.tie_descripcion 
            FROM sna.sna_institucion_educativa ie
            JOIN sna.sna_tipo_institucion_educativa tie ON ie.tie_codigo = tie.tie_codigo
            WHERE ie.ine_codigo = :ine_codigo
        """, {"ine_codigo": ine_codigo})
        row = cursor.fetchone()
        if row is None:
            return {
                "message": "Colegio no encontrado",
            }
        return {
            "ine_codigo": row[0],
            "ine_descripcion": row[1],
            "tie_codigo": row[2],
            "tie_descripcion": row[3]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo el colegio: {str(e)}")
    finally:
        cursor.close()


@router.get("/paises")
def get_paises(
    conn: cx_Oracle.Connection = Depends(get_connection)
):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT area_nombre as label,area_codigo as value
            FROM   easi.area_geografica
            WHERE  area_tipo   = 'PE'
        """)
        rows = cursor.fetchall()
        columns = [col[0].lower() for col in cursor.description]
        provincias = [dict(zip(columns, row)) for row in rows]
        return provincias
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo las provincias: {str(e)}")
    finally:
        cursor.close()

@router.get("/provincias")
def get_provincias(
    paisId: int,
    conn: cx_Oracle.Connection = Depends(get_connection)
):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT area_nombre as label,area_codigo as value
            FROM   easi.area_geografica
            WHERE  area_tipo   = 'PR'
            AND area_padre = :pais
        """, {'pais': paisId})
        rows = cursor.fetchall()
        columns = [col[0].lower() for col in cursor.description]
        provincias = [dict(zip(columns, row)) for row in rows]
        return provincias
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo las provincias: {str(e)}")
    finally:
        cursor.close()


@router.get("/ciudades")
def get_ciudades(
    provinciaId: int,
    conn: cx_Oracle.Connection = Depends(get_connection)
):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT area_nombre as label,area_codigo as value
            FROM   easi.area_geografica
            WHERE  area_tipo   = 'CI'
            AND area_padre=:provinciaId
        """, {"provinciaId": provinciaId})
        rows = cursor.fetchall()
        columns = [col[0].lower() for col in cursor.description]
        ciudades = [dict(zip(columns, row)) for row in rows]
        return ciudades
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo las ciudades: {str(e)}")
    finally:
        cursor.close()

@router.get("/parroquias")
def get_parroquias(
    ciudadId: str,
    conn: cx_Oracle.Connection = Depends(get_connection)
):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT area_nombre as label,area_codigo as value
            FROM   easi.area_geografica
            WHERE  area_tipo   = 'CM'
            AND area_padre=:ciudadId
        """, {"ciudadId": ciudadId})
        rows = cursor.fetchall()
        columns = [col[0].lower() for col in cursor.description]
        parroquias = [dict(zip(columns, row)) for row in rows]
        return parroquias
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo las parroquias: {str(e)}")
    finally:
        cursor.close()
