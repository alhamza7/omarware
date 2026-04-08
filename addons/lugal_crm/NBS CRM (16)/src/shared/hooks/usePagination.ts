import { useState, useCallback } from 'react';

interface UsePaginationReturn {
  page:       number;
  perPage:    number;
  setPage:    (page: number) => void;
  setPerPage: (perPage: number) => void;
  nextPage:   () => void;
  prevPage:   () => void;
  reset:      () => void;
}

/**
 * Reusable pagination state hook.
 * Use in every container that displays a paginated list.
 */
export function usePagination(defaultPerPage = 20): UsePaginationReturn {
  const [page,    setPage]    = useState(1);
  const [perPage, setPerPage] = useState(defaultPerPage);

  const nextPage = useCallback(() => setPage((p) => p + 1), []);
  const prevPage = useCallback(() => setPage((p) => Math.max(1, p - 1)), []);
  const reset    = useCallback(() => setPage(1), []);

  return { page, perPage, setPage, setPerPage, nextPage, prevPage, reset };
}
