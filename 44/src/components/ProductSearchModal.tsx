import { Dialog, DialogContent, DialogHeader, DialogTitle } from './ui/dialog';
import { Input } from './ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { Badge } from './ui/badge';
import { Search, X } from 'lucide-react';
import { useState } from 'react';

interface Product {
  code: string;
  name: string;
  nameAr?: string;
  uom: string;
  priceUSD: number;
  stock: number;
  warehouse: string;
}

interface ProductSearchModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelectProduct: (product: Product) => void;
}

export function ProductSearchModal({ open, onOpenChange, onSelectProduct }: ProductSearchModalProps) {
  const [searchTerm, setSearchTerm] = useState('');

  // Mock data - في التطبيق الحقيقي سيتم جلبها من API
  const allProducts: Product[] = [
    { code: 'SA0TH', name: 'S-342', nameAr: 'شاشة 32 بوصة', uom: 'شاشة 32 بوصة', priceUSD: 97.00, stock: 893, warehouse: 'BN-1' },
    { code: 'BSN0421', name: 'K M', uom: 'شاشة بيتلز', priceUSD: 52.00, stock: 46, warehouse: 'BN-2' },
    { code: 'BSN0441', name: 'K M', uom: 'سوبر مام', priceUSD: 52.00, stock: 31, warehouse: 'BN-1' },
    { code: 'RG0756', name: 'K M', nameAr: 'سوبر مام', uom: 'يو بوكسس', priceUSD: 140.00, stock: 0, warehouse: 'No stock' },
    { code: 'PRM00658', name: 'K M', nameAr: 'موتور اس ام', uom: 'LOCK OIL RUCH KIWI', priceUSD: 0.00, stock: 0, warehouse: 'No stock' },
    { code: 'PRM00049', name: 'K M', nameAr: 'موتور اس ام', uom: 'LOCK OIL RUCH KIWI PRAWDZIASZ CRĄG SZL M', priceUSD: 90.00, stock: 0, warehouse: 'No stock' },
    { code: 'ACP00319', name: 'كيبورد ام', uom: 'حار', priceUSD: 9.00, stock: 18, warehouse: 'BN-2' },
    { code: 'ACP00761', name: 'كيبورد ام', uom: 'حار', priceUSD: 317.00, stock: 51, warehouse: 'BN-2' },
    { code: 'PRM00412', name: 'K M', nameAr: 'سوبرمانشو', uom: 'PRM SG', priceUSD: 60.00, stock: 0, warehouse: 'No stock' },
    { code: 'PRM00633', name: 'K M', nameAr: 'سوبرمانشو', uom: 'JUMBO', priceUSD: 60.00, stock: 0, warehouse: 'No stock' },
    { code: 'LOC00027', name: 'K M', nameAr: 'خبرات أرامكو', uom: 'حار', priceUSD: 275.00, stock: 0, warehouse: 'No stock' },
  ];

  const filteredProducts = searchTerm.length >= 2 
    ? allProducts.filter(p => 
        p.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (p.nameAr && p.nameAr.includes(searchTerm))
      )
    : [];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] p-0 gap-0">
        <DialogHeader className="bg-blue-600 text-white px-6 py-4 rounded-t-lg">
          <div className="flex items-center justify-between">
            <DialogTitle className="text-xl">Product Search</DialogTitle>
            <div className="flex items-center gap-2 bg-white/20 px-3 py-1 rounded-md">
              <span className="text-sm">{filteredProducts.length} results</span>
            </div>
          </div>
        </DialogHeader>
        
        <div className="p-6 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input 
              placeholder="Search by code, name, or barcode..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 h-11 border-gray-300 focus:border-blue-500"
              autoFocus
            />
          </div>
          
          {searchTerm.length < 2 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-20 h-20 bg-blue-50 rounded-full flex items-center justify-center mb-4">
                <Search className="w-10 h-10 text-blue-300" />
              </div>
              <p className="text-gray-600 mb-1">Type 2+ characters to search</p>
              <p className="text-sm text-gray-400">Search by product name, code or barcode</p>
            </div>
          ) : (
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <div className="max-h-[450px] overflow-y-auto">
                <Table>
                  <TableHeader className="sticky top-0 bg-blue-50 z-10">
                    <TableRow>
                      <TableHead className="text-left">Code</TableHead>
                      <TableHead className="text-left">Product</TableHead>
                      <TableHead className="text-left">UoM</TableHead>
                      <TableHead className="text-center">Price (USD)</TableHead>
                      <TableHead className="text-center">Stock</TableHead>
                      <TableHead className="text-center">Warehouse</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredProducts.length > 0 ? (
                      filteredProducts.map((product, index) => (
                        <TableRow 
                          key={index}
                          className="cursor-pointer hover:bg-blue-50 transition-colors"
                          onClick={() => {
                            onSelectProduct(product);
                            onOpenChange(false);
                            setSearchTerm('');
                          }}
                        >
                          <TableCell className="text-sm text-blue-600">{product.code}</TableCell>
                          <TableCell>
                            <div>
                              <div className="text-sm">{product.name}</div>
                              {product.nameAr && (
                                <div className="text-xs text-gray-500">{product.nameAr}</div>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-sm text-gray-600">{product.uom}</TableCell>
                          <TableCell className="text-center text-sm">${product.priceUSD.toFixed(2)}</TableCell>
                          <TableCell className="text-center">
                            <Badge 
                              variant={product.stock > 0 ? 'default' : 'secondary'}
                              className={product.stock > 0 ? 'bg-green-100 text-green-700 hover:bg-green-100' : 'bg-red-100 text-red-700 hover:bg-red-100'}
                            >
                              {product.stock}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-center">
                            <Badge 
                              variant="outline"
                              className={product.stock > 0 ? 'border-green-300 text-green-700' : 'border-red-300 text-red-700'}
                            >
                              {product.warehouse}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))
                    ) : (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                          No products found matching "{searchTerm}"
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </div>
          )}
          
          <div className="flex items-center justify-between pt-2 border-t border-gray-200">
            <p className="text-sm text-gray-500">
              💡 Click on product to add to order
            </p>
            <p className="text-sm text-gray-500">
              {filteredProducts.length} results
            </p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
