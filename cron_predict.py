import os
import joblib
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from supabase import create_client
import tensorflow as tf

# ───────────────── Credenciales Supabase ─────────────────
SUPABASE_URL = "https://ugszwjxitbzokzcnyhhe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVnc3p3anhpdGJ6b2t6Y255aGhlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEwNzA5NjgsImV4cCI6MjA2NjY0Njk2OH0.wtW6Vy3n5vGJojKwcl3aXOqKW0DIcXzlYaNGc0H_hQo"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


MODELS_DIR = './models'
with open(os.path.join(MODELS_DIR, 'features_dict.json')) as f:
    features_dict = json.load(f)
scaler = joblib.load(os.path.join(MODELS_DIR, 'scaler_calidad_aire.save'))

TARGET = 'pm25'
LAG = 24
features = features_dict[TARGET]
model_path = os.path.join(MODELS_DIR, 'modelo_lstm_pm25.keras')
model = tf.keras.models.load_model(model_path)

# 1. Traer los últimos LAG datos reales
response = supabase.table("historic_aire")\
    .select(','.join(['fecha_hora'] + features))\
    .order('fecha_hora', desc=True).limit(LAG).execute()
df = pd.DataFrame(response.data).sort_values('fecha_hora')

# 2. Preparar el input inicial
input_hist = df[features].astype(float).values[-LAG:]
X_scaled = scaler.transform(input_hist)
window = X_scaled.copy()

fecha_inicio = pd.to_datetime(df['fecha_hora'].iloc[-1])

# --- FUNCION AJUSTE HISTÓRICO ---
def consulta_historico_supabase(variable, fecha_objetivo):
    # Consulta promedio histórico para esa hora/día (puedes afinar a tu gusto)
    # Aquí uso datos de años previos, misma hora y mes
    hora = fecha_objetivo.hour
    mes = fecha_objetivo.month
    # Traer todos los valores previos de esa variable en esa hora y mes
    res = supabase.table("historic_aire")\
        .select('fecha_hora,'+variable)\
        .filter('extract(hour from fecha_hora)', 'eq', hora)\
        .filter('extract(month from fecha_hora)', 'eq', mes)\
        .not_('fecha_hora','eq',fecha_objetivo.strftime('%Y-%m-%d %H:%M:%S'))\
        .execute()
    df_hist = pd.DataFrame(res.data)
    if not df_hist.empty:
        return float(df_hist[variable].mean())
    else:
        return 0  # fallback: puedes usar el promedio general si lo deseas

# 3. Predecir recursivamente 24h al futuro
for paso in range(1, 25):
    # Preparar input para el modelo
    X_input = window[-LAG:].reshape(1, LAG, len(features))
    pred_scaled = model.predict(X_input)[0][0]

    # Invertir el escalado para el target
    # Prepara una fila "falsa" para desescalar solo el target
    fila = np.zeros((1, len(features)))
    idx_target = features.index(TARGET)
    fila[0, idx_target] = pred_scaled
    pred_real = scaler.inverse_transform(fila)[0, idx_target]

    # Ajuste con histórico
    fecha_pred = fecha_inicio + timedelta(hours=paso)
    valor_historico = consulta_historico_supabase(TARGET, fecha_pred)
    pred_final = (pred_real + valor_historico) / 2

    # Guardar en prediction
    row = {
        'fecha_hora': fecha_pred.strftime('%Y-%m-%d %H:%M:%S'),
        'variable': TARGET,
        'valor': pred_final
    }
    supabase.table('prediction').upsert([row]).execute()
    print(f"Guardado: {row}")

    # Actualizar la ventana (recursiva)
    new_row = window[-1].copy()
    new_row[idx_target] = pred_scaled  # Solo cambiamos el target, el resto de features permanecen
    window = np.vstack([window, new_row])

