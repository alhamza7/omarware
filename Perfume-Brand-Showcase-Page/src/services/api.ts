// API Service for fetching perfume data from Odoo
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8070';

export interface Note {
  name: string;
  category: 'top' | 'middle' | 'base';
}

export interface PerfumeTag {
  id: string;
  name: string;
}

export interface Perfume {
  id: string;        // perfume code
  name: string;
  brand: string;
  brandId: string;   // brand code
  image: string;
  season: string[];
  occasion: string[];
  longevity: string;
  sillage: string;
  description: string;
  notes: {
    top: string[];
    middle: string[];
    base: string[];
  };
  tags: PerfumeTag[];
}

export interface Brand {
  id: string;        // brand code
  name: string;
  country: string;
  perfumes: Perfume[];
}

class PerfumeAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetchAPI<T>(endpoint: string): Promise<T> {
    try {
      // Note: for GET requests we avoid setting custom headers to keep the request "simple"
      // so that browsers don't send a CORS preflight (OPTIONS) request.
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        method: 'GET',
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error(`Error fetching ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * Get all brands with their perfumes
   */
  async getBrands(): Promise<Brand[]> {
    return this.fetchAPI<Brand[]>('/api/perfume/brands');
  }

  /**
   * Get a specific brand by code
   */
  async getBrand(brandCode: string): Promise<Brand> {
    return this.fetchAPI<Brand>(`/api/perfume/brands/${brandCode}`);
  }

  /**
   * Get all perfumes
   */
  async getPerfumes(brandId?: string): Promise<Perfume[]> {
    const endpoint = brandId 
      ? `/api/perfume/perfumes?brand_id=${brandId}`
      : '/api/perfume/perfumes';
    return this.fetchAPI<Perfume[]>(endpoint);
  }

  /**
   * Get a specific perfume by code
   */
  async getPerfume(perfumeCode: string): Promise<Perfume> {
    return this.fetchAPI<Perfume>(`/api/perfume/perfumes/${perfumeCode}`);
  }
}

// Export singleton instance
export const perfumeAPI = new PerfumeAPI();

// Export default for convenience
export default perfumeAPI;

