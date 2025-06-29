# cron_predict.py  – Railway Job independiente
import os, json, joblib, datetime as dt
import pandas as pd
import numpy as np
import tensorflow as tf
from supabase import create_client

# ───────────────── Credenciales Supabase ─────────────────
SUPABASE_URL = "https://ugszwjxitbzokzcnyhhe.supabase.co"
SUPABASE_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnc3p3anhpdGJ6b2t6Y255aGhlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEwNzA5NjgsImV4cCI6MjA2NjY0Njk2OH0."
    "wtW6Vy3n5vGJojKwcl3aXOqKW0DIcXzlYaNGc0H_hQo"
)
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ───────────────── Cargar artefactos ─────────────────────
scaler   = joblib.load("scaler_calidad_aire.save")
feat_dic = json.load(open("features_dict.json"))
models   = {
    var: tf.keras.models.load_model(
        f"modelo_{'lstm' if var!='no2' else 'nn'}_{var}.keras"
    )
    for var in feat_dic.keys()
}

# ───────────────── Obtener ventana de 24 h ───────────────
now_utc = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
start   = now_utc - dt.timedelta(hours=24)

raw = (
    supabase.table("calidad_aire")
    .select("*")
    .gte("fecha_hora", start.isoformat())
    .lt("fecha_hora",  now_utc.isoformat())
    .order("fecha_hora")
    .execute()
)
df = pd.DataFrame(raw.data)
if len(df) < 24:
    raise RuntimeError("No se obtuvieron 24 filas completas; se aborta la predicción.")

# ───────────────── Reconstruir rezagos ───────────────────
for col in feat_dic.keys():
    for c in feat_dic[col]:
        if "_lag" in c:
            lag = int(c.split("lag")[-1])
            df[c] = df[col].shift(lag)
df = df.tail(24)   # nos aseguramos de tener exactamente 24 filas alineadas

# ───────────────── Realizar predicciones ─────────────────
predicciones = []
for var, features in feat_dic.items():
    X = df[features].copy()
    if var != "no2":                     # Modelos LSTM (secuencia 24×N)
        Xs = scaler.transform(X)         # (24, N)
        Xs = Xs.reshape(1, 24, -1)
    else:                                # Modelo NN (vector único)
        Xs = scaler.transform(X.tail(1)) # (1, N)

    valor = float(models[var].predict(Xs, verbose=0)[0, 0])
    predicciones.append({"fecha_hora": now_utc.isoformat(),
                         "variable":   var,
                         "valor":      valor})

# ───────────────── Guardar en tabla prediction ───────────
supabase.table("prediction").insert(predicciones).execute()
print("Predicciones registradas:\n", predicciones)
