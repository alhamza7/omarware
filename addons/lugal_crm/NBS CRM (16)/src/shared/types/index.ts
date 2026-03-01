/** Shared pagination params sent to API */
export interface PaginationParams {
  page:     number;
  per_page: number;
}

/** Paginated API response wrapper */
export interface PaginatedResponse<T> {
  total:    number;
  page:     number;
  per_page: number;
  items:    T[];
}

/** Generic select option used in dropdowns */
export interface SelectOption {
  id:    number | string;
  name:  string;
  label?: string;
}

/** Branch reference used in filters */
export interface BranchRef {
  id:   number;
  name: string;
  code: string;
}

/** User reference (res.users) */
export interface UserRef {
  id:   number;
  name: string;
}

/** Theme types */
export type ColorTheme = 'dark-gold' | 'light-turquoise';

/** Active sidebar tab */
export type ActiveTab =
  | 'dashboard'
  | 'customers'
  | 'products'
  | 'orders'
  | 'supply-chain'
  | 'analytics'
  | 'call-centre'
  | 'knowledge-base'
  | 'admin-dashboard'
  | 'settings'
  | 'omni-channel'
  | 'tickets'
  | 'agents'
  | 'promotions'
  | 'sales-pipeline'
  | 'forecasting'
  | 'event-log';
