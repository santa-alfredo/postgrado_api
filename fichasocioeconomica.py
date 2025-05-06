from fastapi import APIRouter, Request, Response, HTTPException, Depends, Body, Query
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
from typing import Optional

load_dotenv()

router = APIRouter(prefix="/ficha", tags=["ficha"])


BASE_URL = os.getenv("BASE_URL")

def obtener_valor_campo(valor):
    # Verifica si el valor es un objeto con el atributo 'value'
    if hasattr(valor, 'value'):
        return valor.value
    # Si no tiene el atributo 'value', devuelve el valor tal como está
    return valor

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
            "telefono": "fis_celular",
            "nacionalidad": "fis_nacionalidad",
            
            "tieneDiscapacidad": "fis_discapacidad",
            "discapacidad.tipo": "fis_tip_disc",
            "discapacidad.porcentaje": "fis_porc_disc",
            "discapacidad.carnet": "fis_nro_carnet",
            "enfermedadCronica.nombre": "fis_enfer_present",
            
            "relacionCompa": "fis_relac_companeros",
            "relacionDocente": "fis_relac_docentes",
            "relacionPadres": "fis_relac_padres",
            "relacionPareja": "fis_relac_pareja",
            "integracionUmet": "fis_integrado_umet",

            "cambioResidencia": "fis_tuvo_camb_resi",
            "direccion": "fis_direccion",
            "provinciaId": "fis_provincia",
            "ciudadId": "fis_ciudad",
            "parroquiaId": "fis_parroquia",
            
            "colegio.value": "fis_cole_graduo",
            "tipoColegio": "fis_cole_tipo",
            "promedio": "fis_calif_grado",

            "carrera": "fis_carrera_matricula",
            "semestre": "fis_semestre_matricula",
            "beca": "fis_beca",
            "estudioOtraUniversidad": "fis_est_otr_u",
            "otraUniversidad.razon": "fis_raz_camb_u",

            "situacionLaboral": "fis_situacion_lab",
            "dependenciaEconomica": "fis_dependencia_economica",
            "laboral.dependiente": "fis_vive_con",
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
        }
        
        cursor = conn.cursor()

        # Verifica existencia
        cursor.execute("""
            SELECT 1 FROM sna.sna_ficha_socioeconomica WHERE cllc_cdg = :cllc_cdg
        """, {"cllc_cdg": user.username})
        exists = cursor.fetchone() is not None

        cursor.execute("""
            SELECT TRUNC(MONTHS_BETWEEN(SYSDATE, cllc_fecha_nac) / 12) AS edad
            FROM sigac.cliente_local
            WHERE cllc_cdg = :cllc_cdg """, {"cllc_cdg": user.username})
        row = cursor.fetchone()
        edad = row[0] if row else 0

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
        campos_sql.append("fis_edad = :fis_edad")
        valores_sql = {"cllc_cdg": user.username, "fis_pel_codigo": periodo, 'fis_edad':edad}

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
        cursor.execute("""SELECT cllc_cdg FROM sigac.cliente_local where cllc_cdg = :cllc_cdg""", {'cllc_cdg':user.username})
        row = cursor.fetchone()
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
                SELECT fi.*, cl.cllc_nmb, cl.cllc_ruc, cl.cllc_email_univ, cl.cllc_email, cl.cllc_fecha_nac,
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
        carrera = {"id": str(row[0]), "nombre": row[1]} if row else {"id": None, "nombre": None}

        # consulta colegio
        colegio = {"value": 0, "label": "Sin colegio", "tipoValue": 0, "tipoLabel": ""}
        if ficha['fis_cole_graduo'] and ficha['fis_cole_tipo']:
            cursor.execute("""
                SELECT ie.ine_codigo, ie.ine_descripcion, tie.tie_codigo, tie.tie_descripcion
                FROM sna.sna_institucion_educativa ie ,sna.sna_tipo_institucion_educativa tie
                WHERE 
                ie.ine_tipo_institucion <> 'UNIVERSIDAD'
                and ie.tie_codigo=tie.tie_codigo
                and ie.ine_codigo = :ine_codigo
                and tie.tie_codigo = :tie_codigo
            """, {'ine_codigo':ficha['fis_cole_graduo'], 'tie_codigo': ficha['fis_cole_tipo']})
            row = cursor.fetchone()
            colegio = {"value": str(row[0]), "label": row[1], "tipoValue": str(row[2]), "tipoLabel": row[3]}
        
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
            "indigenaNacionalidad": ficha.get("nac_codigo", 34),
            "beca": beca,
            "carrera": carrera,
            "promedio": ficha["fis_calif_grado"] or 0,
            "direccion": ficha["fis_direccion"] or "",
            "etnia": ficha["fis_recono_etnico"] or "",
            "anioGraduacion": ficha["fis_especialidad"] or 2000,
            "semestre": str(ficha.get("fis_semestre_matricula",0)) or "",
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


@router.get("/provincias")
def get_provincias(
    conn: cx_Oracle.Connection = Depends(get_connection)
):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT area_nombre as nombre,area_codigo as id
            FROM   easi.area_geografica
            WHERE  area_tipo   = 'PR'
            AND area_padre='593'
        """)
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
            SELECT area_nombre as nombre,area_codigo as id
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
            SELECT area_nombre as nombre,area_codigo as id
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
