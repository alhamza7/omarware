import { useState, useCallback, useRef } from 'react';
import type { ApiResult } from '../services/apiClient';

interface UseApiState<T> {
  data:      T | null;
  loading:   boolean;
  error:     string | null;
}

interface UseApiReturn<T, A extends unknown[]> extends UseApiState<T> {
  execute:  (...args: A) => Promise<ApiResult<T>>;
  reset:    () => void;
}

/**
 * Generic hook wrapping any async API call.
 * Handles loading, error, and data state automatically.
 *
 * @param fn - The async service function to call
 */
export function useApi<T, A extends unknown[]>(
  fn: (...args: A) => Promise<ApiResult<T>>,
): UseApiReturn<T, A> {
  const [data,    setData]    = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);
  const mountedRef = useRef(true);

  const execute = useCallback(
    async (...args: A): Promise<ApiResult<T>> => {
      setLoading(true);
      setError(null);
      const result = await fn(...args);
      if (mountedRef.current) {
        if (result.success && result.data !== undefined) {
          setData(result.data);
        } else {
          setError(result.error ?? 'An error occurred');
        }
        setLoading(false);
      }
      return result;
    },
    [fn],
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}
