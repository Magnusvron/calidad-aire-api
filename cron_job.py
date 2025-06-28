import os

# Leer variables del entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AQICN_TOKEN = os.getenv("AQICN_TOKEN")
AQICN_STATION = os.getenv("AQICN_STATION")
# Limpieza de variables
SUPABASE_URL = SUPABASE_URL.strip()
SUPABASE_KEY = SUPABASE_KEY.strip()
AQICN_TOKEN = AQICN_TOKEN.strip()
AQICN_STATION = AQICN_STATION.strip()

# Imprimir valores crudos para depurar
print("=== VARIABLES DE ENTORNO LEÍDAS ===")
print("SUPABASE_URL:", repr(SUPABASE_URL))
print("SUPABASE_KEY:", repr(SUPABASE_KEY))
print("AQICN_TOKEN:", repr(AQICN_TOKEN))
print("AQICN_STATION:", repr(AQICN_STATION))

# Construir URL completa
api_url = f"https://api.waqi.info/feed/{AQICN_STATION}/?token={AQICN_TOKEN}"
print("\nURL construida para AQICN:", api_url)

# Probar acceso a la API
import requests
try:
    response = requests.get(api_url)
    print("\nRespuesta JSON de AQICN:")
    print(response.json())
except Exception as e:
    print("❌ Error al intentar conectarse a la API:", e)
