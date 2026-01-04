import json
import logging
import os
import sys
import requests
from datetime import datetime, timedelta, timezone
from mcp.server import Server

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

server = Server("pvpc")
logger.info("🚀 Servidor PVPC MCP inicializado")

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
# TOOL: HOY
# -------------------------
@server.tool()
def pvpc_hoy() -> str:
    """Obtiene los precios PVPC para hoy"""
    try:
        logger.info("🔧 Tool llamado: pvpc_hoy")
        ahora = datetime.now(timezone.utc)
        valores = pedir_1001(ahora)
        resultado = procesar(valores)
        return json.dumps(resultado, ensure_ascii=False)
    except Exception as e:
        logger.error(f"💥 Error en pvpc_hoy: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# -------------------------
# TOOL: MAÑANA
# -------------------------
@server.tool()
def pvpc_manhana() -> str:
    """Obtiene los precios PVPC para mañana (disponible después de las 20:00)"""
    try:
        logger.info("🔧 Tool llamado: pvpc_manhana")
        hora_local = datetime.now()
        
        if hora_local.hour < 20:
            logger.warning(f"⏰ Datos de mañana solicitados a las {hora_local.hour}:00 (disponible desde las 20:00)")
            return json.dumps({
                "error": "Datos de mañana no disponibles hasta las 20:00",
                "hora_actual": hora_local.strftime("%H:%M")
            }, ensure_ascii=False)

        manana = datetime.now(timezone.utc) + timedelta(days=1)
        valores = pedir_1001(manana)
        resultado = procesar(valores)
        return json.dumps(resultado, ensure_ascii=False)
    
    except Exception as e:
        logger.error(f"💥 Error en pvpc_manhana: {e}")
        return json.dumps({"error": str(e)}, ensure_ascii=False)

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    logger.info(f"🌐 Iniciando servidor en puerto {PORT}")
    server.run()
