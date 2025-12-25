/**
 * اختبار جلب أصناف حقيقية من SAP
 * 
 * تشغيل: node test_real_items.js
 */

require('dotenv').config();
const sapClient = require('./src/sap_client');

async function testRealItems() {
  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║           🔍 اختبار جلب أصناف حقيقية من SAP              ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');

  try {
    // تسجيل الدخول
    console.log('📝 تسجيل الدخول...');
    await sapClient.login();
    console.log('✅ تم تسجيل الدخول بنجاح\n');

    // الصنف الذي وجدناه في الاختبار السابق
    const testItems = [
      { code: 'MA00124', name: 'W3' },
      { code: 'S00737', barcode: '100527', name: 'S-527' }
    ];

    console.log('📦 اختبار الأصناف:\n');

    for (const item of testItems) {
      console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
      console.log(`🔍 الصنف: ${item.code} (${item.name})`);
      if (item.barcode) {
        console.log(`📱 الباركود: ${item.barcode}`);
      }
      console.log('');

      try {
        // Test 1: جلب بكود الصنف
        console.log('   📊 جلب الكميات من جميع المخازن:');
        const qty = await sapClient.getItemQuantity(item.code, 1); // المخزن 1
        
        if (qty) {
          console.log(`   ✅ نجح!`);
          console.log(`      المخزن: ${qty.warehouseCode}`);
          console.log(`      الكمية الموجودة: ${qty.quantity}`);
          console.log(`      المحجوز: ${qty.committed}`);
          console.log(`      المتاح: ${qty.available}`);
        } else {
          console.log(`   ⚠️  الصنف غير موجود في المخزن 1`);
        }
        console.log('');

        // Test 2: إذا كان له باركود، جرب البحث بالباركود
        if (item.barcode) {
          console.log('   🔎 جلب بالباركود:');
          const barcodeResult = await sapClient.getItemByBarcode(item.barcode, 1);
          
          if (barcodeResult) {
            console.log(`   ✅ نجح!`);
            console.log(`      كود الصنف: ${barcodeResult.itemCode}`);
            console.log(`      اسم الصنف: ${barcodeResult.itemName}`);
            console.log(`      الكمية المتاحة: ${barcodeResult.available}`);
          } else {
            console.log(`   ⚠️  الباركود غير موجود`);
          }
          console.log('');
        }

      } catch (error) {
        console.log(`   ❌ خطأ: ${error.message}`);
        console.log('');
      }
    }

    // اختبار إضافي: جلب أول 10 أصناف مع باركود
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('📋 قائمة أول 10 أصناف لها باركود في SAP:\n');

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
        $top: 10,
        $filter: "BarCode ne null and BarCode ne ''",
        $select: 'ItemCode,ItemName,BarCode',
      },
    });

    if (itemsResponse.data.value && itemsResponse.data.value.length > 0) {
      itemsResponse.data.value.forEach((item, index) => {
        console.log(`${index + 1}. ${item.ItemCode} - ${item.ItemName}`);
        console.log(`   الباركود: ${item.BarCode}`);
      });
    } else {
      console.log('لا توجد أصناف بباركود');
    }

    console.log('\n╔════════════════════════════════════════════════════════════╗');
    console.log('║                                                            ║');
    console.log('║              ✅ الاختبار اكتمل بنجاح!                     ║');
    console.log('║                                                            ║');
    console.log('╚════════════════════════════════════════════════════════════╝');
    console.log('');
    console.log('💡 نصيحة: استخدم هذه الأكواد والباركودات في اختبار التطبيق');
    console.log('');

  } catch (error) {
    console.error('\n❌ خطأ:', error.message);
    if (error.response) {
      console.error('Response:', error.response.data);
    }
  } finally {
    await sapClient.logout();
  }
}

testRealItems();






