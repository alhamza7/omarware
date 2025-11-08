import { Button } from './ui/button';
import { Input } from './ui/input';
import { Search } from 'lucide-react';

export function CustomerSection() {
  return (
    <div className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
      <div className="max-w-[1800px] mx-auto">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">Customer:</label>
            <Input 
              placeholder="Search customer..."
              className="w-48 h-9"
            />
          </div>
          
          <Button 
            variant="outline" 
            size="sm"
            className="h-9 border-blue-300 text-blue-700 hover:bg-blue-50"
          >
            <Search className="w-4 h-4 mr-2" />
            Search
          </Button>
          
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">Pricelist:</label>
            <select className="h-9 px-3 border border-gray-300 rounded-md text-sm bg-white focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option>SAP Price List 1</option>
              <option>SAP Price List 2</option>
            </select>
          </div>
          
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 whitespace-nowrap">Order #:</label>
            <Input 
              placeholder="New Order"
              defaultValue="New Order"
              className="w-32 h-9"
            />
          </div>
          
          <div className="flex gap-2 ml-auto">
            <Button 
              className="h-9 bg-blue-600 hover:bg-blue-700 text-white"
            >
              # Load
            </Button>
            <Button 
              className="h-9 bg-green-600 hover:bg-green-700 text-white"
            >
              New
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
