# cron_job.py
import requests
import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AQICN_TOKEN = os.getenv("AQICN_TOKEN")  # lo debes definir en tu .env
STATION_ID = os.getenv("AQICN_STATION")  # ejemplo: "A499747"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

API_URL = f"https://api.waqi.info/feed/{STATION_ID}/?token={AQICN_TOKEN}"

response = requests.get(API_URL)
data = response.json()

if data["status"] == "ok":
    registros = []
    fecha_hora = data["data"]["time"]["iso"]
    iaqi = data["data"]["iaqi"]

    for variable, valor in iaqi.items():
        registros.append({
            "fecha_hora": fecha_hora,
            "variable": variable.upper(),
            "valor": valor["v"]
        })

    # UPSERT por clave compuesta (fecha_hora + variable)
    for registro in registros:
        supabase.table("calidad-aire").upsert(registro, on_conflict=["fecha_hora", "variable"]).execute()

    print("Datos insertados correctamente.")
else:
    print("Error al obtener datos de AQICN:", data)
    print(data)  # para ver el mensaje completo de error
    
print(f"{len(registros)} registros procesados para {fecha_hora}.")

