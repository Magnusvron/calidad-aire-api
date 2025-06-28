from fastapi import FastAPI
from scraper import upsert_datos
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
def root():
    return {"message": "API calidad aire"}

@app.get("/api/datos")
def get_datos(variable: str, desde: str, hasta: str):
    data = supabase.table("calidad_aire").select("*")\
        .eq("variable", variable)\
        .gte("fecha_hora", desde)\
        .lte("fecha_hora", hasta).execute()
    return data.data
