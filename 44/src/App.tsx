import { useState } from 'react';
import { Header } from './components/Header';
import { CustomerSection } from './components/CustomerSection';
import { ProductsTable } from './components/ProductsTable';
import { ProductSearchModal } from './components/ProductSearchModal';
import { OrderSummary } from './components/OrderSummary';

export default function App() {
  const [isSearchOpen, setIsSearchOpen] = useState(false);

  const handleSelectProduct = (product: any) => {
    console.log('Selected product:', product);
    // هنا يمكن إضافة المنتج للجدول
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      
      <CustomerSection />
      
      <div className="flex-1 px-6 py-6 max-w-[1800px] mx-auto w-full">
        <ProductsTable onSearchClick={() => setIsSearchOpen(true)} />
      </div>
      
      <OrderSummary />
      
      <ProductSearchModal 
        open={isSearchOpen}
        onOpenChange={setIsSearchOpen}
        onSelectProduct={handleSelectProduct}
      />
    </div>
  );
}
