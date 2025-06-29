from pydantic import BaseModel
from typing import Dict, Literal
import json

# Definición de tipos de contaminantes
Contaminante = Literal[
    "co", "o3", "so2", "pm25", "tmp", "pb", "hr", "no2"
]

class PredictionRequest(BaseModel):
    """Esquema para solicitudes de predicción"""
    contaminante: Contaminante
    datos: Dict[str, float]

class ModelConfig:
    """Configuración centralizada de modelos y features"""
    
    # Cargar features desde JSON
    with open('models/features_dict.json', 'r', encoding='utf-8') as f:
        FEATURES = json.load(f)
    
    # Mapeo de modelos
    MODEL_PATHS = {
        "co": "models/modelo_lstm_co.keras",
        "o3": "models/modelo_lstm_o3.keras",
        "so2": "models/modelo_lstm_so2.keras",
        "pm25": "models/modelo_lstm_pm25.keras",
        "tmp": "models/modelo_lstm_tmp.keras",
        "pb": "models/modelo_lstm_ph.keras",  
        "hr": "models/modelo_lstm_hr.keras",
        "no2": "models/modelo_nn_no2.keras"
    }

    @classmethod
    def validate_contaminante(cls, value: str) -> str:
        """Validar que el contaminante exista"""
        if value not in cls.MODEL_PATHS:
            raise ValueError(f"Contaminante no válido. Opciones: {list(cls.MODEL_PATHS.keys())}")
        return value
