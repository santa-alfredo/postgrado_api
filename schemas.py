from pydantic import BaseModel, EmailStr, Field, model_validator
from typing import Optional, Dict, Literal, List, Union
from datetime import date, datetime
from pydantic.v1 import validator
import re

class User(BaseModel):
    username: str
    email: EmailStr
    name: str

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
    razon: str = Field(..., min_length=2, max_length=100)

class Empleado(BaseModel):
    tipo: Literal["empleado"] = "empleado"
    empresa: str = Field(..., min_length=1, max_length=100)
    cargo: str = Field(..., min_length=1, max_length=100)
    sueldo: str = Field(..., min_length=1, max_length=100)

class NegocioPropio(BaseModel):
    tipo: Literal["negocio propio"] = "negocio propio"
    negocio: str = Field(..., min_length=2, max_length=100)
    actividades: str = Field(..., min_length=2, max_length=100)

class Pensionado(BaseModel):
    tipo: Literal["pensionado"] = "pensionado"
    fuente: str = Field(..., min_length=2, max_length=100)
    monto: float = Field(..., ge=0)

class OtroLaboral(BaseModel):
    tipo: Literal["otro"] = "otro"
    descripcion: str = Field(..., min_length=2, max_length=100)

class Desempleado(BaseModel):
    tipo: Literal["desempleado"] = "desempleado"
    dependiente: Literal["padre", "madre", "hermano", "otro"]

class MiembroFamiliar(BaseModel):
    sueldo: str = ""
    edad: str = ""
    parentesco: Literal["hijo", "padre", "madre", "hermano", "conyuge", "otro"]
    ocupacion: Optional[str] = None

class Discapacidad(BaseModel):
    tipo: Literal["fisica", "psiquica", "auditiva", "visual", "intelectual", "multiple"]
    porcentaje: int = Field(..., ge=10, le=100)
    carnet: str = Field(...)

class EnfermedadCronica(BaseModel):
    nombre: str = Field(...)
    lugaresTratamiento: Literal["clinicaPrivada", "publica", "iess", "otro"]

class Colegio(BaseModel):
    value: str
    label: str
    tipoValue: str
    tipoLabel: str

    class Config:
        min_anystr_length = 1
        anystr_strip_whitespace = True

class FichaSocioeconomicaSchema(BaseModel):
    cllc_cdg: Optional[int] = None # primary key
    nombres: str = Field(..., min_length=2, max_length=50)
    cedula: str = Field(..., min_length=10, max_length=13)
    fechaNacimiento: Optional[date] = None
    genero: str = Field(...)
    estadoCivil: str = Field(..., max_length=20)
    telefono: Optional[str] = Field(None, min_length=10, max_length=15)
    email: str = Field(...)
    nacionalidad: str = Field(..., max_length=30)
    cambioResidencia: Optional[str] = "N"
    direccion: str = Field(..., min_length=10, max_length=200)
    provinciaId: str = Field(...)
    ciudadId: str = Field(...)
    parroquiaId: str = Field(...)
    carrera: str = Field(..., min_length=2, max_length=100)
    colegio: Colegio = Field(...)
    tipoColegio: str = Field(..., max_length=20)
    anioGraduacion: int = Field(..., ge=1900, le=2025)
    semestre: str = Field(..., pattern=r"^\d+$")
    promedio: float = Field(..., ge=0, le=10)
    estudioOtraUniversidad: bool = Field(...)
    otraUniversidad: Optional[OtraUniversidad] = None
    beca: Optional[str] = "N"
    internet: Optional[str] = "N"
    computadora: Optional[str] = "N"
    ingresosFamiliares: str = ""
    gastosMensuales: str = ""
    vivienda: str = ""
    transporte: str = ""
    alimentacion: str = ""
    otrosGastos: str = ""
    situacionLaboral: Literal["empleado", "desempleado", "negocio propio", "pensionado", "otro"]
    trabaja: Optional[str] = 'N'
    laboral: Optional[Union[Empleado, NegocioPropio, Pensionado, OtroLaboral, Desempleado]] = None
    dependenciaEconomica: Literal["S", "N"] = "N"
    relacionCompa: Literal["excelente", "buena", "regular", "mala"]
    integracionUmet: Literal["S", "N"]
    relacionDocente: Literal["excelente", "buena", "regular", "mala"]
    relacionPadres: Literal["excelente", "buena", "regular", "mala"]
    relacionPareja: Optional[Literal["excelente", "buena", "regular", "mala"]] = None
    
    tipoCasa: Optional[str] = ""
    estadoFamiliar: Literal["cabezaHogar", "familia", "independiente"]
    cabezaHogar: Optional[str] = "N"
    origenRecursos: Optional[str] = "0"
    origenEstudios: Optional[str] = "0"
    miembros: Optional[List[MiembroFamiliar]] = None
    numeroHijos: Optional[int] = 0
    numeroFamiliar: Optional[str] = "0"
    ocupacionPadre: Optional[str] = ""
    ocupacionMadre: Optional[str] = ""
    sueldoPadre: Optional[str] = None
    sueldoMadre: Optional[str] = None
    tienePadres: Optional[str] = None
    personasTrabajan: Optional[int] = 0
    situacionLaboralPadre: Optional[str]= None
    situacionLaboralMadre: Optional[str]= None

    tieneDiscapacidad: Literal["S", "N"]
    discapacidad: Optional[Discapacidad] = None
    tieneEnfermedadCronica: Literal["S", "N"]
    enfermedadCronica: Optional[EnfermedadCronica] = None
    etnia: Optional[str] = None
    indigenaNacionalidad: Optional[int] = None

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
    
    @model_validator(mode="after")
    def set_dependencia_economica(cls, model):
        if model.situacionLaboral == "desempleado":
            model.dependenciaEconomica = "S"
            model.trabaja = 'N'
        elif model.dependenciaEconomica is None:
            model.dependenciaEconomica = "N"
            model.trabaja = 'S'
        return model
    
    @model_validator(mode="after")
    def set_cabeza_hogar(cls, model):
        if model.estadoFamiliar == "cabezaHogar":
            model.cabezaHogar = "S"
        elif model.estadoFamiliar == "familia":
            model.cabezaHogar = "N"
        return model
    
    @model_validator(mode="after")
    def calculos_miembros(self) -> "FichaSocioeconomicaSchema":
        self.numeroHijos = 0
        self.personasTrabajan = 0
        padre_presente = False
        madre_presente = False
        if self.miembros:
            self.numeroFamiliar = str(len(self.miembros))
            for m in self.miembros:
                if m.sueldo != "0":
                    self.personasTrabajan += 1
                if m.parentesco == "hijo":
                    self.numeroHijos += 1
                elif m.parentesco == "padre":
                    self.ocupacionPadre = m.ocupacion
                    self.sueldoPadre = m.sueldo
                    self.situacionLaboralPadre = "T" if m.sueldo != "0" else "NT"
                    padre_presente = True
                elif m.parentesco == "madre":
                    self.ocupacionMadre = m.ocupacion
                    self.sueldoMadre = m.sueldo
                    self.situacionLaboralMadre = "T" if m.sueldo != "0" else "NT"
                    madre_presente = True
        if padre_presente and madre_presente:
            self.tienePadres = "AMBOS"
        elif padre_presente:
            self.tienePadres = "PFA"
        elif madre_presente:
            self.tienePadres = "MFA"
        else:
            self.tienePadres = "OTRO"
        return self