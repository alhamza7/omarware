import { useEffect } from 'react';
import { usePosStore } from '../store/posStore';
import posPerfumeApi from '../../../services/posPerfumeApi';

/**
 * Loads POS bootstrap data (pricelists, warehouses, exchange rate, etc.)
 * and session info on first mount. Runs only once.
 */
export function usePosSetup() {
  const store = usePosStore();

  useEffect(() => {
    if (store.isSetupLoaded) return;

    const load = async () => {
      try {
        // Load setup + session in parallel
        const [setupRes, sessionRes] = await Promise.all([
          posPerfumeApi.getSetup(),
          posPerfumeApi.getSession(),
        ]);

        if (setupRes.success && setupRes.data) {
          store.setSetup(setupRes.data);
        } else {
          store.setSetupError(setupRes.error ?? 'Failed to load POS setup');
        }

        if (sessionRes.success && sessionRes.data) {
          store.setSession(
            sessionRes.data.user_name,
            sessionRes.data.company_name,
            sessionRes.data.exchange_rate,
          );
        }
      } catch (err) {
        store.setSetupError(err instanceof Error ? err.message : 'Network error');
      }
    };

    load();
  }, []);

  return {
    setup:         store.setup,
    isSetupLoaded: store.isSetupLoaded,
    setupError:    store.setupError,
    exchangeRate:  store.exchangeRate,
    userName:      store.userName,
    companyName:   store.companyName,
    pricelists:    store.setup?.pricelists ?? [],
    warehouses:    store.setup?.warehouses ?? [],
    invoiceTypes:  store.setup?.invoice_types ?? [],
  };
}
