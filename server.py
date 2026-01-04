import os
import requests
from mcp.server.fastmcp import FastMCP

# ------------------------------------------------------------------
# MCP
# ------------------------------------------------------------------
mcp = FastMCP("PVPC-ESIOS")

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
ESIOS_TOKEN = os.getenv("ESIOS_TOKEN")
if not ESIOS_TOKEN:
    raise RuntimeError("ESIOS_TOKEN no definido")

HEADERS = {
    "Accept": "application/json; application/vnd.esios-api-v2+json",
    "Content-Type": "application/json",
    "Authorization": f"{ESIOS_TOKEN}",
}

URL_INDICATOR = "https://api.esios.ree.es/indicators/1001/"

# ------------------------------------------------------------------
# Core
# ------------------------------------------------------------------
def _leer_indicador():
    r = requests.get(URL_INDICATOR, headers=HEADERS, timeout=15)
    r.raise_for_status()
    return r.json()["indicator"]


def _normalizar_valores(values):
    salida = []

    for v in values:
        value_mwh = float(v["value"])
        value_kwh = value_mwh / 1000

        salida.append({
            "geo_id": v["geo_id"],
            "datetime": v["datetime"],
            "datetime_utc": v["datetime_utc"],
            "tz_time": v["tz_time"],
            "value_mwh": round(value_mwh, 4),
            "value_kwh": round(value_kwh, 6),
        })

    return salida


# ------------------------------------------------------------------
# MCP Tools
# ------------------------------------------------------------------
@mcp.tool()
def precios_pvpc():
    """
    Precios PVPC horarios disponibles actualmente según ESIOS (indicador 1001).
    Datos crudos normalizados, sin enriquecimiento.
    """
    indicator = _leer_indicador()

    return {
        "version": "1.0",
        "indicator": {
            "id": indicator["id"],
            "name": indicator["name"],
        },
        "updated_at": indicator["values_updated_at"],
        "timezone": indicator["timezone"],
        "currency": "EUR",
        "unit": {
            "base": "MWh",
            "derived": "kWh",
        },
        "data": _normalizar_valores(indicator["values"]),
    }


@mcp.tool()
def geos():
    """
    Catálogo de GEO_IDs disponibles para el indicador PVPC.
    """
    indicator = _leer_indicador()

    return {
        "version": "1.0",
        "indicator_id": indicator["id"],
        "geos": [
            {
                "geo_id": g["id"],
                "name": g["name"],
                "timezone": g["timezone"],
            }
            for g in indicator["geos"]
        ],
    }


# ------------------------------------------------------------------
# Run
# ------------------------------------------------------------------
if __name__ == "__main__":
    mcp.run(host="0.0.0.0", port=8080)
