import requests
from datetime import datetime
from supabase import create_client

# ==== Variables explícitas ====
SUPABASE_URL = "https://ugszwjxitbzokzcnyhhe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnc3p3anhpdGJ6b2t6Y255aGhlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEwNzA5NjgsImV4cCI6MjA2NjY0Njk2OH0.wtW6Vy3n5vGJojKwcl3aXOqKW0DIcXzlYaNGc0H_hQo"  # reemplaza con tu clave real
AQICN_TOKEN = "866a9b35170c510c9c82eeb3f158476e17a4c214"  # token de AQICN
STATION_ID = "A499747"  # estación deseada

print(f"Conectando a SUPABASE_URL: {SUPABASE_URL}")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Solicitud AQICN ===
API_URL = f"https://api.waqi.info/feed/{STATION_ID}/?token={AQICN_TOKEN}"
response = requests.get(API_URL)
data = response.json()

if data["status"] == "ok":
    registros = []

    fecha_original = datetime.fromisoformat(data["data"]["time"]["iso"].replace("Z", "+00:00"))
    fecha_hora = fecha_original.replace(minute=0, second=0, microsecond=0).isoformat()

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

    for var_aqicn, valor in data["data"]["iaqi"].items():
        if var_aqicn in variable_map:
            registros.append({
                "fecha_hora": fecha_hora,
                "variable": variable_map[var_aqicn],
                "valor": valor["v"]
            })

    print("Registros a insertar o actualizar:")
    for r in registros:
        print(r)

    # ✅ Inserción masiva
    supabase.table("calidad-aire").upsert(
        registros,
        on_conflict=["fecha_hora", "variable"]
    ).execute()

    print(f"{len(registros)} registros procesados para {fecha_hora}.")
else:
    print("Error al obtener datos de AQICN:", data)
