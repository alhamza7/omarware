/**
 * اختبار الاتصال مع SAP B1 Service Layer
 * 
 * تشغيل: node test_sap_connection.js
 */

require('dotenv').config();
const sapClient = require('./src/sap_client');

async function testSAPConnection() {
  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║        🧪 اختبار الاتصال مع SAP B1 Service Layer         ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');

  try {
    // Test 1: تسجيل الدخول
    console.log('📝 Test 1: تسجيل الدخول...');
    const sessionId = await sapClient.login();
    console.log(`✅ نجح! Session ID: ${sessionId.substring(0, 20)}...`);
    console.log('');

    // Test 2: الحصول على قائمة المخازن
    console.log('📦 Test 2: جلب قائمة المخازن...');
    const warehouses = await sapClient.getWarehouses();
    console.log(`✅ تم جلب ${warehouses.length} مخزن:`);
    warehouses.slice(0, 5).forEach(wh => {
      console.log(`   - ${wh.code}: ${wh.name}`);
    });
    if (warehouses.length > 5) {
      console.log(`   ... و ${warehouses.length - 5} مخزن آخر`);
    }
    console.log('');

    // Test 3: جلب أول صنف من SAP
    console.log('🔍 Test 3: جلب أول صنف من SAP...');
    const axios = require('axios');
    const https = require('https');
    
    const client = axios.create({
      baseURL: sapClient.baseURL,
      httpsAgent: new https.Agent({
        rejectUnauthorized: false,
      }),
      headers: {
        'Cookie': `B1SESSION=${sapClient.sessionId}`,
      },
    });

    const itemsResponse = await client.get('/Items', {
      params: {
        $top: 1,
        $select: 'ItemCode,ItemName,ItemWarehouseInfoCollection',
      },
    });

    if (itemsResponse.data.value && itemsResponse.data.value.length > 0) {
      const firstItem = itemsResponse.data.value[0];
      console.log(`✅ تم جلب صنف تجريبي:`);
      console.log(`   كود الصنف: ${firstItem.ItemCode}`);
      console.log(`   اسم الصنف: ${firstItem.ItemName}`);
      
      if (firstItem.ItemWarehouseInfoCollection && firstItem.ItemWarehouseInfoCollection.length > 0) {
        const firstWh = firstItem.ItemWarehouseInfoCollection[0];
        console.log(`   المخزن: ${firstWh.WarehouseCode}`);
        console.log(`   الكمية: ${firstWh.InStock || 0}`);
        console.log(`   المحجوز: ${firstWh.Committed || 0}`);
        console.log(`   المتاح: ${(firstWh.InStock || 0) - (firstWh.Committed || 0)}`);
      }
      console.log('');

      // Test 4: استخدام دالة getItemQuantity
      console.log('📊 Test 4: اختبار getItemQuantity...');
      const itemCode = firstItem.ItemCode;
      const quantity = await sapClient.getItemQuantity(itemCode, 1);
      if (quantity) {
        console.log(`✅ نجح! البيانات:`);
        console.log(`   كود الصنف: ${quantity.itemCode}`);
        console.log(`   المخزن: ${quantity.warehouseCode}`);
        console.log(`   الكمية: ${quantity.quantity}`);
        console.log(`   المحجوز: ${quantity.committed}`);
        console.log(`   المتاح: ${quantity.available}`);
      }
    }
    console.log('');

    // Test 5: البحث عن صنف بباركود (اختياري)
    console.log('🔎 Test 5: اختبار البحث بالباركود...');
    try {
      const barcodeResult = await client.get('/Items', {
        params: {
          $top: 1,
          $filter: "BarCode ne null and BarCode ne ''",
          $select: 'ItemCode,ItemName,BarCode',
        },
      });

      if (barcodeResult.data.value && barcodeResult.data.value.length > 0) {
        const itemWithBarcode = barcodeResult.data.value[0];
        console.log(`✅ وجدنا صنف بباركود:`);
        console.log(`   الباركود: ${itemWithBarcode.BarCode}`);
        console.log(`   الكود: ${itemWithBarcode.ItemCode}`);
        console.log(`   الاسم: ${itemWithBarcode.ItemName}`);
      } else {
        console.log(`⚠️  لم نجد أصناف بباركود في SAP`);
      }
    } catch (e) {
      console.log(`⚠️  خطأ في البحث عن الباركود: ${e.message}`);
    }
    console.log('');

    // النتيجة النهائية
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║                                                            ║');
    console.log('║              ✅ جميع الاختبارات نجحت!                     ║');
    console.log('║                                                            ║');
    console.log('║        🎉 التكامل مع SAP يعمل بشكل ممتاز! 🎉            ║');
    console.log('║                                                            ║');
    console.log('╚════════════════════════════════════════════════════════════╝');
    console.log('');
    console.log('💡 ملاحظة: Session ID يُحفظ ويُستخدم في جميع الطلبات');
    console.log('           لا حاجة لتسجيل الدخول مرة أخرى!');
    console.log('');

  } catch (error) {
    console.error('\n❌ فشل الاختبار:');
    console.error(`   الخطأ: ${error.message}`);
    
    if (error.response) {
      console.error(`   Status: ${error.response.status}`);
      console.error(`   Data: ${JSON.stringify(error.response.data, null, 2)}`);
    }
    
    console.log('\n🔧 تحقق من:');
    console.log('   1. عنوان Service Layer صحيح');
    console.log('   2. اسم قاعدة البيانات صحيح');
    console.log('   3. اسم المستخدم وكلمة المرور صحيحين');
    console.log('   4. الشبكة تسمح بالاتصال بالمنفذ 50000');
    console.log('   5. SAP Service Layer يعمل');
    
    process.exit(1);
  } finally {
    // تسجيل الخروج
    await sapClient.logout();
  }
}

// تشغيل الاختبار
testSAPConnection();






