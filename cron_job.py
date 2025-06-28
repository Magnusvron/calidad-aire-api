import requests
import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Cargar variables de entorno (funciona local y en GitHub Actions)
load_dotenv()

# === Variables de entorno requeridas ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AQICN_TOKEN = os.getenv("AQICN_TOKEN")
STATION_ID = os.getenv("AQICN_STATION")  # Ej: "A469795"

# Validación
if not all([SUPABASE_URL, SUPABASE_KEY, AQICN_TOKEN, STATION_ID]):
    raise EnvironmentError("Faltan variables de entorno necesarias")

# Inicializar cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Construir URL AQICN
API_URL = f"https://api.waqi.info/feed/{STATION_ID}/?token={AQICN_TOKEN}"
response = requests.get(API_URL)
data = response.json()

# === Verificación de respuesta ===
if data["status"] == "ok":
    registros = []

    # Redondear a hora exacta (hora cerrada)
    fecha_original = datetime.fromisoformat(data["data"]["time"]["iso"].replace("Z", "+00:00"))
    fecha_hora = fecha_original.replace(minute=0, second=0, microsecond=0).isoformat()

    # Mapeo de variables AQICN → Base de datos
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

    # Construcción de registros
    for var_aqicn, valor in data["data"]["iaqi"].items():
        if var_aqicn in variable_map:
            registros.append({
                "fecha_hora": fecha_hora,
                "variable": variable_map[var_aqicn],
                "valor": valor["v"]
            })

    # Depuración
    print("Registros a insertar o actualizar:")
    for r in registros:
        print(r)

    # Inserción o actualización (upsert)
    for registro in registros:
        supabase.table("calidad-aire").upsert(
            registro,
            on_conflict=["fecha_hora", "variable"]
        ).execute()

    print(f"{len(registros)} registros procesados para {fecha_hora}.")
else:
    print("Error al obtener datos de AQICN:", data)
