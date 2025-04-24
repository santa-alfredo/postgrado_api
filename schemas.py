from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Literal, List, Union
from datetime import date, datetime
from pydantic.v1 import validator
import re

class User(BaseModel):
    name: str
    email: EmailStr

class LoginForm(BaseModel):
    email: EmailStr
    password: str

class TokenForm(BaseModel):
    token: str

class Cliente(BaseModel):
    cllc_cdg: int # primary key
    cam_codigo: Optional[int]
    car_codigo: Optional[int]
    cdds_cdg: Optional[str]
    cllc_adicionado: Optional[str]
    cllc_calle: Optional[str]
    cllc_cargo_trabajo: Optional[str]
    cllc_cdg_ref: Optional[int]
    cllc_celular: Optional[str]
    cllc_cnd_pago: Optional[str]
    cllc_contacto: Optional[str]
    cllc_email: Optional[EmailStr]
    cllc_email_univ: Optional[EmailStr]
    cllc_estado: Optional[str]
    cllc_etnia: Optional[int]
    cllc_fax: Optional[str]
    cllc_fch_ingreso: date
    cllc_fecha_adicion: Optional[date]
    cllc_fecha_modificacion: Optional[date]
    cllc_fecha_nac: Optional[date]
    cllc_fono: Optional[str]
    cllc_fono2: Optional[str]
    cllc_g_contable: Optional[int]
    cllc_hra_consulta: Optional[str]
    cllc_hra_pago: Optional[str]
    cllc_lug_pago: Optional[str]
    cllc_modificado: Optional[str]
    cllc_nmb: str
    cllc_nmr: Optional[str]
    cllc_obs: Optional[str]
    cllc_observaciones: Optional[str]
    cllc_pers_contacto: Optional[str]
    cllc_plazo_pago: Optional[int]
    cllc_ruc: str
    cllc_rut: int
    cllc_ruta: Optional[str]
    cllc_rut_dv: Optional[str]
    cllc_senescyt: Optional[str]
    cllc_tipo_cliente: Optional[str]
    cllc_tipo_cliente_aux: Optional[str]
    cllc_tipo_contrib: Optional[str]
    cllc_tipo_usuario: Optional[str]
    cllc_tpo_documento: Optional[str]
    cllc_web: Optional[str]
    cmns_cdg: Optional[str]
    cnvt_cdg: Optional[str]
    cod_gru_ente: Optional[int]
    cup_codigo: Optional[int]
    empr_codigo: Optional[str]
    fac_codigo: Optional[int]
    gcll_cdg: Optional[str]
    grup_codigo: Optional[int]
    grup_codigo_aux: Optional[int]
    ina_jornada: Optional[int]
    ine_codigo: Optional[int]
    inu_codigo: Optional[int]
    mls_msg: Optional[str]
    mod_codigo: Optional[int]
    nctb_cdg_nivel_1: Optional[str]

