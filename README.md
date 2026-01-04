# 🔌 PVPC-GPT

Servidor MCP (Model Context Protocol) para consultar precios PVPC (Precio Voluntario para el Pequeño Consumidor) de electricidad en España en tiempo real.

## 🚀 Deploy rápido en Fly.io

### 1. Instalar Fly CLI
```bash
curl -L https://fly.io/install.sh | sh
```

### 2. Login en Fly.io
```bash
flyctl auth login
```

### 3. Deploy
```bash
flyctl deploy
```

¡Listo! Tu API estará corriendo en `https://pvpc-gpt.fly.dev`

## 📋 Configuración (Opcional)

Si quieres usar tu propio token de ESIOS:

```bash
flyctl secrets set ESIOS_TOKEN=tu_token_aqui
```

Obtén tu token en: https://www.esios.ree.es/es/pagina/api

## 🛠️ Funcionalidades

- ✅ **Precios de hoy**: Consulta los precios PVPC hora por hora
- ✅ **Precios de mañana**: Disponible después de las 20:00h
- ✅ **Semáforo de precios**: Clasificación por colores según el precio
- ✅ **Reintentos automáticos**: Gestión inteligente de errores de conexión
- ✅ **Logging detallado**: Seguimiento completo de todas las operaciones

## 📊 Semáforo de precios

- 🟢 **Verde**: < 0.10 €/kWh
- 🟡 **Amarillo**: 0.10 - 0.15 €/kWh
- 🟠 **Naranja**: 0.15 - 0.20 €/kWh
- 🔴 **Rojo**: 0.20 - 0.25 €/kWh
- 🟣 **Púrpura**: > 0.25 €/kWh

## 💰 Costos Fly.io

Este proyecto está optimizado para el **plan gratuito** de Fly.io:
- ✅ 256MB RAM (dentro del límite gratuito)
- ✅ Auto-suspend cuando no hay tráfico
- ✅ Auto-start en nuevas peticiones
- ✅ **$0/mes** con tráfico moderado

## 📝 Licencia

MIT