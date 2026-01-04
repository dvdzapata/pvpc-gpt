import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import requests
from typing import Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PVPC GPT API",
    description="API para consultar precios de electricidad PVPC en España",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PriceQuery(BaseModel):
    fecha: Optional[str] = None
    hora: Optional[int] = None

@app.get("/")
async def root():
    """Endpoint raíz con información de la API"""
    return {
        "message": "PVPC GPT API - Consulta precios de electricidad en España",
        "endpoints": {
            "/precio-actual": "Obtiene el precio actual de la electricidad",
            "/precio": "Obtiene precios por fecha y/o hora específica",
            "/health": "Estado de salud de la API"
        }
    }

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

@app.get("/health")
async def health():
    """Endpoint de salud"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/precio-actual")
async def precio_actual():
    """Obtiene el precio actual de la electricidad PVPC"""
    try:
        logger.info("📊 Consultando precio actual PVPC")
        
        # Obtener fecha y hora actual en España
        now = datetime.now()
        fecha = now.strftime("%Y-%m-%d")
        hora = now.hour
        
        # Consultar API de REE
        url = f"https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
        params = {
            "start_date": f"{fecha}T00:00",
            "end_date": f"{fecha}T23:59",
            "time_trunc": "hour"
        }
        
        logger.info(f"🔍 Consultando REE para fecha {fecha}, hora {hora}")
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Buscar el precio PVPC en los datos
        pvpc_data = None
        for indicator in data.get("included", []):
            if indicator.get("type") == "PVPC":
                pvpc_data = indicator
                break
        
        if not pvpc_data:
            logger.warning("⚠️ No se encontraron datos PVPC")
            raise HTTPException(status_code=404, detail="No se encontraron datos PVPC")
        
        # Obtener el precio de la hora actual
        valores = pvpc_data.get("attributes", {}).get("values", [])
        precio_actual = None
        
        for valor in valores:
            valor_datetime = datetime.fromisoformat(valor["datetime"].replace("Z", "+00:00"))
            if valor_datetime.hour == hora:
                precio_actual = valor["value"]
                break
        
        if precio_actual is None:
            logger.warning(f"⚠️ No se encontró precio para la hora {hora}")
            raise HTTPException(status_code=404, detail=f"No se encontró precio para la hora {hora}")
        
        # Convertir de €/MWh a €/kWh
        precio_kwh = precio_actual / 1000
        
        logger.info(f"✅ Precio actual: {precio_kwh:.4f} €/kWh")
        
        return {
            "fecha": fecha,
            "hora": hora,
            "precio_mwh": round(precio_actual, 2),
            "precio_kwh": round(precio_kwh, 4),
            "unidad": "€/kWh",
            "timestamp": now.isoformat()
        }
        
    except requests.RequestException as e:
        logger.error(f"❌ Error al consultar API REE: {str(e)}")
        raise HTTPException(status_code=503, detail="Error al consultar datos de REE")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/precio")
async def precio(query: PriceQuery):
    """Obtiene precios PVPC por fecha y/o hora específica"""
    try:
        # Si no se proporciona fecha, usar la actual
        if query.fecha is None:
            fecha = datetime.now().strftime("%Y-%m-%d")
        else:
            fecha = query.fecha
        
        logger.info(f"📊 Consultando precios PVPC para {fecha}")
        
        # Consultar API de REE
        url = f"https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
        params = {
            "start_date": f"{fecha}T00:00",
            "end_date": f"{fecha}T23:59",
            "time_trunc": "hour"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Buscar el precio PVPC en los datos
        pvpc_data = None
        for indicator in data.get("included", []):
            if indicator.get("type") == "PVPC":
                pvpc_data = indicator
                break
        
        if not pvpc_data:
            logger.warning("⚠️ No se encontraron datos PVPC")
            raise HTTPException(status_code=404, detail="No se encontraron datos PVPC")
        
        valores = pvpc_data.get("attributes", {}).get("values", [])
        
        # Si se especifica hora, devolver solo esa hora
        if query.hora is not None:
            for valor in valores:
                valor_datetime = datetime.fromisoformat(valor["datetime"].replace("Z", "+00:00"))
                if valor_datetime.hour == query.hora:
                    precio_mwh = valor["value"]
                    precio_kwh = precio_mwh / 1000
                    
                    logger.info(f"✅ Precio para hora {query.hora}: {precio_kwh:.4f} €/kWh")
                    
                    return {
                        "fecha": fecha,
                        "hora": query.hora,
                        "precio_mwh": round(precio_mwh, 2),
                        "precio_kwh": round(precio_kwh, 4),
                        "unidad": "€/kWh"
                    }
            
            raise HTTPException(status_code=404, detail=f"No se encontró precio para la hora {query.hora}")
        
        # Si no se especifica hora, devolver todos los precios del día
        precios = []
        for valor in valores:
            valor_datetime = datetime.fromisoformat(valor["datetime"].replace("Z", "+00:00"))
            precio_mwh = valor["value"]
            precio_kwh = precio_mwh / 1000
            
            precios.append({
                "hora": valor_datetime.hour,
                "precio_mwh": round(precio_mwh, 2),
                "precio_kwh": round(precio_kwh, 4)
            })
        
        logger.info(f"✅ Devolviendo {len(precios)} precios para {fecha}")
        
        return {
            "fecha": fecha,
            "precios": precios,
            "unidad": "€/kWh"
        }
        
    except requests.RequestException as e:
        logger.error(f"❌ Error al consultar API REE: {str(e)}")
        raise HTTPException(status_code=503, detail="Error al consultar datos de REE")
    except Exception as e:
        logger.error(f"❌ Error inesperado: {str(e)}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
