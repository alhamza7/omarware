const axios = require('axios');
const https = require('https');
const sapConfig = require('./sap_config');

/**
 * SAP B1 Service Layer Client
 * يدير الاتصال والمصادقة مع SAP Business One Service Layer
 */
class SAPClient {
  constructor() {
    this.sessionId = null;
    this.sessionTimeout = null;
    this.baseURL = sapConfig.SAP_SERVICE_LAYER_URL;
    
    // إنشاء axios instance مع تجاهل شهادات SSL (للتطوير فقط)
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 seconds timeout
      httpsAgent: new https.Agent({
        rejectUnauthorized: false, // تحذير: استخدم فقط في بيئة التطوير
        keepAlive: true,
        maxSockets: 10,
        maxFreeSockets: 5,
        timeout: 30000,
        minVersion: 'TLSv1.2', // تحديد الحد الأدنى لإصدار TLS
      }),
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  /**
   * اختبار الاتصال بخادم SAP بدون تسجيل دخول
   */
  async testConnection() {
    if (!sapConfig.SAP_ENABLED) {
      return { success: false, error: 'SAP integration is disabled' };
    }

    try {
      console.log('🔄 Testing connection to SAP server...');
      console.log(`   URL: ${this.baseURL}`);
      
      // محاولة الوصول إلى endpoint بسيط
      const response = await this.client.get('/$metadata', {
        timeout: 10000,
        validateStatus: () => true, // قبول أي رمز حالة
      });
      
      if (response.status === 200 || response.status === 401) {
        console.log('✅ SAP server is reachable');
        return { success: true, message: 'Server is reachable' };
      } else {
        console.log('⚠️ SAP server responded with status:', response.status);
        return { success: false, error: `Server responded with status ${response.status}` };
      }
    } catch (error) {
      let errorMessage = error.message;
      
      if (error.code === 'ECONNREFUSED') {
        errorMessage = 'Connection refused - SAP server is not running or firewall is blocking';
      } else if (error.code === 'ENOTFOUND') {
        errorMessage = 'SAP server hostname not found - check the URL';
      } else if (error.code === 'ETIMEDOUT') {
        errorMessage = 'Connection timed out - server is too slow or unreachable';
      } else if (error.code === 'ECONNRESET') {
        errorMessage = 'Connection was reset - possible SSL/TLS issue';
      } else if (error.message.includes('socket disconnected')) {
        errorMessage = 'TLS handshake failed - SAP server may require specific SSL/TLS version';
      }
      
      console.error('❌ Connection test failed:', errorMessage);
      return { success: false, error: errorMessage, code: error.code };
    }
  }

  /**
   * تسجيل الدخول إلى SAP B1 Service Layer
   */
  async login() {
    if (!sapConfig.SAP_ENABLED) {
      throw new Error('SAP integration is disabled');
    }

    try {
      console.log('🔄 Attempting to login to SAP B1...');
      console.log(`   URL: ${this.baseURL}`);
      console.log(`   Company DB: ${sapConfig.SAP_COMPANY_DB}`);
      
      const response = await this.client.post('/Login', {
        CompanyDB: sapConfig.SAP_COMPANY_DB,
        UserName: sapConfig.SAP_USERNAME,
        Password: sapConfig.SAP_PASSWORD,
      }, {
        timeout: 30000,
      });

      this.sessionId = response.data.SessionId;
      
      // تعيين Session ID في headers
      this.client.defaults.headers.common['Cookie'] = `B1SESSION=${this.sessionId}`;
      
      // إعداد تجديد الجلسة تلقائياً
      this._scheduleSessionRefresh();
      
      console.log('✅ Successfully logged in to SAP B1 Service Layer');
      return this.sessionId;
    } catch (error) {
      let errorMessage = error.message;
      
      if (error.code === 'ECONNREFUSED') {
        errorMessage = 'Connection refused - SAP server is not reachable';
      } else if (error.code === 'ENOTFOUND') {
        errorMessage = 'SAP server hostname not found';
      } else if (error.code === 'ETIMEDOUT') {
        errorMessage = 'Connection timed out';
      } else if (error.code === 'ECONNRESET') {
        errorMessage = 'Connection was reset by SAP server';
      } else if (error.message.includes('socket disconnected')) {
        errorMessage = 'TLS handshake failed - check SAP server SSL/TLS configuration';
      }
      
      console.error('❌ Failed to login to SAP B1:', errorMessage);
      console.error('   Error code:', error.code || 'N/A');
      console.error('   Full error:', error.message);
      
      throw new Error(`SAP Login failed: ${errorMessage}`);
    }
  }

  /**
   * جدولة تجديد الجلسة قبل انتهاء صلاحيتها
   */
  _scheduleSessionRefresh() {
    if (this.sessionTimeout) {
      clearTimeout(this.sessionTimeout);
    }

    // تجديد الجلسة قبل انتهائها بـ 5 دقائق
    const refreshTime = (sapConfig.SAP_SESSION_TIMEOUT - 5) * 60 * 1000;
    this.sessionTimeout = setTimeout(() => {
      console.log('⏰ Session قارب على الانتهاء، إعادة تسجيل الدخول...');
      this.login().catch(err => {
        console.error('❌ فشل تجديد الجلسة:', err.message);
      });
    }, refreshTime);
  }

  /**
   * التأكد من وجود جلسة نشطة
   */
  async ensureLoggedIn() {
    if (!this.sessionId) {
      await this.login();
    }
  }

  /**
   * تسجيل الخروج من SAP B1 Service Layer
   */
  async logout() {
    if (!this.sessionId) return;

    try {
      await this.client.post('/Logout');
      this.sessionId = null;
      if (this.sessionTimeout) {
        clearTimeout(this.sessionTimeout);
        this.sessionTimeout = null;
      }
      console.log('✅ Successfully logged out from SAP B1');
    } catch (error) {
      console.error('❌ Failed to logout from SAP B1:', error.message);
    }
  }

  /**
   * الحصول على كمية الصنف في مخزن محدد
   * @param {string} itemCode - كود الصنف في SAP
   * @param {number} warehouseId - رقم المخزن (1-18)
   * @returns {Promise<{itemCode: string, warehouseCode: string, quantity: number, committed: number, available: number}>}
   */
  async getItemQuantity(itemCode, warehouseId) {
    if (!sapConfig.SAP_ENABLED) {
      return null;
    }

    await this.ensureLoggedIn();

    // تحويل رقم المخزن إلى كود SAP
    const sapWarehouseCode = sapConfig.WAREHOUSE_MAPPING[warehouseId];
    if (!sapWarehouseCode) {
      throw new Error(`Invalid warehouse ID: ${warehouseId}`);
    }

    try {
      // استعلام Service Layer للحصول على كمية الصنف
      // نستخدم Items مع $select و $filter للحصول على معلومات المخزون
      const response = await this.client.get('/Items', {
        params: {
          $filter: `ItemCode eq '${itemCode}'`,
          $select: 'ItemCode,ItemName,ItemWarehouseInfoCollection',
        },
      });

      if (!response.data || !response.data.value || response.data.value.length === 0) {
        return null; // الصنف غير موجود في SAP
      }

      const item = response.data.value[0];
      const warehouseInfo = item.ItemWarehouseInfoCollection || [];
      
      // البحث عن معلومات المخزن المحدد
      const warehouseData = warehouseInfo.find(
        (wh) => wh.WarehouseCode === sapWarehouseCode
      );

      if (!warehouseData) {
        // المخزن موجود لكن الصنف غير مسجل فيه
        return {
          itemCode: item.ItemCode,
          itemName: item.ItemName,
          warehouseCode: sapWarehouseCode,
          quantity: 0,
          committed: 0,
          available: 0,
        };
      }

      return {
        itemCode: item.ItemCode,
        itemName: item.ItemName,
        warehouseCode: sapWarehouseCode,
        quantity: warehouseData.InStock || 0, // الكمية الموجودة
        committed: warehouseData.Committed || 0, // الكمية المحجوزة
        available: (warehouseData.InStock || 0) - (warehouseData.Committed || 0), // الكمية المتاحة
      };
    } catch (error) {
      console.error(`❌ Failed to get item quantity from SAP:`, error.message);
      
      // إذا كانت الجلسة منتهية، نعيد المحاولة مرة واحدة
      if (error.response && error.response.status === 401) {
        this.sessionId = null;
        await this.ensureLoggedIn();
        return this.getItemQuantity(itemCode, warehouseId);
      }
      
      throw error;
    }
  }

  /**
   * البحث عن صنف بالباركود
   * @param {string} barcode - الباركود
   * @param {number} warehouseId - رقم المخزن
   * @returns {Promise<object|null>}
   */
  async getItemByBarcode(barcode, warehouseId) {
    if (!sapConfig.SAP_ENABLED) {
      return null;
    }

    await this.ensureLoggedIn();

    const sapWarehouseCode = sapConfig.WAREHOUSE_MAPPING[warehouseId];
    if (!sapWarehouseCode) {
      throw new Error(`Invalid warehouse ID: ${warehouseId}`);
    }

    try {
      // البحث عن الصنف بالباركود
      const response = await this.client.get('/Items', {
        params: {
          $filter: `BarCode eq '${barcode}'`,
          $select: 'ItemCode,ItemName,BarCode,ItemWarehouseInfoCollection',
        },
      });

      if (!response.data || !response.data.value || response.data.value.length === 0) {
        return null;
      }

      const item = response.data.value[0];
      const warehouseInfo = item.ItemWarehouseInfoCollection || [];
      const warehouseData = warehouseInfo.find(
        (wh) => wh.WarehouseCode === sapWarehouseCode
      );

      return {
        itemCode: item.ItemCode,
        itemName: item.ItemName,
        barcode: item.BarCode,
        warehouseCode: sapWarehouseCode,
        quantity: warehouseData ? (warehouseData.InStock || 0) : 0,
        committed: warehouseData ? (warehouseData.Committed || 0) : 0,
        available: warehouseData 
          ? ((warehouseData.InStock || 0) - (warehouseData.Committed || 0))
          : 0,
      };
    } catch (error) {
      console.error(`❌ Failed to get item by barcode from SAP:`, error.message);
      
      if (error.response && error.response.status === 401) {
        this.sessionId = null;
        await this.ensureLoggedIn();
        return this.getItemByBarcode(barcode, warehouseId);
      }
      
      throw error;
    }
  }

  /**
   * الحصول على جميع المخازن من SAP
   * @returns {Promise<Array>}
   */
  async getWarehouses() {
    if (!sapConfig.SAP_ENABLED) {
      return [];
    }

    await this.ensureLoggedIn();

    try {
      const response = await this.client.get('/Warehouses', {
        params: {
          $select: 'WarehouseCode,WarehouseName,Inactive',
        },
      });

      return (response.data.value || [])
        .filter(wh => !wh.Inactive)
        .map(wh => ({
          code: wh.WarehouseCode,
          name: wh.WarehouseName,
        }));
    } catch (error) {
      console.error(`❌ Failed to get warehouses from SAP:`, error.message);
      throw error;
    }
  }

}

// إنشاء instance واحد للاستخدام في كل التطبيق (Singleton)
const sapClient = new SAPClient();

// تسجيل الخروج عند إيقاف التطبيق
process.on('SIGINT', async () => {
  await sapClient.logout();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await sapClient.logout();
  process.exit(0);
});

module.exports = sapClient;

