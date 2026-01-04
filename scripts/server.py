import json
import requests
from datetime import datetime, timedelta, timezone
from mcp.server import Server

ESIOS_TOKEN = "d6467eb25b2fa5e8226442a58b308d4cf3c54b23600ed70bcde4873e88066da6"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "x-api-key": ESIOS_TOKEN
}

server = Server("pvpc")

# -------------------------
# SEMÁFORO PVPC (€/kWh)
# -------------------------
def pvpc_semaforo(precio_kwh: float) -> str:
    if precio_kwh < 0.10:
        return "verde"
    elif precio_kwh < 0.15:
        return "amarillo"
    elif precio_kwh < 0.20:
        return "naranja"
    elif precio_kwh < 0.25:
        return "rojo"
    else:
        return "purpura"

# -------------------------
# PETICIÓN A ESIOS
# -------------------------
def pedir_1001(fecha):
    fecha_inicio = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    fecha_fin = fecha_inicio + timedelta(days=1)

    params = {
        "time_trunc": "hour",
        "start_date": fecha_inicio.isoformat(),
        "end_date": fecha_fin.isoformat()
    }

    url = "https://api.esios.ree.es/indicators/1001"
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    data = r.json()

    return data["indicator"]["values"]

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
            "precio_mwh": precio_mwh,
            "precio_kwh": precio_kwh,
            "semaforo": pvpc_semaforo(precio_kwh)
        })
    return salida

# -------------------------
# TOOL: HOY
# -------------------------
@server.tool()
def pvpc_hoy() -> str:
    ahora = datetime.now(timezone.utc)
    valores = pedir_1001(ahora)
    return json.dumps(procesar(valores), ensure_ascii=False)

# -------------------------
# TOOL: MAÑANA
# -------------------------
@server.tool()
def pvpc_manhana() -> str:
    hora_local = datetime.now()
    if hora_local.hour < 20:
        return json.dumps({"error": "Datos de mañana no disponibles hasta las 20:00"}, ensure_ascii=False)

    manana = datetime.now(timezone.utc) + timedelta(days=1)
    valores = pedir_1001(manana)
    return json.dumps(procesar(valores), ensure_ascii=False)

# -------------------------
# MAIN
# -------------------------
if __name__ == "__main__":
    server.run()
