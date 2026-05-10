import { useSupplyChain } from '../hooks/useSupplyChain';
import { SupplyChain } from '../../../app/components/supply-chain/supply-chain';
import type { ApiSupplyPo } from '../../../app/components/supply-chain/sc-purchase-orders';

/** Connects SupplyChain UI with live POs, vendors, and containers from API */
export function SupplyChainContainer() {
  const { purchaseOrders } = useSupplyChain();

  return (
    <SupplyChain apiPurchaseOrders={purchaseOrders as unknown as ApiSupplyPo[]} />
  );
}
