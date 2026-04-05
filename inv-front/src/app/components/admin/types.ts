export type SortDirection = 'none' | 'asc' | 'desc';

export interface SortConfig {
  key: string;
  dir: SortDirection;
}

export interface ItemData {
  id: number;
  code: string;
  name: string;
  dateAdded: string;
}

export interface UserData {
  id: number;
  fullName: string;
  username: string;
  role: string;
  warehouse: string;
  dateAdded: string;
}

export interface BarcodeData {
  id: number;
  code: string;
  name: string;
  barcode: string;
  unit: string;
}

export interface AuditData {
  id: number;
  code: string;
  name: string;
  warehouse: string;
  quantity: string;
  user: string;
  date: string;
}

export type ViewState = 'main' | 'items' | 'users' | 'barcodes' | 'audits';
