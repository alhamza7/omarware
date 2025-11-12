import { useState } from 'react';
import { Printer, Download } from 'lucide-react';
import { Button } from './ui/button';

interface InvoiceItem {
  id: number;
  name: string;
  quantity: number;
  unit: string;
  price: number;
  total: number;
}

export function OdooInvoice() {
  const [invoiceData] = useState({
    invoiceNumber: '25031055',
    date: '10/11/2025',
    time: '12:52PM',
    cashierNumber: 'IBG05777',
    paymentMethod: 'نقدي',
    dueDate: '10/11/2025',
    boxNumber: 'IBG05777',
    customer: {
      name: 'أحمد ضياء أحمد / ابو غريب',
      phone: '07826643939 - 07715509363',
      address: '6'
    },
    items: [
      { id: 1, name: 'بكارت روچ - ADF', quantity: 1, unit: 'كغم 0.25', price: 22.00, total: 22.00 },
      { id: 2, name: 'وصال - ADF', quantity: 1, unit: 'كغم 0.25', price: 19.50, total: 19.50 },
      { id: 3, name: 'البقرة - ADF', quantity: 1, unit: 'كغم 0.25', price: 14.50, total: 14.50 },
      { id: 4, name: 'لفعامة الشرق - ADF', quantity: 1, unit: 'كغم 0.25', price: 18.25, total: 18.25 },
      { id: 5, name: 'مونيسى كايبا - ADF L3', quantity: 1, unit: 'كغم 0.25', price: 14.50, total: 14.50 },
      { id: 6, name: 'راميا (عرض بلاك فرايد) - ADF', quantity: 1, unit: 'كغم 0.25', price: 8.50, total: 8.50 },
      { id: 7, name: 'نطبز م هروم - ADF', quantity: 1, unit: 'كغم 0.25', price: 15.75, total: 15.75 },
      { id: 8, name: 'شيكز - ADF M', quantity: 1, unit: 'كغم 0.25', price: 17.00, total: 17.00 },
      { id: 9, name: 'تيري هيرز - ADF', quantity: 1, unit: 'كغم 0.25', price: 20.75, total: 20.75 },
      { id: 10, name: 'جواد الليل - ADF', quantity: 1, unit: 'كغم 0.25', price: 17.00, total: 17.00 },
      { id: 11, name: 'بيلو فورمين - ADF M', quantity: 1, unit: 'كغم 0.25', price: 15.75, total: 15.75 },
      { id: 12, name: 'سفير سنت - ADF', quantity: 1, unit: 'كغم 0.25', price: 15.75, total: 15.75 },
    ] as InvoiceItem[]
  });

  const subtotal = invoiceData.items.reduce((sum, item) => sum + item.total, 0);
  const total = subtotal;

  const handlePrint = () => {
    window.print();
  };

  const handleDownload = () => {
    alert('تحميل الفاتورة كـ PDF');
  };

  return (
    <div className="max-w-5xl mx-auto">
      {/* Print buttons - hide on print */}
      <div className="mb-4 flex gap-2 justify-end print:hidden">
        <Button onClick={handlePrint} variant="default" className="gap-2">
          <Printer className="w-4 h-4" />
          طباعة
        </Button>
        <Button onClick={handleDownload} variant="outline" className="gap-2">
          <Download className="w-4 h-4" />
          تحميل PDF
        </Button>
      </div>

      {/* Invoice Container */}
      <div className="bg-white shadow-xl overflow-hidden print:shadow-none">
        {/* Header */}
        <div className="bg-white p-4 pb-3">
          <div className="flex items-center justify-between gap-4 mb-4">
            {/* Company Info - Right Side */}
            <div className="flex-1 text-right">
              <h1 className="text-blue-900 mb-0.5" style={{ fontSize: '20px', fontWeight: '700', lineHeight: '1.2' }}>
                شركة نور الإبرأس للتجارة العامة
              </h1>
              <p className="text-gray-600" style={{ fontSize: '11px' }}>
                Noor Alnibraas For General Trading
              </p>
            </div>

            {/* Logo - Center */}
            <div className="flex flex-col items-center">
              <div 
                className="bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-full flex items-center justify-center shadow-lg border-2 border-white"
                style={{ width: '70px', height: '70px' }}
              >
                <div className="text-center">
                  <div style={{ fontSize: '24px', lineHeight: '1' }}>☀️</div>
                </div>
              </div>
            </div>

            {/* Invoice Badge - Left Side */}
            <div className="flex-1 flex justify-start">
              <div className="bg-gradient-to-br from-yellow-400 to-yellow-500 px-5 py-2.5 rounded-lg shadow-lg border-2 border-yellow-600">
                <div className="text-center text-blue-900">
                  <div style={{ fontSize: '20px', lineHeight: '1' }}>🧾</div>
                  <h2 className="mt-1" style={{ fontSize: '14px', fontWeight: '600' }}>
                    فاتورة مبيعات
                  </h2>
                </div>
              </div>
            </div>
          </div>

          {/* Invoice Details Grid */}
          <div className="border-2 border-blue-600 rounded-lg overflow-hidden">
            <div className="grid grid-cols-3 bg-white">
              <div className="p-2 text-center border-l-2 border-blue-600">
                <div className="text-gray-600 mb-0.5" style={{ fontSize: '10px' }}>الوقت / اليوم</div>
                <div className="text-blue-900" style={{ fontSize: '12px', fontWeight: '600' }}>
                  {invoiceData.time}
                </div>
              </div>
              <div className="p-2 text-center border-l-2 border-blue-600">
                <div className="text-gray-600 mb-0.5" style={{ fontSize: '10px' }}>التاريخ</div>
                <div className="text-blue-900" style={{ fontSize: '12px', fontWeight: '600' }}>
                  {invoiceData.date}
                </div>
              </div>
              <div className="p-2 text-center">
                <div className="text-gray-600 mb-0.5" style={{ fontSize: '10px' }}>رقم الفاتورة</div>
                <div className="text-blue-900" style={{ fontSize: '12px', fontWeight: '600' }}>
                  {invoiceData.invoiceNumber}
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 bg-white border-t-2 border-blue-600">
              <div className="p-2 text-center border-l-2 border-blue-600">
                <div className="text-gray-600 mb-0.5" style={{ fontSize: '10px' }}>رقم التحصيل</div>
                <div className="text-blue-900" style={{ fontSize: '12px', fontWeight: '600' }}>
                  {invoiceData.cashierNumber}
                </div>
              </div>
              <div className="p-2 text-center">
                <div className="text-gray-600 mb-0.5" style={{ fontSize: '10px' }}>نوع العادرة</div>
                <div className="text-blue-900" style={{ fontSize: '12px', fontWeight: '600' }}>
                  {invoiceData.paymentMethod}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 bg-white border-t-2 border-blue-600">
              <div className="p-2 text-center border-l-2 border-blue-600">
                <div className="text-gray-600 mb-0.5" style={{ fontSize: '10px' }}>استحقاق الدفع</div>
                <div className="text-blue-900" style={{ fontSize: '12px', fontWeight: '600' }}>
                  {invoiceData.dueDate}
                </div>
              </div>
              <div className="p-2 text-center">
                <div className="text-gray-600 mb-0.5" style={{ fontSize: '10px' }}>رقم الصندوق</div>
                <div className="text-blue-900" style={{ fontSize: '12px', fontWeight: '600' }}>
                  {invoiceData.boxNumber}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Customer Info */}
        <div className="bg-gradient-to-r from-blue-700 to-blue-600 text-white">
          <div className="grid grid-cols-3">
            <div className="p-2.5 text-center border-l-2 border-blue-500">
              <div className="text-blue-200 mb-0.5" style={{ fontSize: '10px' }}>العنوان</div>
              <div style={{ fontSize: '12px', fontWeight: '500' }}>{invoiceData.customer.address}</div>
            </div>
            <div className="p-2.5 text-center border-l-2 border-blue-500">
              <div className="text-blue-200 mb-0.5" style={{ fontSize: '10px' }}>ملاحضات</div>
              <div style={{ fontSize: '12px', fontWeight: '500' }}>{invoiceData.customer.phone}</div>
            </div>
            <div className="p-2.5 text-center">
              <div className="text-blue-200 mb-0.5" style={{ fontSize: '10px' }}>الاسم</div>
              <div style={{ fontSize: '12px', fontWeight: '500' }}>{invoiceData.customer.name}</div>
            </div>
          </div>
        </div>

        <div className="bg-blue-600 text-white p-2 text-center shadow-sm">
          <span style={{ fontSize: '13px', fontWeight: '600' }}>المنتج</span>
        </div>

        {/* Items Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gradient-to-r from-yellow-400 to-yellow-500">
                <th className="p-2 text-center border-l-2 border-yellow-600" style={{ fontSize: '12px', fontWeight: '600', width: '5%' }}>
                  ت
                </th>
                <th className="p-2 text-right border-l-2 border-yellow-600" style={{ fontSize: '12px', fontWeight: '600', width: '45%' }}>
                  اسم المادة
                </th>
                <th className="p-2 text-center border-l-2 border-yellow-600" style={{ fontSize: '12px', fontWeight: '600', width: '10%' }}>
                  الكمية
                </th>
                <th className="p-2 text-center border-l-2 border-yellow-600" style={{ fontSize: '12px', fontWeight: '600', width: '15%' }}>
                  الوحدة
                </th>
                <th className="p-2 text-center border-l-2 border-yellow-600" style={{ fontSize: '12px', fontWeight: '600', width: '12.5%' }}>
                  سعر المادة
                </th>
                <th className="p-2 text-center" style={{ fontSize: '12px', fontWeight: '600', width: '12.5%' }}>
                  المجموع الكلي $
                </th>
              </tr>
            </thead>
            <tbody>
              {invoiceData.items.map((item, index) => (
                <tr
                  key={item.id}
                  className={`${
                    index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                  } border-b border-gray-200 hover:bg-blue-50 transition-colors`}
                >
                  <td className="p-2 text-center border-l border-gray-300" style={{ fontSize: '11px' }}>
                    {String(item.id).padStart(3, '0')}
                  </td>
                  <td className="p-2 text-right border-l border-gray-300" style={{ fontSize: '11px' }}>
                    {item.name}
                  </td>
                  <td className="p-2 text-center border-l border-gray-300" style={{ fontSize: '11px' }}>
                    {item.quantity}
                  </td>
                  <td className="p-2 text-center border-l border-gray-300" style={{ fontSize: '11px' }}>
                    {item.unit}
                  </td>
                  <td className="p-2 text-center border-l border-gray-300" style={{ fontSize: '11px' }}>
                    {item.price.toFixed(2)}
                  </td>
                  <td className="p-2 text-center" style={{ fontSize: '11px', fontWeight: '600' }}>
                    {item.total.toFixed(2)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Totals */}
        <div className="bg-gradient-to-br from-gray-50 to-gray-100 p-5 border-t-4 border-blue-600">
          <div className="max-w-lg mr-auto space-y-3">
            <div className="flex justify-between items-center p-3 bg-white rounded-lg shadow-sm border-2 border-gray-200">
              <span className="text-gray-700" style={{ fontSize: '13px', fontWeight: '600' }}>المجموع الفرعي:</span>
              <span className="text-blue-900" style={{ fontSize: '16px', fontWeight: '700' }}>{subtotal.toFixed(2)} $</span>
            </div>
            <div className="flex justify-between items-center p-4 bg-gradient-to-r from-blue-700 to-blue-600 text-white rounded-xl shadow-lg border-2 border-blue-800">
              <span style={{ fontSize: '15px', fontWeight: '600' }}>المجموع الكلي:</span>
              <span style={{ fontSize: '22px', fontWeight: '700' }}>{total.toFixed(2)} $</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gradient-to-r from-blue-700 to-blue-600 text-white p-4 text-center border-t-2 border-blue-800">
          <p className="mb-1" style={{ fontSize: '14px', fontWeight: '600' }}>شكراً لتعاملكم معنا</p>
          <p className="opacity-90" style={{ fontSize: '11px' }}>نتمنى لكم تجربة تسوق ممتعة</p>
          <div className="mt-3 pt-3 border-t border-blue-500 opacity-80">
            <p style={{ fontSize: '10px' }}>هذه فاتورة رسمية صادرة من نظام Odoo</p>
          </div>
        </div>
      </div>

      {/* Print Styles */}
      <style>{`
        @media print {
          body {
            margin: 0;
            padding: 0;
          }
          .print\\:hidden {
            display: none !important;
          }
          .print\\:shadow-none {
            box-shadow: none !important;
          }
          .print\\:rounded-none {
            border-radius: 0 !important;
          }
        }
      `}</style>
    </div>
  );
}
