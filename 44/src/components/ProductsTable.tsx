import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { X } from 'lucide-react';
import { useState } from 'react';

interface Product {
  id: number;
  name: string;
  quantity: number;
  unit: string;
  warehouse: string;
  available: number;
  priceUSD: number;
  priceIQD: number;
  discount: number;
  total: number;
}

interface ProductsTableProps {
  onSearchClick: () => void;
}

export function ProductsTable({ onSearchClick }: ProductsTableProps) {
  const [products, setProducts] = useState<Product[]>([]);

  const removeProduct = (id: number) => {
    setProducts(products.filter(p => p.id !== id));
  };

  const updateQuantity = (id: number, quantity: number) => {
    setProducts(products.map(p => 
      p.id === id ? { ...p, quantity, total: quantity * p.priceUSD } : p
    ));
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="bg-blue-600 hover:bg-blue-600">
              <TableHead className="text-white text-center w-12">#</TableHead>
              <TableHead className="text-white min-w-[200px]">Product</TableHead>
              <TableHead className="text-white text-center w-24">Quantity</TableHead>
              <TableHead className="text-white text-center w-24">UoM</TableHead>
              <TableHead className="text-white text-center w-28">Warehouse</TableHead>
              <TableHead className="text-white text-center w-24">Available</TableHead>
              <TableHead className="text-white text-center w-28">Price (USD)</TableHead>
              <TableHead className="text-white text-center w-28">Price (IQD)</TableHead>
              <TableHead className="text-white text-center w-24">Disc. %</TableHead>
              <TableHead className="text-white text-center w-28">Total</TableHead>
              <TableHead className="text-white text-center w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {products.map((product, index) => (
              <TableRow key={product.id} className="hover:bg-blue-50/50 border-b border-gray-100">
                <TableCell className="text-center">{index + 1}</TableCell>
                <TableCell>
                  <button
                    onClick={onSearchClick}
                    className="w-full text-left px-2 py-1 rounded hover:bg-blue-50 text-gray-700 transition-colors"
                  >
                    {product.name}
                  </button>
                </TableCell>
                <TableCell>
                  <Input 
                    type="number"
                    value={product.quantity}
                    onChange={(e) => updateQuantity(product.id, parseInt(e.target.value) || 0)}
                    className="text-center h-8 border-gray-200 focus:border-blue-500"
                  />
                </TableCell>
                <TableCell className="text-center text-sm text-gray-600">{product.unit}</TableCell>
                <TableCell className="text-center text-sm text-gray-600">{product.warehouse}</TableCell>
                <TableCell className="text-center text-sm">{product.available}</TableCell>
                <TableCell className="text-center text-sm">${product.priceUSD.toFixed(2)}</TableCell>
                <TableCell className="text-center text-sm">{product.priceIQD.toFixed(2)}</TableCell>
                <TableCell className="text-center text-sm">{product.discount}%</TableCell>
                <TableCell className="text-center">${product.total.toFixed(2)}</TableCell>
                <TableCell className="text-center">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                    onClick={() => removeProduct(product.id)}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {[...Array(10 - products.length)].map((_, i) => (
              <TableRow key={`empty-${i}`} className="hover:bg-blue-50/50 border-b border-gray-100">
                <TableCell className="text-center text-gray-400">{products.length + i + 1}</TableCell>
                <TableCell>
                  <button
                    onClick={onSearchClick}
                    className="w-full text-left px-2 py-1 rounded hover:bg-blue-50 text-gray-400 transition-colors"
                  >
                    Search product...
                  </button>
                </TableCell>
                <TableCell>
                  <Input 
                    type="number"
                    defaultValue="1"
                    className="text-center h-8 border-gray-200 focus:border-blue-500"
                  />
                </TableCell>
                <TableCell className="text-center text-sm text-gray-400">Unit...</TableCell>
                <TableCell className="text-center text-sm text-gray-400">WH...</TableCell>
                <TableCell className="text-center text-sm text-gray-400">0</TableCell>
                <TableCell className="text-center text-sm text-gray-400">0.00</TableCell>
                <TableCell className="text-center text-sm text-gray-400">0.00</TableCell>
                <TableCell className="text-center text-sm text-gray-400">0</TableCell>
                <TableCell className="text-center text-sm text-gray-400">0.00</TableCell>
                <TableCell className="text-center">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
