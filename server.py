from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
import requests
import os
from datetime import datetime, timedelta
import asyncio

app = FastAPI()

# Get ESIOS token from environment variable
ESIOS_TOKEN = os.getenv("ESIOS_TOKEN")

# Semaphore to limit concurrent requests
semaphore = asyncio.Semaphore(5)

async def fetch_pvpc_data(date_str):
    """Fetch PVPC data from ESIOS API with retry logic"""
    async with semaphore:
        headers = {
            "Authorization": f"Token token={ESIOS_TOKEN}",
            "Accept": "application/json"
        }
        
        url = f"https://api.esios.ree.es/indicators/1001?start_date={date_str}T00:00:00&end_date={date_str}T23:59:59"
        
        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1 * (attempt + 1))

@app.get("/hoy")
async def get_today_prices():
    """Get today's PVPC prices"""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        data = await fetch_pvpc_data(today)
        
        if "indicator" in data and "values" in data["indicator"]:
            prices = []
            for value in data["indicator"]["values"]:
                prices.append({
                    "datetime": value["datetime"],
                    "value": value["value"],
                    "datetime_utc": value.get("datetime_utc", value["datetime"])
                })
            
            return JSONResponse(content={
                "date": today,
                "prices": prices,
                "unit": "€/MWh"
            })
        else:
            return JSONResponse(
                status_code=500,
                content={"error": "Invalid response format from ESIOS API"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/manana")
async def get_tomorrow_prices():
    """Get tomorrow's PVPC prices"""
    try:
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        data = await fetch_pvpc_data(tomorrow)
        
        if "indicator" in data and "values" in data["indicator"]:
            prices = []
            for value in data["indicator"]["values"]:
                prices.append({
                    "datetime": value["datetime"],
                    "value": value["value"],
                    "datetime_utc": value.get("datetime_utc", value["datetime"])
                })
            
            return JSONResponse(content={
                "date": tomorrow,
                "prices": prices,
                "unit": "€/MWh"
            })
        else:
            return JSONResponse(
                status_code=500,
                content={"error": "Invalid response format from ESIOS API"}
            )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

@app.get("/.well-known/openai-apps-challenge")
async def openai_verification():
    """Serve OpenAI verification file"""
    return FileResponse(
        path=".well-known/openai-apps-challenge",
        media_type="text/plain"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
