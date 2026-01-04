import express, { Request, Response } from 'express';
import dotenv from 'dotenv';
import { ESIOSClient } from './esios.js';

// Cargar variables de entorno
dotenv.config();

const app = express();
const port = process.env.PORT || 3000;

// Crear instancia del cliente ESIOS
const esiosClient = new ESIOSClient(process.env.ESIOS_TOKEN);

// Middleware
app.use(express.json());

// CORS para permitir llamadas desde GPT
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept');
  next();
});

/**
 * Endpoint raíz - información de la API
 */
app.get('/', (req: Request, res: Response) => {
  res.json({
    name: 'PVPC GPT API',
    description: 'API para obtener datos del indicador 1001 de ESIOS (PVPC)',
    version: '1.0.0',
    endpoints: {
      '/': 'Información de la API',
      '/pvpc/current': 'Precio actual del PVPC',
      '/pvpc/today': 'Todos los precios del día',
      '/pvpc/summary': 'Resumen del día (min, max, promedio)'
    }
  });
});

/**
 * Endpoint para obtener el precio actual del PVPC
 */
app.get('/pvpc/current', async (req: Request, res: Response) => {
  try {
    const currentPrice = await esiosClient.getCurrentPrice();
    
    if (!currentPrice) {
      res.status(404).json({
        error: 'No se encontró el precio para la hora actual'
      });
      return;
    }

    res.json({
      success: true,
      data: currentPrice
    });
  } catch (error) {
    console.error('Error en /pvpc/current:', error);
    res.status(500).json({
      success: false,
      error: 'Error al obtener el precio actual del PVPC',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * Endpoint para obtener todos los precios del día
 */
app.get('/pvpc/today', async (req: Request, res: Response) => {
  try {
    const prices = await esiosClient.getCurrentPVPC();
    
    res.json({
      success: true,
      count: prices.length,
      data: prices
    });
  } catch (error) {
    console.error('Error en /pvpc/today:', error);
    res.status(500).json({
      success: false,
      error: 'Error al obtener los precios del día',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * Endpoint para obtener el resumen del día
 */
app.get('/pvpc/summary', async (req: Request, res: Response) => {
  try {
    const summary = await esiosClient.getDailySummary();
    
    res.json({
      success: true,
      data: summary
    });
  } catch (error) {
    console.error('Error en /pvpc/summary:', error);
    res.status(500).json({
      success: false,
      error: 'Error al obtener el resumen del día',
      message: error instanceof Error ? error.message : 'Unknown error'
    });
  }
});

/**
 * Endpoint de salud del servidor
 */
app.get('/health', (req: Request, res: Response) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString()
  });
});

// Iniciar servidor
app.listen(port, () => {
  console.log(`🚀 Servidor PVPC GPT corriendo en http://localhost:${port}`);
  console.log(`📊 Indicador ESIOS: 1001 (PVPC)`);
  console.log(`🔑 Token ESIOS: ${process.env.ESIOS_TOKEN ? 'Configurado' : 'No configurado (límites de API)'}`);
});

export default app;
