import requests
from datetime import datetime, timezone
from supabase import create_client
import os

SUPABASE_URL="https://ugszwjxitbzokzcnyhhe.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnc3p3anhpdGJ6b2t6Y255aGhlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEwNzA5NjgsImV4cCI6MjA2NjY0Njk2OH0.wtW6Vy3n5vGJojKwcl3aXOqKW0DIcXzlYaNGc0H_hQo"
AQICN_TOKEN="866a9b35170c510c9c82eeb3f158476e17a4c214"
AQICN_STATION="A469795"

# Validación de config
if not all([SUPABASE_URL, SUPABASE_KEY, AQICN_TOKEN]):
    raise ValueError("Faltan variables de entorno requeridas")

# Cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def obtener_datos_contaminacion():
    """Obtiene datos de la API AQICN y los formatea"""
    API_URL = f"https://api.waqi.info/feed/{AQICN_STATION}/?token={AQICN_TOKEN}"
    response = requests.get(API_URL)
    data = response.json()
    
    if data["status"] != "ok":
        raise ValueError(f"Error en API AQICN: {data.get('data', 'Sin detalles')}")
    
    # Procesamiento de fecha (redondeo a hora completa)
    fecha_original = datetime.fromisoformat(data["data"]["time"]["iso"].replace("Z", "+00:00"))
    fecha_hora = fecha_original.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    
    # Mapeo de variables
    variable_map = {
        "co": "CO",
        "h": "HR",
        "no2": "NO2",
        "o3": "O3",
        "p": "PB",
        "pm25": "PM25",
        "so2": "SO2",
        "t": "Temp"
    }
    
    registros = []
    for var_aqicn, valor in data["data"]["iaqi"].items():
        if var_aqicn in variable_map:
            registros.append({
                "fecha_hora": fecha_hora.isoformat(),
                "variable": variable_map[var_aqicn],
                "valor": valor["v"]
            })
    
    return registros

def actualizar_base_datos(registros):
    """Realiza upsert de los registros en Supabase"""
    if not registros:
        print("No hay registros para actualizar")
        return
    
    # Upsert con el formato que sabemos que funciona
    response = supabase.table("calidad_aire").upsert(
        registros,
        on_conflict="fecha_hora,variable"
    ).execute()
    
    return response.data

if __name__ == "__main__":
    try:
        print("Iniciando actualización de datos...")
        registros = obtener_datos_contaminacion()
        print(f"Obtenidos {len(registros)} registros")
        
        resultado = actualizar_base_datos(registros)
        print("Actualización completada:", resultado)
        
    except Exception as e:
        print(f"Error en la ejecución: {str(e)}")
        raise  # Para que falle el workflow
