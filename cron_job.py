import requests
import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AQICN_TOKEN = os.getenv("AQICN_TOKEN")
STATION_ID = os.getenv("AQICN_STATION")  # ejemplo: A469795

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

API_URL = f"https://api.waqi.info/feed/{STATION_ID}/?token={AQICN_TOKEN}"

response = requests.get(API_URL)
data = response.json()

if data["status"] == "ok":
    registros = []

    # Redondear la hora hacia abajo a la hora cerrada
    fecha_original = datetime.fromisoformat(data["data"]["time"]["iso"].replace("Z", "+00:00"))
    fecha_hora = fecha_original.replace(minute=0, second=0, microsecond=0).isoformat()

    iaqi = data["data"]["iaqi"]
    for variable, valor in iaqi.items():
        registro = {
            "fecha_hora": fecha_hora,
            "variable": variable.upper(),
            "valor": valor["v"]
        }
        registros.append(registro)

    # Imprimir registros
    print("Registros a insertar o actualizar:")
    for r in registros:
        print(r)

    # Upsert
    for registro in registros:
        supabase.table("calidad-aire").upsert(
            registro,
            on_conflict=["fecha_hora", "variable"]
        ).execute()

    print(f"{len(registros)} registros procesados para {fecha_hora}.")

else:
    print("Error al obtener datos de AQICN:", data)
