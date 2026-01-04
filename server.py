import os
import logging
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import httpx

# -------------------------
# CONFIGURACIÓN LOGGING
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# -------------------------
# FASTAPI APP
# -------------------------
app = FastAPI(
    title="PVPC Semáforo API",
    description="API para consultar el precio de la luz en España con sistema de semáforo",
    version="1.0.0"
)

# -------------------------
# FUNCIONES AUXILIARES
# -------------------------
def pvpc_semaforo(precio: float) -> dict:
    """
    Determina el color del semáforo según el precio.
    
    Args:
        precio: Precio en €/kWh
        
    Returns:
        dict con color, emoji y descripción
    """
    if precio < 0.10:
        return {
            "color": "🟢 VERDE",
            "emoji": "🟢",
            "descripcion": "Precio muy bajo - momento ideal para consumir"
        }
    elif precio < 0.15:
        return {
            "color": "🟡 AMARILLO",
            "emoji": "🟡",
            "descripcion": "Precio moderado - consumo normal"
        }
    else:
        return {
            "color": "🔴 ROJO",
            "emoji": "🔴",
            "descripcion": "Precio alto - evita consumos elevados"
        }

async def pedir_1001(fecha: str) -> dict:
    """
    Obtiene datos de PVPC desde la API de ESIOS (REE).
    
    Args:
        fecha: Fecha en formato YYYY-MM-DD
        
    Returns:
        dict con los datos de la API
    """
    url = "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
    params = {
        "start_date": f"{fecha}T00:00",
        "end_date": f"{fecha}T23:59",
        "time_trunc": "hour"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            logger.info(f"🔍 Consultando PVPC para {fecha}")
            response = await client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            logger.info(f"✅ Datos obtenidos correctamente para {fecha}")
            return data
        except httpx.HTTPError as e:
            logger.error(f"❌ Error HTTP al consultar API: {e}")
            raise HTTPException(status_code=502, detail=f"Error al consultar API de REE: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

def procesar(data: dict) -> dict:
    """
    Procesa los datos de la API y genera el resumen con semáforo.
    
    Args:
        data: Datos JSON de la API de REE
        
    Returns:
        dict con el resumen procesado
    """
    try:
        # Extraer valores de PVPC
        valores = data["included"][0]["attributes"]["values"]
        
        # Convertir a formato más legible
        precios = []
        for v in valores:
            hora = datetime.fromisoformat(v["datetime"].replace("Z", "+00:00"))
            precio_kwh = v["value"] / 1000  # De MWh a kWh
            semaforo = pvpc_semaforo(precio_kwh)
            
            precios.append({
                "hora": hora.strftime("%H:%M"),
                "precio": round(precio_kwh, 4),
                "precio_formatted": f"{precio_kwh:.4f} €/kWh",
                "semaforo": semaforo["emoji"],
                "color": semaforo["color"],
                "descripcion": semaforo["descripcion"]
            })
        
        # Calcular estadísticas
        precios_valores = [p["precio"] for p in precios]
        precio_medio = sum(precios_valores) / len(precios_valores)
        precio_min = min(precios_valores)
        precio_max = max(precios_valores)
        
        # Encontrar mejores y peores horas
        horas_min = [p for p in precios if p["precio"] == precio_min]
        horas_max = [p for p in precios if p["precio"] == precio_max]
        
        # Determinar semáforo para precio medio
        semaforo_medio = pvpc_semaforo(precio_medio)
        
        return {
            "resumen": {
                "precio_medio": round(precio_medio, 4),
                "precio_min": round(precio_min, 4),
                "precio_max": round(precio_max, 4),
                "semaforo": semaforo_medio["emoji"],
                "color": semaforo_medio["color"],
                "descripcion": semaforo_medio["descripcion"]
            },
            "mejores_horas": horas_min,
            "peores_horas": horas_max,
            "precios_por_hora": precios
        }
    except (KeyError, IndexError) as e:
        logger.error(f"❌ Error al procesar datos: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar datos de la API: {str(e)}")

# -------------------------
# ENDPOINTS
# -------------------------
@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "🌟 PVPC Semáforo API",
        "version": "1.0.0",
        "endpoints": {
            "/": "Información de la API",
            "/health": "Estado del servicio",
            "/hoy": "Precio de la luz HOY con semáforo",
            "/manana": "Precio de la luz MAÑANA con semáforo"
        },
        "semaforo": {
            "🟢": "< 0.10 €/kWh - Precio muy bajo",
            "🟡": "0.10-0.15 €/kWh - Precio moderado",
            "🔴": "> 0.15 €/kWh - Precio alto"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/hoy")
async def get_hoy():
    """Obtiene el precio de la luz para HOY"""
    fecha = datetime.utcnow().strftime("%Y-%m-%d")
    logger.info(f"📅 Solicitando precios para HOY: {fecha}")
    
    data = await pedir_1001(fecha)
    resultado = procesar(data)
    
    return {
        "fecha": fecha,
        "dia": "HOY",
        **resultado
    }

@app.get("/manana")
async def get_manana():
    """Obtiene el precio de la luz para MAÑANA"""
    fecha = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    logger.info(f"📅 Solicitando precios para MAÑANA: {fecha}")
    
    data = await pedir_1001(fecha)
    resultado = procesar(data)
    
    return {
        "fecha": fecha,
        "dia": "MAÑANA",
        **resultado
    }

# -------------------------
# VERIFICACIÓN OPENAI
# -------------------------
@app.get("/.well-known/openai-apps-challenge")
async def openai_challenge():
    """Sirve el archivo de verificación de OpenAI Apps"""
    file_path = ".well-known/openai-apps-challenge"
    if os.path.exists(file_path):
        logger.info("✅ Sirviendo archivo de verificación OpenAI")
        from fastapi.responses import FileResponse
        return FileResponse(file_path, media_type="text/plain")
    else:
        logger.error("❌ Archivo de verificación no encontrado")
        raise HTTPException(status_code=404, detail="Verification file not found")

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Iniciando servidor en puerto {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
