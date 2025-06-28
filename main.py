from fastapi import FastAPI
from scraper import upsert_datos
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()
app = FastAPI()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
def root():
    return {"message": "API calidad aire"}

from fastapi.responses import JSONResponse

@app.get("/api/datos")
def get_datos(variable: str, desde: str, hasta: str):
    try:
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        data = supabase.table("calidad-aire").select("*")\
            .eq("variable", variable)\
            .gte("fecha_hora", desde)\
            .lte("fecha_hora", hasta).execute()
        return data.data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/debug")
def debug():
    try:
        supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
        data = supabase.table("calidad-aire").select("*").limit(5).execute()
        return data.data
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

