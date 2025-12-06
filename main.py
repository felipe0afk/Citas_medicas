from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse 

# Importamos las funciones del módulo de conexión a Oracle
from database import crear_cita, obtener_citas, actualizar_cita, eliminar_cita 

# --- Modelos de Datos (Schema Pydantic) ---

class CitaBase(BaseModel):
    # Usamos datetime para validar la entrada de fecha/hora del formulario
    fecha_cita: datetime 
    paciente_nombre: str
    motivo: str

class Cita(CitaBase):
    # Mapeo de campos de la base de datos (que están en MAYÚSCULAS) a Pydantic
    cita_id: int = Field(alias="CITA_ID")
    paciente_nombre: str = Field(alias="PACIENTE_NOMBRE")
    # La fecha la devolvemos como string después de leerla de Oracle
    fecha_cita: str = Field(alias="FECHA_CITA") 
    motivo: str = Field(alias="MOTIVO")
    estado: str = Field(alias="ESTADO", default="Programada")

    class Config:
        # Configuración necesaria para Pydantic V2 para leer atributos de los modelos de la DB
        validate_by_name = True
        from_attributes = True

class CitaEstadoUpdate(BaseModel):
    estado: str 

# --- Definición de la Aplicación (API Endpoints) ---
app = FastAPI(title="API CRUD de Citas Médicas con Oracle")

API_PREFIX = "/api"

# Montamos la carpeta 'static' para servir CSS y JS
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_app():
    # Enrutamiento principal que sirve la interfaz de usuario
    return FileResponse('index.html')

@app.post(f"{API_PREFIX}/citas/", response_model=Cita)
def crear_nueva_cita(cita: CitaBase):
    # Formateamos la fecha para que Oracle la pueda insertar correctamente
    fecha_str = cita.fecha_cita.strftime('%Y-%m-%d %H:%M:%S')
    
    new_id = crear_cita(
        paciente=cita.paciente_nombre, 
        fecha=fecha_str, 
        motivo=cita.motivo
    )
    
    if new_id is None:
        raise HTTPException(status_code=500, detail="Error al crear la cita en la base de datos.")
    
    # Creamos el objeto de respuesta usando el ID retornado por Oracle
    cita_data = {
        "CITA_ID": new_id, 
        "PACIENTE_NOMBRE": cita.paciente_nombre, 
        "FECHA_CITA": fecha_str, 
        "MOTIVO": cita.motivo, 
        "ESTADO": "Programada"
    }
    
    return Cita.model_validate(cita_data)

@app.get(f"{API_PREFIX}/citas/", response_model=List[Cita])
def listar_citas():
    # Lógica de la operación READ: obtiene todas las citas
    citas_db = obtener_citas()
    if citas_db is None:
        return []
    return citas_db

@app.put(f"{API_PREFIX}/citas/{{cita_id}}")
def actualizar_estado(cita_id: int, update: CitaEstadoUpdate):
    # Lógica de la operación UPDATE: cambiar el estado de la cita
    if actualizar_cita(cita_id, update.estado):
        return {"message": f"Cita {cita_id} actualizada a estado: {update.estado}"}
    
    raise HTTPException(status_code=404, detail=f"Cita con ID {cita_id} no encontrada o error.")

@app.delete(f"{API_PREFIX}/citas/{{cita_id}}")
def borrar_cita(cita_id: int):
    # Lógica de la operación DELETE: eliminar la cita por ID
    if eliminar_cita(cita_id):
        return {"message": f"Cita {cita_id} eliminada correctamente."}
        
    raise HTTPException(status_code=404, detail=f"Cita con ID {cita_id} no encontrada o error.")