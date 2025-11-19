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
