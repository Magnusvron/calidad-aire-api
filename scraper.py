import httpx
import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AQICN_TOKEN = os.getenv("AQICN_TOKEN")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_aqicn_data():
    url = f"https://api.waqi.info/feed/@469795/?token={AQICN_TOKEN}"
    r = httpx.get(url).json()
    if r["status"] != "ok":
        return []
    
    fecha = r["data"]["time"]["iso"]
    iaqi = r["data"]["iaqi"]

    mapeo = {
        "co": "CO", "no2": "NO2", "o3": "O3", "so2": "SO2",
        "pm25": "PM25", "t": "Temp", "h": "HR", "p": "PB"
    }

    registros = []
    for clave, variable in mapeo.items():
        if clave in iaqi:
            registros.append({
                "fecha_hora": fecha,
                "variable": variable,
                "valor": iaqi[clave]["v"],
                "fuente": "tiempo_real"
            })
    return registros

def upsert_datos():
    datos = fetch_aqicn_data()
    for d in datos:
        supabase.table("calidad-aire").upsert(d).execute()
