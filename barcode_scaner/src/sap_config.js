// تكوين SAP Business One Service Layer
// يرجى تعديل هذه الإعدادات حسب بيئتك

module.exports = {
  // عنوان Service Layer
  SAP_SERVICE_LAYER_URL: process.env.SAP_SERVICE_LAYER_URL || 'https://192.168.15.50:50000/b1s/v1',
  
  // بيانات الدخول
  SAP_COMPANY_DB: process.env.SAP_COMPANY_DB || 'NBS_LIVE_NEW',
  SAP_USERNAME: process.env.SAP_USERNAME || 'manager',
  SAP_PASSWORD: process.env.SAP_PASSWORD || 'na54321',
  
  // إعدادات إضافية
  SAP_SESSION_TIMEOUT: 30, // دقيقة
  SAP_ENABLED: process.env.SAP_ENABLED === 'true' || true, // تمكين/تعطيل التكامل
  
  // تحديد اسم حقل المخزن في SAP (يمكن تعديله حسب إعداداتك)
  SAP_WAREHOUSE_FIELD: 'WhsCode', // حقل كود المخزن في SAP
  
  // مطابقة أرقام المخازن بين النظام و SAP
  // مثال: المخزن رقم 1 في النظام = "01" في SAP
  WAREHOUSE_MAPPING: {
    1: process.env.SAP_WH_01 || '01',
    2: process.env.SAP_WH_02 || '02',
    3: process.env.SAP_WH_03 || '03',
    4: process.env.SAP_WH_04 || '04',
    5: process.env.SAP_WH_05 || '05',
    6: process.env.SAP_WH_06 || '06',
    7: process.env.SAP_WH_07 || '07',
    8: process.env.SAP_WH_08 || '08',
    9: process.env.SAP_WH_09 || '09',
    10: process.env.SAP_WH_10 || '10',
    11: process.env.SAP_WH_11 || '11',
    12: process.env.SAP_WH_12 || '12',
    13: process.env.SAP_WH_13 || '13',
    14: process.env.SAP_WH_14 || '14',
    15: process.env.SAP_WH_15 || '15',
    16: process.env.SAP_WH_16 || '16',
    17: process.env.SAP_WH_17 || '17',
    18: process.env.SAP_WH_18 || '18',
  },
};

