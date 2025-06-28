# cron_job.py

import requests
import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener credenciales y parámetros desde el entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AQICN_TOKEN = os.getenv("AQICN_TOKEN")  # Token válido de AQICN
STATION_ID = os.getenv("AQICN_STATION")  # Debe ser numérico, ej. "469795"

# Crear cliente de Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Construir URL de la API (IMPORTANTE: el '@' antes del ID)
API_URL = f"https://api.waqi.info/feed/@{STATION_ID}/?token={AQICN_TOKEN}"
print("Consultando:", API_URL)  # Útil para debug en GitHub Actions

# Obtener datos
response = requests.get(API_URL)
data = response.json()
print("Respuesta API:", data)

if data["status"] == "ok":
    registros = []
    fecha_hora = data["data"]["time"]["iso"]
    iaqi = data["data"].get("iaqi", {})

    for variable, valor in iaqi.items():
        registros.append({
            "fecha_hora": fecha_hora,
            "variable": variable.upper(),
            "valor": valor["v"]
        })

    # Insertar en Supabase (UPSERT por clave compuesta)
    for registro in registros:
        supabase.table("calidad-aire").upsert(registro, on_conflict=["fecha_hora", "variable"]).execute()

    print(f"{len(registros)} registros procesados para {fecha_hora}.")
else:
    print("❌ Error al obtener datos de AQICN:", data)
