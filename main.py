from fastapi import FastAPI, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from fichasocioeconomica import router as ficha_socioeconomica_router
from cliente import router as cliente_router
app = FastAPI()


# Permitir solicitudes desde tu dominio (ajusta esto según Cloudflare)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://alumno.umet.app", "http://localhost:3000"],
    allow_credentials=True, # Permite que las cookies se compartan entre dominios
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ficha_socioeconomica_router)
app.include_router(cliente_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

