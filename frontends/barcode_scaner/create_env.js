// سكريبت لإنشاء ملف .env تلقائياً
const fs = require('fs');
const path = require('path');

const envContent = `# ============================================
# تكوين SAP Business One Service Layer
# ============================================

# تفعيل/تعطيل التكامل مع SAP
# true = مفعل | false = معطل
SAP_ENABLED=true

# عنوان SAP Service Layer
# تأكد من استخدام العنوان الصحيح لخادم SAP
SAP_SERVICE_LAYER_URL=https://192.168.15.50:50000/b1s/v1

# اسم قاعدة بيانات الشركة في SAP
# يجب أن يكون مطابقاً تماماً للاسم في SAP
SAP_COMPANY_DB=NBS_LIVE_NEW

# بيانات الدخول إلى SAP
# استخدم حساب له صلاحيات الوصول إلى Service Layer
SAP_USERNAME=manager
SAP_PASSWORD=na54321

# ============================================
# مطابقة المخازن (اختياري)
# ============================================
# إذا كانت أكواد المخازن في SAP مختلفة، عدّلها هنا

SAP_WH_01=01
SAP_WH_02=02
SAP_WH_03=03
SAP_WH_04=04
SAP_WH_05=05
SAP_WH_06=06
SAP_WH_07=07
SAP_WH_08=08
SAP_WH_09=09
SAP_WH_10=10
SAP_WH_11=11
SAP_WH_12=12
SAP_WH_13=13
SAP_WH_14=14
SAP_WH_15=15
SAP_WH_16=16
SAP_WH_17=17
SAP_WH_18=18
`;

const envPath = path.join(__dirname, '.env');

try {
  if (fs.existsSync(envPath)) {
    console.log('⚠️  ملف .env موجود بالفعل');
    console.log('   المسار:', envPath);
    console.log('');
    console.log('📝 المحتوى الحالي:');
    console.log(fs.readFileSync(envPath, 'utf8'));
    console.log('');
    
    const readline = require('readline').createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    readline.question('❓ هل تريد استبداله؟ (yes/no): ', (answer) => {
      if (answer.toLowerCase() === 'yes' || answer.toLowerCase() === 'y') {
        fs.writeFileSync(envPath, envContent, 'utf8');
        console.log('✅ تم استبدال ملف .env بنجاح!');
        console.log('   المسار:', envPath);
      } else {
        console.log('❌ تم الإلغاء. الملف القديم محفوظ.');
      }
      readline.close();
    });
  } else {
    fs.writeFileSync(envPath, envContent, 'utf8');
    console.log('✅ تم إنشاء ملف .env بنجاح!');
    console.log('   المسار:', envPath);
    console.log('');
    console.log('📋 الخطوات التالية:');
    console.log('   1. راجع الملف .env وتأكد من الإعدادات');
    console.log('   2. عدّل عنوان SAP إذا كان مختلفاً');
    console.log('   3. عدّل بيانات الدخول');
    console.log('   4. شغّل السيرفر: node src/server.js');
    console.log('   5. اختبر الاتصال من لوحة التحكم');
  }
} catch (error) {
  console.error('❌ خطأ:', error.message);
  console.log('');
  console.log('💡 الحل البديل:');
  console.log('   1. أنشئ ملف جديد اسمه .env في المجلد الرئيسي');
  console.log('   2. انسخ المحتوى التالي:');
  console.log('');
  console.log(envContent);
}


