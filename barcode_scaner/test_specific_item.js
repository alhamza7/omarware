/**
 * اختبار الصنف G00262 - المشاعر الملتهبة
 * 
 * تشغيل: node test_specific_item.js
 */

require('dotenv').config();
const sapClient = require('./src/sap_client');

async function testSpecificItem() {
  console.log('\n╔════════════════════════════════════════════════════════════╗');
  console.log('║         🧪 اختبار الصنف: G00262                          ║');
  console.log('║         المشاعر الملتهبة - 0.25 كغم                      ║');
  console.log('╚════════════════════════════════════════════════════════════╝\n');

  try {
    // تسجيل الدخول
    console.log('📝 تسجيل الدخول إلى SAP...');
    await sapClient.login();
    console.log('✅ تم تسجيل الدخول بنجاح\n');

    const itemCode = 'G00262';
    
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`🔍 جلب معلومات الصنف: ${itemCode}\n`);

    // Test 1: جلب معلومات الصنف من SAP
    console.log('📦 Test 1: جلب تفاصيل الصنف من SAP...');
    
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

    const itemResponse = await client.get('/Items', {
      params: {
        $filter: `ItemCode eq '${itemCode}'`,
        $select: 'ItemCode,ItemName,BarCode,ItemWarehouseInfoCollection',
      },
    });

    if (!itemResponse.data.value || itemResponse.data.value.length === 0) {
      console.log(`❌ الصنف ${itemCode} غير موجود في SAP`);
      return;
    }

    const item = itemResponse.data.value[0];
    console.log(`✅ تم جلب الصنف بنجاح:`);
    console.log(`   كود الصنف: ${item.ItemCode}`);
    console.log(`   اسم الصنف: ${item.ItemName}`);
    console.log(`   الباركود: ${item.BarCode || 'لا يوجد'}`);
    console.log('');

    // Test 2: عرض الكميات في جميع المخازن
    console.log('📊 Test 2: الكميات في جميع المخازن:');
    console.log('');

    if (item.ItemWarehouseInfoCollection && item.ItemWarehouseInfoCollection.length > 0) {
      let totalQuantity = 0;
      let totalCommitted = 0;
      
      console.log('┌──────────────┬──────────┬──────────┬──────────┐');
      console.log('│   المخزن    │  الموجود │  المحجوز │  المتاح  │');
      console.log('├──────────────┼──────────┼──────────┼──────────┤');
      
      item.ItemWarehouseInfoCollection.forEach(wh => {
        const inStock = wh.InStock || 0;
        const committed = wh.Committed || 0;
        const available = inStock - committed;
        
        totalQuantity += inStock;
        totalCommitted += committed;
        
        console.log(`│ ${wh.WarehouseCode.padEnd(12)} │ ${String(inStock).padStart(8)} │ ${String(committed).padStart(8)} │ ${String(available).padStart(8)} │`);
      });
      
      console.log('├──────────────┼──────────┼──────────┼──────────┤');
      console.log(`│ المجموع      │ ${String(totalQuantity).padStart(8)} │ ${String(totalCommitted).padStart(8)} │ ${String(totalQuantity - totalCommitted).padStart(8)} │`);
      console.log('└──────────────┴──────────┴──────────┴──────────┘');
      console.log('');
    } else {
      console.log('   ⚠️  لا توجد معلومات مخزون لهذا الصنف');
      console.log('');
    }

    // Test 3: استخدام دالة getItemQuantity للمخزن 1
    console.log('📊 Test 3: اختبار getItemQuantity للمخزن 1 (WH01):');
    
    const qty1 = await sapClient.getItemQuantity(itemCode, 1);
    if (qty1) {
      console.log(`✅ نجح!`);
      console.log(`   المخزن: ${qty1.warehouseCode}`);
      console.log(`   الكمية الموجودة: ${qty1.quantity}`);
      console.log(`   الكمية المحجوزة: ${qty1.committed}`);
      console.log(`   الكمية المتاحة: ${qty1.available}`);
      console.log('');
      
      // عرض كيف ستظهر في التطبيق
      console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
      console.log('📱 كيف ستظهر في تطبيق الموبايل:');
      console.log('');
      console.log('╔═══════════════════════════════════════════════════════════╗');
      console.log('║              إضافة كمية                                  ║');
      console.log('╠═══════════════════════════════════════════════════════════╣');
      console.log(`║ ${itemCode} — ${item.ItemName.substring(0, 35).padEnd(35)}           ║`);
      if (item.BarCode) {
        console.log(`║ باركود: ${item.BarCode.padEnd(47)} ║`);
      }
      console.log('╠═══════════════════════════════════════════════════════════╣');
      console.log('║ ☁️  كمية SAP:                                            ║');
      console.log('║ ┌───────────────────────────────────────────────────────┐ ║');
      console.log(`║ │ الكمية الموجودة: ${String(qty1.quantity).padStart(33)} │ ║`);
      console.log(`║ │ الكمية المحجوزة: ${String(qty1.committed).padStart(33)} │ ║`);
      console.log(`║ │ ✅ الكمية المتاحة: ${String(qty1.available).padStart(31)} │ ║`);
      console.log('║ └───────────────────────────────────────────────────────┘ ║');
      console.log('╠═══════════════════════════════════════════════════════════╣');
      console.log('║ الكمية: [____]                                           ║');
      console.log('╠═══════════════════════════════════════════════════════════╣');
      console.log('║  [إلغاء]                                      [حفظ]      ║');
      console.log('╚═══════════════════════════════════════════════════════════╝');
      console.log('');
    } else {
      console.log(`⚠️  الصنف غير موجود في المخزن 1`);
      console.log('');
    }

    // Test 4: إذا كان له باركود، اختبر البحث بالباركود
    if (item.BarCode) {
      console.log(`🔎 Test 4: اختبار البحث بالباركود (${item.BarCode}):`);
      
      const barcodeResult = await sapClient.getItemByBarcode(item.BarCode, 1);
      if (barcodeResult) {
        console.log(`✅ نجح!`);
        console.log(`   كود الصنف: ${barcodeResult.itemCode}`);
        console.log(`   اسم الصنف: ${barcodeResult.itemName}`);
        console.log(`   الباركود: ${barcodeResult.barcode}`);
        console.log(`   الكمية المتاحة: ${barcodeResult.available}`);
      } else {
        console.log(`⚠️  الباركود غير موجود`);
      }
      console.log('');
    }

    // النتيجة النهائية
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║                                                            ║');
    console.log('║              ✅ الاختبار اكتمل بنجاح!                     ║');
    console.log('║                                                            ║');
    if (qty1 && qty1.quantity > 0) {
      console.log('║     🎉 الكمية موجودة في SAP وستظهر في التطبيق! 🎉      ║');
    } else {
      console.log('║     ⚠️  الكمية = 0 لكن الصنف موجود في SAP              ║');
    }
    console.log('║                                                            ║');
    console.log('╚════════════════════════════════════════════════════════════╝');
    console.log('');
    
    console.log('💡 ملاحظات:');
    console.log('   - الكمية من SAP ستظهر تلقائياً عند المسح/البحث');
    console.log('   - لا حاجة لأي إعداد إضافي');
    console.log('   - يعمل مع المسح والبحث اليدوي');
    console.log('');

  } catch (error) {
    console.error('\n❌ خطأ:', error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', JSON.stringify(error.response.data, null, 2));
    }
  } finally {
    await sapClient.logout();
  }
}

testSpecificItem();






