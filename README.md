# PVPC GPT

Aplicación GPT para consultar el PVPC (Precio Voluntario para el Pequeño Consumidor) en tiempo real usando el indicador 1001 de ESIOS.

## 📋 Descripción

Esta aplicación proporciona una API REST para obtener datos del precio de la electricidad en España (PVPC) desde el sistema ESIOS (Sistema de Información del Operador del Sistema) de Red Eléctrica de España.

## 🚀 Características

- Consulta del precio actual del PVPC
- Obtención de todos los precios del día
- Resumen diario con precios mínimo, máximo y promedio
- API REST compatible con OpenAI Custom GPT
- Soporte para token de ESIOS (opcional)

## 📦 Instalación

1. Clona el repositorio:
```bash
git clone https://github.com/dvdzapata/pvpc-gpt.git
cd pvpc-gpt
```

2. Instala las dependencias:
```bash
npm install
```

3. Configura las variables de entorno:
```bash
cp .env.example .env
```

Edita el archivo `.env` y añade tu token de ESIOS si lo tienes (opcional pero recomendado):
```
PORT=3000
ESIOS_TOKEN=tu_token_aqui
```

Para obtener un token de ESIOS, visita: https://api.esios.ree.es/

## 🔧 Uso

### Modo desarrollo
```bash
npm run dev
```

### Compilar y ejecutar en producción
```bash
npm run build
npm start
```

## 🌐 Endpoints de la API

### GET /
Información general de la API

### GET /pvpc/current
Obtiene el precio actual del PVPC para la hora en curso.

**Respuesta de ejemplo:**
```json
{
  "success": true,
  "data": {
    "indicator": "PVPC",
    "timestamp": "2026-01-04T08:00:00Z",
    "value": 120.5,
    "units": "€/MWh"
  }
}
```

### GET /pvpc/today
Obtiene todos los precios del PVPC del día actual.

**Respuesta de ejemplo:**
```json
{
  "success": true,
  "count": 24,
  "data": [
    {
      "indicator": "PVPC",
      "timestamp": "2026-01-04T00:00:00Z",
      "value": 115.3,
      "units": "€/MWh"
    },
    ...
  ]
}
```

### GET /pvpc/summary
Obtiene un resumen con los precios mínimo, máximo, promedio y actual del día.

**Respuesta de ejemplo:**
```json
{
  "success": true,
  "data": {
    "min": 98.5,
    "max": 145.8,
    "average": 122.3,
    "current": 120.5,
    "unit": "€/MWh"
  }
}
```

### GET /health
Verifica el estado del servidor.

## 🤖 Integración con OpenAI Custom GPT

Para usar esta API con un Custom GPT de OpenAI:

1. Despliega el servidor en un servicio accesible públicamente (Heroku, Railway, Vercel, etc.)
2. En la configuración de tu Custom GPT, añade la URL de tu servidor
3. Configura las acciones (actions) usando los endpoints disponibles

### Ejemplo de configuración de acciones para GPT

```yaml
openapi: 3.0.0
info:
  title: PVPC API
  version: 1.0.0
servers:
  - url: https://tu-servidor.com
paths:
  /pvpc/current:
    get:
      operationId: getCurrentPrice
      summary: Obtiene el precio actual del PVPC
  /pvpc/summary:
    get:
      operationId: getDailySummary
      summary: Obtiene el resumen del día
```

## 📊 Sobre ESIOS e Indicador 1001

- **ESIOS**: Sistema de Información del Operador del Sistema de Red Eléctrica de España
- **Indicador 1001**: PVPC (Precio Voluntario para el Pequeño Consumidor)
- **Unidades**: €/MWh (euros por megavatio-hora)

## 🛠️ Tecnologías

- Node.js
- TypeScript
- Express.js
- ESIOS API

## 📝 Licencia

MIT

## 👤 Autor

David Fimia Zapata
