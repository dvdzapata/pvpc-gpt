import json
import logging
import os
import sys
import requests
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import uvicorn

# -------------------------
# CONFIGURACIÓN Y LOGGING
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("pvpc-server")

# Leer token desde variable de entorno
ESIOS_TOKEN = os.getenv("ESIOS_TOKEN", "d6467eb25b2fa5e8226442a58b308d4cf3c54b23600ed70bcde4873e88066da6")
PORT = int(os.getenv("PORT", 8080))

if ESIOS_TOKEN == "d6467eb25b2fa5e8226442a58b308d4cf3c54b23600ed70bcde4873e88066da6":
    logger.warning("⚠️  Usando token por defecto. Configura ESIOS_TOKEN en variables de entorno.")

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "x-api-key": ESIOS_TOKEN
}

# Crear aplicación FastAPI
app = FastAPI(
    title="PVPC API",
    description="API para consultar precios PVPC de electricidad en España",
    version="1.0.0"
)

logger.info("🚀 Servidor PVPC API inicializado")

# -------------------------
# SEMÁFORO PVPC (€/kWh)
# -------------------------
def pvpc_semaforo(precio_kwh: float) -> str:
    if precio_kwh < 0.10:
        return "🟢 verde"
    elif precio_kwh < 0.15:
        return "🟡 amarillo"
    elif precio_kwh < 0.20:
        return "🟠 naranja"
    elif precio_kwh < 0.25:
        return "🔴 rojo"
    else:
        return "🟣 púrpura"

# -------------------------
# PETICIÓN A ESIOS CON RETRY
# -------------------------
def pedir_1001(fecha, max_reintentos=3):
    fecha_inicio = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_fin = fecha_inicio + timedelta(days=1)

    params = {
        "time_trunc": "hour",
        "start_date": fecha_inicio.isoformat(),
        "end_date": fecha_fin.isoformat()
    }

    url = "https://api.esios.ree.es/indicators/1001"
    
    for intento in range(1, max_reintentos + 1):
        try:
            logger.info(f"📡 Petición a ESIOS API (intento {intento}/{max_reintentos}): {fecha_inicio.date()}")
            r = requests.get(url, headers=HEADERS, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            logger.info(f"✅ Datos recibidos: {len(data['indicator']['values'])} valores")
            return data["indicator"]["values"]
        
        except requests.exceptions.Timeout:
            logger.error(f"⏱️  Timeout en intento {intento}/{max_reintentos}")
            if intento == max_reintentos:
                raise
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Error HTTP {r.status_code}: {e}")
            raise
        
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            if intento == max_reintentos:
                raise

# -------------------------
# PROCESAR VALORES
# -------------------------
def procesar(lista):
    salida = []
    for item in lista:
        precio_mwh = item["value"]
        precio_kwh = precio_mwh / 1000
        salida.append({
            "datetime": item["datetime"],
            "geo_id": item["geo_id"],
            "geo_name": item["geo_name"],
            "precio_mwh": round(precio_mwh, 2),
            "precio_kwh": round(precio_kwh, 4),
            "semaforo": pvpc_semaforo(precio_kwh)
        })
    logger.info(f"📊 Procesados {len(salida)} registros de precios")
    return salida

# -------------------------
# ENDPOINTS
# -------------------------

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "name": "PVPC API",
        "version": "1.0.0",
        "endpoints": {
            "/hoy": "Precios PVPC de hoy",
            "/manana": "Precios PVPC de mañana (disponible desde las 20:00)",
            "/health": "Health check"
        }
    }

@app.get("/health")
async def health():
    """Health check para Fly.io"""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/hoy")
async def pvpc_hoy():
    """Obtiene los precios PVPC para hoy"""
    try:
        logger.info("🔧 Endpoint llamado: /hoy")
        ahora = datetime.now(timezone.utc)
        valores = pedir_1001(ahora)
        resultado = procesar(valores)
        return JSONResponse(content=resultado)
    except Exception as e:
        logger.error(f"💥 Error en /hoy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/manana")
async def pvpc_manana():
    """Obtiene los precios PVPC para mañana (disponible después de las 20:00)"""
    try:
        logger.info("🔧 Endpoint llamado: /manana")
        hora_local = datetime.now()
        
        if hora_local.hour < 20:
            logger.warning(f"⏰ Datos de mañana solicitados a las {hora_local.hour}:00 (disponible desde las 20:00)")
            raise HTTPException(
                status_code=425,
                detail={
                    "error": "Datos de mañana no disponibles hasta las 20:00",
                    "hora_actual": hora_local.strftime("%H:%M")
                }
            )

        manana = datetime.now(timezone.utc) + timedelta(days=1)
        valores = pedir_1001(manana)
        resultado = procesar(valores)
        return JSONResponse(content=resultado)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"💥 Error en /manana: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/.well-known/openai-apps-challenge")
async def openai_challenge():
    """Sirve el archivo de verificación de OpenAI Apps"""
    file_path = ".well-known/openai-apps-challenge"
    if os.path.exists(file_path):
        logger.info("✅ Sirviendo archivo de verificación OpenAI")
        return FileResponse(file_path, media_type="text/plain")
    else:
        logger.error("❌ Archivo de verificación no encontrado")
        raise HTTPException(status_code=404, detail="Verification file not found")

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    logger.info(f"🌐 Iniciando servidor FastAPI en puerto {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
