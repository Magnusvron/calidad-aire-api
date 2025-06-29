from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from tensorflow.keras.models import load_model
import numpy as np
from schemas import PredictionRequest, ModelConfig, Contaminante
from supabase import create_client
import os
from typing import Dict

# Configuración inicial
app = FastAPI(
    title="API de Predicción de Contaminantes",
    description="Predice niveles de contaminantes usando modelos LSTM/Keras",
    version="1.0.0"
)

# CORS (Ajustar en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a Supabase
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Carga de modelos al iniciar
MODELS = {
    cont: load_model(path) 
    for cont, path in ModelConfig.MODEL_PATHS.items()
}

@app.on_event("startup")
async def startup_event():
    """Verificar que todos los modelos se cargaron correctamente"""
    for cont, model in MODELS.items():
        if model is None:
            raise RuntimeError(f"Error al cargar modelo para {cont}")

# Endpoints
@app.post("/predict", summary="Predicción con datos proporcionados")
async def predict(request: PredictionRequest):
    """
    Realiza predicciones para un contaminante específico.
    
    Requiere:
    - contaminante: uno de ['co', 'o3', 'so2', ...]
    - datos: diccionario con las variables requeridas (ver /features/{contaminante})
    """
    try:
        # Validación adicional
        ModelConfig.validate_contaminante(request.contaminante)
        
        required_vars = ModelConfig.FEATURES[request.contaminante]
        missing_vars = [var for var in required_vars if var not in request.datos]
        
        if missing_vars:
            raise HTTPException(
                status_code=400,
                detail=f"Faltan variables requeridas: {missing_vars}"
            )
        
        # Preparar input en orden correcto
        input_array = np.array([[request.datos[var] for var in required_vars]])
        
        # Predecir
        prediction = MODELS[request.contaminante].predict(input_array)
        
        return {
            "contaminante": request.contaminante,
            "prediccion": prediction.flatten().tolist(),
            "unidades": "µg/m³",
            "variables_utilizadas": required_vars
        }
        
    except Exception as e:
        raise HTTPException(500, f"Error en predicción: {str(e)}")

@app.get("/features/{contaminante}", summary="Obtener variables requeridas")
async def get_required_features(contaminante: Contaminante):
    """Devuelve la lista de variables necesarias para un contaminante"""
    return {
        "contaminante": contaminante,
        "variables_requeridas": ModelConfig.FEATURES[contaminante]
    }

@app.get("/predict_from_db", summary="Predicción con últimos datos de Supabase")
async def predict_from_db(contaminante: Contaminante):
    """
    Obtiene automáticamente los últimos datos de Supabase y genera predicción.
    
    Nota: Solo usa datos disponibles (puede fallar si faltan variables)
    """
    try:
        # Obtener últimos datos
        data = supabase.table("mediciones") \
                 .select("*") \
                 .order("fecha", desc=True) \
                 .limit(1) \
                 .execute().data[0]
        
        # Filtrar variables requeridas
        required_vars = ModelConfig.FEATURES[contaminante]
        input_data = {k: v for k, v in data.items() if k in required_vars}
        
        # Validar datos completos
        if len(input_data) != len(required_vars):
            missing = set(required_vars) - set(input_data.keys())
            raise HTTPException(
                400,
                detail=f"Datos incompletos en Supabase. Faltan: {missing}"
            )
        
        # Usar endpoint principal
        return await predict(PredictionRequest(
            contaminante=contaminante,
            datos=input_data
        ))
        
    except Exception as e:
        raise HTTPException(500, f"Error al predecir desde Supabase: {str(e)}")

# Health Check
@app.get("/health")
async def health_check():
    return {"status": "ok", "loaded_models": list(MODELS.keys())}
