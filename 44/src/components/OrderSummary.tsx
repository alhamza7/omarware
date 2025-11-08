import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { FileText, ShoppingCart, Save, XCircle, MessageSquare } from 'lucide-react';

export function OrderSummary() {
  const subtotal = 0.00;
  const taxRate = 0;
  const taxAmount = 0.00;
  const discount = 0.00;
  const grandTotal = subtotal + taxAmount - discount;
  const totalIQD = 0;

  return (
    <div className="bg-white border-t-2 border-gray-200 px-6 py-4 shadow-lg">
      <div className="max-w-[1800px] mx-auto">
        <div className="flex items-center justify-between gap-8">
          <div className="flex items-center gap-8">
            <div className="space-y-2">
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600 w-24">Subtotal:</span>
                <span className="text-lg">${subtotal.toFixed(2)}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600 w-24">Tax total:</span>
                <span className="text-lg">${taxAmount.toFixed(2)}</span>
              </div>
            </div>
            
            <Separator orientation="vertical" className="h-16" />
            
            <div className="space-y-2">
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600 w-28">Discount:</span>
                <span className="text-lg">-${discount.toFixed(2)}</span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-gray-800 w-28">Grand Total:</span>
                <span className="text-2xl text-blue-600">${grandTotal.toFixed(2)}</span>
              </div>
            </div>
            
            <Separator orientation="vertical" className="h-16" />
            
            <div className="text-sm text-gray-600">
              <div>Total in Iraqi Dinar:</div>
              <div className="text-lg text-gray-800 mt-1">{totalIQD.toLocaleString()} <span className="text-sm">IQD</span></div>
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button 
              variant="outline"
              className="border-blue-300 text-blue-700 hover:bg-blue-50 h-10"
            >
              <FileText className="w-4 h-4 mr-2" />
              Quotation
            </Button>
            
            <Button 
              className="bg-green-600 hover:bg-green-700 text-white h-10"
            >
              <ShoppingCart className="w-4 h-4 mr-2" />
              Sale Order
            </Button>
            
            <Button 
              className="bg-blue-600 hover:bg-blue-700 text-white h-10"
            >
              <Save className="w-4 h-4 mr-2" />
              Draft
            </Button>
            
            <Button 
              className="bg-red-600 hover:bg-red-700 text-white h-10"
            >
              <XCircle className="w-4 h-4 mr-2" />
              Cancel
            </Button>
            
            <Button 
              className="bg-green-500 hover:bg-green-600 text-white h-10"
            >
              <MessageSquare className="w-4 h-4 mr-2" />
              WhatsApp
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