# Ficha Socioeconomica
class OtraUniversidad(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    carrera: str = Field(..., min_length=2, max_length=100)

class Empleado(BaseModel):
    tipo: Literal["empleado"] = "empleado"
    empresa: str = Field(..., min_length=2, max_length=100)
    cargo: str = Field(..., min_length=2, max_length=100)
    sueldo: float = Field(..., ge=0, le=1000000)

class NegocioPropio(BaseModel):
    tipo: Literal["negocio propio"] = "negocio propio"
    negocio: str = Field(..., min_length=2, max_length=100)
    ingresos: float = Field(..., ge=0, le=1000000)
    gastos: float = Field(..., ge=0, le=1000000)
    actividades: str = Field(..., min_length=2, max_length=100)

class Pensionado(BaseModel):
    tipo: Literal["pensionado"] = "pensionado"
    fuente: str = Field(..., min_length=2, max_length=100)
    monto: float = Field(..., ge=0)

class OtroLaboral(BaseModel):
    tipo: Literal["otro"] = "otro"
    descripcion: str = Field(..., min_length=2, max_length=100)

class MiembroFamiliar(BaseModel):
    sueldo: float = Field(..., ge=0)
    edad: int = Field(..., ge=1, le=100)
    parentesco: Literal["hijo", "padreMadre", "hermano", "conyuge", "otro"]
    ocupacion: Optional[str] = None

class Discapacidad(BaseModel):
    tipo: Literal["fisica", "psiquica", "auditiva", "visual", "intelectual", "multiple"]
    porcentaje: int = Field(..., ge=10, le=100)
    carnet: str = Field(...)

class EnfermedadCronica(BaseModel):
    nombre: str = Field(...)
    lugaresTratamiento: Literal["clinicaPrivada", "publica", "iess", "otro"]

class FichaSocioeconomicaSchema(BaseModel):
    cllc_cdg: int # primary key
    nombres: str = Field(..., min_length=2, max_length=50)
    cedula: str = Field(..., min_length=10, max_length=13)
    fechaNacimiento: date = Field(...)
    genero: str = Field(...)
    estadoCivil: str = Field(..., max_length=20)
    telefono: Optional[str] = Field(None, min_length=10, max_length=15)
    email: str = Field(...)
    cambioResidencia: Optional[bool] = None
    direccion: str = Field(..., min_length=10, max_length=200)
    provinciaId: str = Field(...)
    ciudadId: str = Field(...)
    parroquiaId: str = Field(...)
    carrera: str = Field(..., min_length=2, max_length=100)
    colegio: str = Field(..., min_length=2, max_length=100)
    tipoColegio: str = Field(..., max_length=20)
    anioGraduacion: int = Field(..., ge=1900, le=2025)
    semestre: str = Field(..., pattern=r"^\d+$")
    promedio: float = Field(..., ge=0, le=10)
    estudioOtraUniversidad: bool = Field(...)
    otraUniversidad: Optional[OtraUniversidad] = None
    beca: Optional[bool] = None
    ingresosFamiliares: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$")
    gastosMensuales: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$")
    vivienda: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$")
    transporte: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$")
    alimentacion: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$")
    otrosGastos: str = Field(..., pattern=r"^\d+(\.\d{1,2})?$")
    situacionLaboral: Literal["empleado", "desempleado", "negocio propio", "pensionado", "otro"]
    laboral: Optional[Union[Empleado, NegocioPropio, Pensionado, OtroLaboral]] = None
    relacionCompa: Literal["excelente", "buena", "regular", "mala"]
    integracionUmet: Literal["si", "no"]
    relacionDocente: Literal["excelente", "buena", "regular", "mala"]
    relacionPadres: Literal["excelente", "buena", "regular", "mala"]
    relacionPareja: Optional[Literal["excelente", "buena", "regular", "mala"]] = None
    estadoFamiliar: Literal["cabezaHogar", "vivePadres", "independiente"]
    miembros: Optional[List[MiembroFamiliar]] = None
    tieneDiscapacidad: Literal["si", "no"]
    discapacidad: Optional[Discapacidad] = None
    tieneEnfermedadCronica: Literal["si", "no"]
    enfermedadCronica: Optional[EnfermedadCronica] = None

    @validator("nombres")
    def validate_nombres(cls, v):
        if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", v):
            raise ValueError("Los nombres solo pueden contener letras y espacios")
        return v

    @validator("cedula")
    def validate_cedula(cls, v):
        if not re.match(r"^\d+$", v):
            raise ValueError("La cédula solo puede contener números")
        return v

    @validator("telefono")
    def validate_telefono(cls, v):
        if v and not re.match(r"^[\d\s()-]+$", v):
            raise ValueError("El teléfono solo puede contener números, espacios, guiones y paréntesis")
        return v

    @validator("email")
    def validate_email(cls, v):
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Debe ser un correo electrónico válido")
        return v

    @validator("fechaNacimiento")
    def validate_fecha_nacimiento(cls, v):
        if v.year < 1900 or v.year > 2025:
            raise ValueError("El año de nacimiento debe estar entre 1900 y 2025")
        return v

    @validator("otraUniversidad")
    def validate_otra_universidad(cls, v, values):
        if values.get("estudioOtraUniversidad") and not v:
            raise ValueError("Otra universidad es requerida si estudió en otra universidad")
        if not values.get("estudioOtraUniversidad") and v:
            raise ValueError("Otra universidad no debe proporcionarse si no estudió en otra universidad")
        return v

    @validator("discapacidad")
    def validate_discapacidad(cls, v, values):
        if values.get("tieneDiscapacidad") == "si" and not v:
            raise ValueError("Discapacidad es requerida si tiene discapacidad")
        if values.get("tieneDiscapacidad") == "no" and v:
            raise ValueError("Discapacidad no debe proporcionarse si no tiene discapacidad")
        return v

    @validator("enfermedadCronica")
    def validate_enfermedad_cronica(cls, v, values):
        if values.get("tieneEnfermedadCronica") == "si" and not v:
            raise ValueError("Enfermedad crónica es requerida si tiene enfermedad crónica")
        if values.get("tieneEnfermedadCronica") == "no" and v:
            raise ValueError("Enfermedad crónica no debe proporcionarse si no tiene enfermedad crónica")
        return v