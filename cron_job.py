import requests
import os
from datetime import datetime, timezone, timedelta
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AQICN_TOKEN = os.getenv("AQICN_TOKEN")
STATION_ID = os.getenv("AQICN_STATION")  # ejemplo: A469795

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Construir URL de API
API_URL = f"https://api.waqi.info/feed/{STATION_ID}/?token={AQICN_TOKEN}"

# Obtener datos
response = requests.get(API_URL)
data = response.json()

if data["status"] == "ok":
    registros = []

    # Extraer y redondear hora
    fecha_original = data["data"]["time"]["iso"]
    dt = datetime.fromisoformat(fecha_original.replace("Z", "+00:00")).astimezone(timezone.utc)
    dt_redondeada = dt.replace(minute=0, second=0, microsecond=0)  # Redondear hacia abajo a hora cerrada

    # Verificar si corresponde a hoy o futuro
    if dt_redondeada.date() < datetime.now(timezone.utc).date():
        print("Dato muy antiguo, ignorado:", dt_redondeada.isoformat())
    else:
        iaqi = data["data"]["iaqi"]

        for variable, valor in iaqi.items():
            registros.append({
                "fecha_hora": dt_redondeada.isoformat(),
                "variable": variable.upper(),
                "valor": valor["v"]
            })

        for registro in registros:
            supabase.table("calidad-aire").upsert(
                registro,
                on_conflict=["fecha_hora", "variable"]
            ).execute()

        print(f"{len(registros)} registros insertados/reemplazados para {dt_redondeada.isoformat()}.")

else:
    print("Error al obtener datos de AQICN:", data)
