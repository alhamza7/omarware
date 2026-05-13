import { ItemData, UserData, BarcodeData, AuditData } from './types';

export const initialItemsData: ItemData[] = [
  { id: 105746, code: 'ADF00001', name: 'CK1', dateAdded: '2026-03-05T12:08:40' },
  { id: 105747, code: 'ADF00002', name: 'المليونيرة', dateAdded: '2026-03-04T10:15:00' },
  { id: 105748, code: 'ADF00003', name: 'ريد ديليشاز', dateAdded: '2026-03-06T14:30:00' },
  { id: 105749, code: 'ADF00004', name: 'كود كيل/كارولين هريرا', dateAdded: '2026-03-01T09:45:00' },
  { id: 105750, code: 'ADF00005', name: 'المعشوق', dateAdded: '2026-03-05T16:20:00' },
];

export const initialUsersData: UserData[] = [
  { id: 1, fullName: '-', username: 'admine', role: 'مدير', warehouse: '18', dateAdded: '2025-12-18T14:56:32' },
  { id: 2, fullName: 'امير المندوب', username: 'amer', role: 'مستخدم', warehouse: '18', dateAdded: '2025-12-20T05:36:52' },
  { id: 3, fullName: 'محمد وسام', username: 'user2', role: 'مستخدم', warehouse: '10', dateAdded: '2025-12-20T05:36:52' },
  { id: 4, fullName: '-', username: 'user3', role: 'مستخدم', warehouse: '11', dateAdded: '2025-12-20T05:36:52' },
  { id: 5, fullName: 'صالح', username: 'user4', role: 'مستخدم', warehouse: '14', dateAdded: '2025-12-20T05:36:52' },
];

export const initialBarcodesData: BarcodeData[] = [
  { id: 7142, code: 'S01542', name: 'S-1272', barcode: '1001081/', unit: 'كرتون' },
  { id: 7141, code: 'S01542', name: 'S-1272', barcode: '1001081//', unit: 'كرتون' },
  { id: 7140, code: 'S01313', name: 'S-299-600PC', barcode: '100299/', unit: 'كرتون' },
];

export const initialAuditsData: AuditData[] = [
  { id: 19754, code: 'G01350', name: '9 AM - افنان', warehouse: '11', quantity: '5.93', user: 'admine', date: '2026-03-17T08:09:47' },
  { id: 19753, code: 'G00732', name: 'كارتير باشا', warehouse: '11', quantity: '5.04', user: 'admine', date: '2026-03-17T08:07:52' },
  { id: 19752, code: 'G01278', name: 'كريد افينتوس ابسولو الاسود - كريد', warehouse: '11', quantity: '6.57', user: 'admine', date: '2026-03-17T08:07:27' },
];

export const systemStats = [
  { label: 'إجمالي الأصناف', subLabel: 'كل المنتجات المسجلة', value: '11,509', color: 'text-[#3B82F6]', shadowGlow: 'shadow-[0_15px_40px_-15px_rgba(59,130,246,0.25)] hover:shadow-[0_15px_40px_-10px_rgba(59,130,246,0.4)] border-[#3B82F6]/20 hover:border-[#3B82F6]/40', lineIcon: true },
  { label: 'وحدات القياس', subLabel: 'أنواع التعبئة', value: '9', color: 'text-[#C084FC]', shadowGlow: 'shadow-[0_15px_40px_-15px_rgba(192,132,252,0.25)] hover:shadow-[0_15px_40px_-10px_rgba(192,132,252,0.4)] border-[#C084FC]/20 hover:border-[#C084FC]/40', lineIcon: true },
  { label: 'إجمالي الباركودات', subLabel: 'معرفات فريدة', value: '7,142', color: 'text-[#10B981]', shadowGlow: 'shadow-[0_15px_40px_-15px_rgba(16,185,129,0.25)] hover:shadow-[0_15px_40px_-10px_rgba(16,185,129,0.4)] border-[#10B981]/20 hover:border-[#10B981]/40', lineIcon: false },
  { label: 'الجردات المكتملة', subLabel: 'عمليات تمت بنجاح', value: '821', color: 'text-[#F43F5E]', shadowGlow: 'shadow-[0_15px_40px_-15px_rgba(244,63,94,0.25)] hover:shadow-[0_15px_40px_-10px_rgba(244,63,94,0.4)] border-[#F43F5E]/20 hover:border-[#F43F5E]/40', lineIcon: false },
];

export const measurementUnits = [
  { name: 'قطعه', items: '3,183', barcodes: '3,276' },
  { name: 'كغم', items: '1,893', barcodes: '1,944' },
  { name: '0.25 كغم', items: '1,292', barcodes: '1,355' },
  { name: 'كرتون', items: '257', barcodes: '481' },
];
