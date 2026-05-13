import { useState, useCallback, useRef } from 'react';
import type { Customer } from '../../../types/pos';
import posPerfumeApi from '../../../services/posPerfumeApi';

/**
 * Debounced customer search against the API.
 * Returns search state and a function to trigger the search.
 */
export function useCustomerSearch() {
  const [results,   setResults]   = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error,     setError]     = useState<string | null>(null);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** Search customers with 300 ms debounce */
  const search = useCallback((query: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);

    if (!query || query.trim().length < 1) {
      setResults([]);
      return;
    }

    debounceRef.current = setTimeout(async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await posPerfumeApi.listCustomers({ query: query.trim(), limit: 20 });
        if (res.success && res.data) {
          setResults(res.data.items ?? []);
        } else {
          setError(res.error ?? 'Customer search failed');
          setResults([]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Network error');
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, 300);
  }, []);

  const clearResults = useCallback(() => {
    setResults([]);
    setError(null);
  }, []);

  return { results, isLoading, error, search, clearResults };
}
