import os
from dotenv import load_dotenv
import requests

load_dotenv()

# Leer variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
AQICN_TOKEN = os.getenv("AQICN_TOKEN")
STATION_ID = os.getenv("AQICN_STATION")

# Imprimir variables para depuración
print("SUPABASE_URL:", SUPABASE_URL)
print("SUPABASE_KEY:", SUPABASE_KEY[:6] + "..." if SUPABASE_KEY else "None")  # Mostrar solo inicio
print("AQICN_TOKEN:", AQICN_TOKEN[:6] + "..." if AQICN_TOKEN else "None")
print("AQICN_STATION:", STATION_ID)

# Construir URL de consulta a AQICN
API_URL = f"https://api.waqi.info/feed/{STATION_ID}/?token={AQICN_TOKEN}"
print("URL construida para AQICN:", API_URL)

# Realizar la petición y mostrar resultado
try:
    response = requests.get(API_URL)
    data = response.json()
    print("Respuesta JSON de AQICN:")
    print(data)
except Exception as e:
    print("Error al hacer la petición:")
    print(e)
