import os
import requests
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables del entorno
load_dotenv()

# Leer credenciales y parámetros de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


# Verificaciones básicas
if not all([SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("⚠️ Faltan variables de entorno. Revisa tu archivo .env o secretos de GitHub.")

# Crear cliente de Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Construir URL de la API de AQICN

API_URL = https://api.waqi.info/feed/A469795/?token=866a9b35170c510c9c82eeb3f158476e17a4c214
response = requests.get(API_URL)
data = response.json()

# Procesar respuesta
if data["status"] == "ok":
    registros = []
    fecha_hora = data["data"]["time"]["iso"]
    iaqi = data["data"].get("iaqi", {})

    for variable, valor in iaqi.items():
        registros.append({
            "fecha_hora": fecha_hora,
            "variable": variable.upper(),
            "valor": valor.get("v")
        })

    for registro in registros:
        supabase.table("calidad-aire").upsert(
            registro,
            on_conflict=["fecha_hora", "variable"]
        ).execute()

    print(f"✅ {len(registros)} registros procesados para {fecha_hora} en estación {STATION_ID}.")
else:
    print("❌ Error al obtener datos de AQICN:", data)
    exit(1)
