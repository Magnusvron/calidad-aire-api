import requests
from datetime import datetime
from supabase import create_client
import os
import pytz

# Configuración
SUPABASE_URL = "https://ugszwjxitbzokzcnyhhe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnc3p3anhpdGJ6b2t6Y255aGhlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEwNzA5NjgsImV4cCI6MjA2NjY0Njk2OH0.wtW6Vy3n5vGJojKwcl3aXOqKW0DIcXzlYaNGc0H_hQo"
AQICN_TOKEN = "866a9b35170c510c9c82eeb3f158476e17a4c214"
AQICN_STATION = "A469795"

# Cliente Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def obtener_hora_queretaro():
    """Obtiene la hora actual en Querétaro, redondeada a la hora completa"""
    tz_queretaro = pytz.timezone('America/Mexico_City')
    hora_local = datetime.now(tz_queretaro)
    return hora_local.replace(minute=0, second=0, microsecond=0)

def formatear_hora_local(dt):
    """Formatea la hora sin información de zona horaria"""
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def obtener_datos_contaminacion():
    """Obtiene datos de contaminación de la API"""
    API_URL = f"https://api.waqi.info/feed/{AQICN_STATION}/?token={AQICN_TOKEN}"
    response = requests.get(API_URL)
    data = response.json()
    
    if data["status"] != "ok":
        raise ValueError(f"Error en API AQICN: {data.get('data', 'Sin detalles')}")
    
    hora_queretaro = obtener_hora_queretaro()
    hora_str = formatear_hora_local(hora_queretaro)
    print(f"\nHora local de actualización (Querétaro): {hora_str}")
    
    variable_map = {
        "co": "CO", "h": "HR", "no2": "NO2", "o3": "O3",
        "p": "PB", "pm25": "PM25", "so2": "SO2", "t": "Temp"
    }
    
    registros = []
    for var_aqicn, valor in data["data"]["iaqi"].items():
        if var_aqicn in variable_map:
            registros.append({
                "fecha_hora": formatear_hora_local(hora_queretaro),  # Almacena como string sin zona horaria
                "variable": variable_map[var_aqicn],
                "valor": valor["v"]
            })
    
    return registros

def actualizar_base_datos(registros):
    """Actualiza la base de datos y devuelve los registros actualizados"""
    if not registros:
        print("No hay registros para actualizar")
        return []
    
    try:
        # Realizar upsert
        response = supabase.table("calidad_aire").upsert(
            registros,
            on_conflict="fecha_hora,variable"
        ).execute()
        
        # Obtener los registros actualizados usando el formato local
        hora_actualizacion = registros[0]["fecha_hora"]
        registros_actualizados = supabase.table("calidad_aire")\
            .select("*")\
            .eq("fecha_hora", hora_actualizacion)\
            .execute()
        
        return registros_actualizados.data
    except Exception as e:
        print(f"Error al actualizar base de datos: {str(e)}")
        raise

def mostrar_registros_actualizados(registros):
    """Muestra los registros actualizados en formato legible"""
    if not registros:
        print("No se encontraron registros actualizados")
        return
    
    print("\nRegistros actualizados/insertados:")
    print("-" * 50)
    print(f"{'Variable':<10} | {'Valor':<10} | {'Fecha/Hora':<25}")
    print("-" * 50)
    for registro in registros:
        print(f"{registro['variable']:<10} | {registro['valor']:<10} | {registro['fecha_hora']:<25}")

if __name__ == "__main__":
    try:
        print("\nIniciando actualización de datos...")
        registros_a_actualizar = obtener_datos_contaminacion()
        print(f"Obtenidos {len(registros_a_actualizar)} mediciones")
        
        registros_actualizados = actualizar_base_datos(registros_a_actualizar)
        print("\nActualización completada exitosamente")
        
        mostrar_registros_actualizados(registros_actualizados)
        
    except Exception as e:
        print(f"\nError durante la ejecución: {str(e)}")
        raise
