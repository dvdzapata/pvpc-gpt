import fetch from 'node-fetch';

export interface PVPCData {
  indicator: string;
  timestamp: string;
  value: number;
  units: string;
}

export interface ESIOSResponse {
  indicator: {
    name: string;
    short_name: string;
  };
  values: Array<{
    value: number;
    datetime: string;
  }>;
}

/**
 * Cliente para obtener datos del indicador 1001 de ESIOS (PVPC)
 */
export class ESIOSClient {
  private readonly baseUrl = 'https://api.esios.ree.es';
  private readonly indicatorId = '1001'; // PVPC - Precio voluntario para el pequeño consumidor
  private readonly token: string;

  constructor(token?: string) {
    // Token opcional - ESIOS puede funcionar sin token pero con límites
    this.token = token || '';
  }

  /**
   * Obtiene los datos actuales del PVPC
   */
  async getCurrentPVPC(): Promise<PVPCData[]> {
    try {
      const today = new Date();
      const startDate = this.formatDate(today);
      const endDate = this.formatDate(today);

      const url = `${this.baseUrl}/indicators/${this.indicatorId}?start_date=${startDate}T00:00&end_date=${endDate}T23:59`;
      
      const headers: Record<string, string> = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      };

      if (this.token) {
        headers['x-api-key'] = this.token;
      }

      const response = await fetch(url, { headers });

      if (!response.ok) {
        throw new Error(`Error fetching ESIOS data: ${response.statusText}`);
      }

      const data = await response.json() as any;

      if (!data.indicator || !data.indicator.values) {
        throw new Error('Invalid response format from ESIOS');
      }

      return data.indicator.values.map((item: any) => ({
        indicator: 'PVPC',
        timestamp: item.datetime,
        value: item.value,
        units: '€/MWh'
      }));
    } catch (error) {
      console.error('Error fetching PVPC data:', error);
      throw error;
    }
  }

  /**
   * Obtiene el precio actual del PVPC
   */
  async getCurrentPrice(): Promise<PVPCData | null> {
    const data = await this.getCurrentPVPC();
    const now = new Date();
    
    // Encuentra el precio de la hora actual
    const currentHourData = data.find(item => {
      const itemDate = new Date(item.timestamp);
      return itemDate.getHours() === now.getHours() &&
             itemDate.toDateString() === now.toDateString();
    });

    return currentHourData || null;
  }

  /**
   * Formatea una fecha al formato requerido por ESIOS (YYYY-MM-DD)
   */
  private formatDate(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  /**
   * Obtiene el resumen del día (precio mínimo, máximo y promedio)
   */
  async getDailySummary(): Promise<{
    min: number;
    max: number;
    average: number;
    current: number | null;
    unit: string;
  }> {
    const data = await this.getCurrentPVPC();
    
    if (data.length === 0) {
      throw new Error('No data available');
    }

    const values = data.map(item => item.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const average = values.reduce((a, b) => a + b, 0) / values.length;
    
    const currentPrice = await this.getCurrentPrice();

    return {
      min,
      max,
      average: Math.round(average * 100) / 100,
      current: currentPrice?.value || null,
      unit: '€/MWh'
    };
  }
}
