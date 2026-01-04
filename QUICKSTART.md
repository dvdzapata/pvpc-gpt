# Guía de Inicio Rápido

## Instalación y Ejecución

### 1. Instalar dependencias
```bash
npm install
```

### 2. Configurar variables de entorno (opcional)
```bash
cp .env.example .env
```

Si tienes un token de ESIOS, edita `.env` y añádelo:
```
ESIOS_TOKEN=tu_token_aqui
```

### 3. Ejecutar en modo desarrollo
```bash
npm run dev
```

El servidor estará disponible en `http://localhost:3000`

### 4. Compilar para producción
```bash
npm run build
npm start
```

## Probando los Endpoints

### Información de la API
```bash
curl http://localhost:3000/
```

### Precio actual
```bash
curl http://localhost:3000/pvpc/current
```

### Todos los precios del día
```bash
curl http://localhost:3000/pvpc/today
```

### Resumen del día
```bash
curl http://localhost:3000/pvpc/summary
```

### Estado del servidor
```bash
curl http://localhost:3000/health
```

## Ejemplo de Respuesta

### `/pvpc/current`
```json
{
  "success": true,
  "data": {
    "indicator": "PVPC",
    "timestamp": "2026-01-04T08:00:00.000Z",
    "value": 120.5,
    "units": "€/MWh"
  }
}
```

### `/pvpc/summary`
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

## Integración con ChatGPT

1. Despliega el servidor en un hosting público (Railway, Render, Fly.io, etc.)
2. Crea un Custom GPT en ChatGPT
3. En la configuración de Actions, sube el archivo `openapi.yaml`
4. Actualiza la URL del servidor en `openapi.yaml` con tu URL de producción
5. Guarda y prueba tu GPT

## Despliegue

### Railway
```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login
railway login

# Crear nuevo proyecto
railway init

# Desplegar
railway up
```

### Render
1. Conecta tu repositorio de GitHub
2. Selecciona "Web Service"
3. Build Command: `npm install && npm run build`
4. Start Command: `npm start`

### Fly.io
```bash
# Instalar Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Lanzar app
fly launch

# Desplegar
fly deploy
```

## Variables de Entorno en Producción

Asegúrate de configurar estas variables en tu plataforma de hosting:

- `PORT`: Puerto del servidor (normalmente lo asigna la plataforma)
- `ESIOS_TOKEN`: (Opcional) Token de API de ESIOS

## Obtener Token de ESIOS

1. Visita https://www.esios.ree.es/es
2. Regístrate o inicia sesión
3. Ve a tu perfil y genera un token de API
4. Añade el token a tu archivo `.env` o a las variables de entorno de tu hosting
