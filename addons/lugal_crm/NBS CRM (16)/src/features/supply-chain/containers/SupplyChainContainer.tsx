import { useSupplyChain } from '../hooks/useSupplyChain';
import { SupplyChain } from '../../../app/components/supply-chain/supply-chain';

/** Connects SupplyChain UI with live POs, vendors, and containers from API */
export function SupplyChainContainer() {
  const {
    purchaseOrders, vendors, containers, selectedPo, isLoading, error,
    statusFilter, setStatusFilter, setSelected, createPo, confirmPo, cancelPo,
  } = useSupplyChain();

  return (
    <SupplyChain
      purchaseOrders={purchaseOrders as never}
      vendors={vendors as never}
      containers={containers as never}
      selectedPo={selectedPo as never}
      isLoading={isLoading}
      error={error}
      statusFilter={statusFilter}
      onStatusFilter={setStatusFilter}
      onSelectPo={setSelected as never}
      onCreatePo={createPo as never}
      onConfirmPo={confirmPo}
      onCancelPo={cancelPo}
    />
  );
}
