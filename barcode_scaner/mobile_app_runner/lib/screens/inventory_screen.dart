import 'dart:async';

import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../api.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key, required this.api});
  final ApiClient api;

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  final _scanner = MobileScannerController(
    // أسرع سرعة كشف ممكنة
    detectionSpeed: DetectionSpeed.noDuplicates,
    // تقليل timeout للسرعة
    detectionTimeoutMs: 250,
    facing: CameraFacing.back,
    torchEnabled: false,
    // عدم إرجاع صورة لتسريع المعالجة
    returnImage: false,
    // دعم جميع أنواع الباركود والـ QR
    formats: [
      BarcodeFormat.qrCode,        // QR Code
      BarcodeFormat.ean13,         // EAN-13
      BarcodeFormat.ean8,          // EAN-8
      BarcodeFormat.code128,       // Code 128
      BarcodeFormat.code39,        // Code 39
      BarcodeFormat.code93,        // Code 93
      BarcodeFormat.codabar,       // Codabar
      BarcodeFormat.dataMatrix,    // Data Matrix
      BarcodeFormat.pdf417,        // PDF417
      BarcodeFormat.aztec,         // Aztec
      BarcodeFormat.upcA,          // UPC-A
      BarcodeFormat.upcE,          // UPC-E
      BarcodeFormat.itf,           // ITF
    ],
    // دقة عالية للكاميرا
    useNewCameraSelector: true,
  );
  bool _paused = false;
  String? _status;
  bool _torchEnabled = false;
  String _username = ''; // اسم المستخدم
  
  // منع التكرار بنظام أذكى
  String? _lastScannedCode;
  DateTime _lastScanTime = DateTime.now();
  int _scanCount = 0; // عداد للنجاحات المتتالية
  
  // البحث اليدوي
  final _searchController = TextEditingController();
  Timer? _searchDebounce;
  List<Map<String, dynamic>> _searchResults = [];
  bool _searching = false;

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_paused) return;
    
    // معالجة ذكية: محاولة قراءة أي باركود من القائمة
    String? raw;
    BarcodeFormat? format;
    
    for (final barcode in capture.barcodes) {
      final value = barcode.rawValue?.trim();
      if (value != null && value.isNotEmpty) {
        raw = value;
        format = barcode.format;
        break;
      }
    }
    
    if (raw == null || raw.isEmpty) return;
    
    // نظام ذكي لمنع التكرار مع السماح بإعادة المسح السريع إذا لزم الأمر
    final now = DateTime.now();
    final timeDiff = now.difference(_lastScanTime).inMilliseconds;
    
    if (_lastScannedCode == raw && timeDiff < 800) {
      // نفس الكود في أقل من 0.8 ثانية - تجاهل
      return;
    }
    
    // تنظيف الكود (إزالة مسافات زائدة، تصحيح أخطاء شائعة)
    raw = _cleanAndValidateBarcode(raw);
    if (raw.isEmpty) return;
    
    _lastScannedCode = raw;
    _lastScanTime = now;
    _scanCount++;

    setState(() {
      _paused = true;
      _status = 'تمت القراءة: $raw ${_getBarcodeTypeName(format)}';
    });

    try {
      final data = await widget.api.getItemByCode(Uri.encodeComponent(raw));
      final item = (data['item'] as Map?)?.cast<String, dynamic>();
      if (item == null) throw Exception('not found');

      final lastCount = (data['lastCount'] as Map?)?.cast<String, dynamic>();
      final sapQuantity = (data['sapQuantity'] as Map?)?.cast<String, dynamic>();
      final itemId = (item['id'] as num).toInt();
      final barcodeId = item['barcode_id'] != null ? (item['barcode_id'] as num).toInt() : null;
      final code = item['item_code']?.toString() ?? '';
      final name = item['item_name']?.toString() ?? '';
      final barcode = item['barcode']?.toString();
      final uom = item['uom']?.toString();

      // إذا كان مجرود مسبقاً، اعرض دايلوج "تم الجرد - هل تريد التعديل؟"
      double? lastQty;
      if (lastCount != null) {
        final action = await _showAlreadyCountedDialog(
          code: code,
          name: name,
          barcode: barcode,
          uom: uom,
          lastCount: lastCount,
          sapQuantity: sapQuantity,
        );
        if (action == null) {
          _resumeSoon();
          return;
        }
        if (action == 'add') {
          lastQty = double.tryParse(lastCount['qty']?.toString() ?? '0') ?? 0;
        }
      }

      // تحديد نوع الوحدة
      final unitType = _getUnitType(uom);
      
      // اختيار Dialog المناسب
      double? finalQty;
      
      if (unitType != 'default') {
        // استخدام Dialog الوحدات المتعددة
        final result = await _multiUnitDialog(
          code: code,
          name: name,
          unitType: unitType,
          barcode: barcode,
          sapQuantity: sapQuantity,
        );
        
        if (result == null) {
          _resumeSoon();
          return;
        }
        
        finalQty = result['total']!;
        
        // إذا كان في وضع الإضافة، أضف الكمية للكمية السابقة
        if (lastQty != null) {
          finalQty = finalQty + lastQty;
        }
        
        // حفظ الجرد مع تفاصيل الوحدات
        await widget.api.saveCount(
          itemId: itemId,
          qty: finalQty,
          note: null,
          sapQty: sapQuantity?['quantity']?.toDouble(),
          sapCommitted: sapQuantity?['committed']?.toDouble(),
          sapAvailable: sapQuantity?['available']?.toDouble(),
          qtyPieces: result['pieces']!,
          qtyDozen: result['dozen']!,
          qtyCarton: result['carton']!,
        );
        
      } else {
        // استخدام Dialog العادي
        final qty = await _qtyDialog(
          code: code, 
          name: name, 
          barcode: barcode,
          uom: uom,
          addMode: lastQty != null,
          lastQty: lastQty,
          sapQuantity: sapQuantity,
        );
        
        if (qty == null) {
          _resumeSoon();
          return;
        }

        // إذا كان في وضع الإضافة، أضف الكمية للكمية السابقة
        finalQty = lastQty != null ? qty + lastQty : qty;
        
        // حفظ الجرد العادي
        await widget.api.saveCount(
          itemId: itemId,
          qty: finalQty,
          note: null,
          sapQty: sapQuantity?['quantity']?.toDouble(),
          sapCommitted: sapQuantity?['committed']?.toDouble(),
          sapAvailable: sapQuantity?['available']?.toDouble(),
        );
      }

      _resumeSoon();
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('باركود غير موجود أو خطأ اتصال')),
        );
      }
      _resumeSoon();
    }
  }

  void _onSearchChanged(String query) {
    _searchDebounce?.cancel();
    if (query.trim().isEmpty) {
      setState(() {
        _searchResults = [];
        _searching = false;
      });
      return;
    }
    setState(() => _searching = true);
    _searchDebounce = Timer(const Duration(milliseconds: 300), () {
      _performSearch(query.trim());
    });
  }

  Future<void> _performSearch(String query) async {
    try {
      final results = await widget.api.searchItems(query);
      if (!mounted) return;
      setState(() {
        _searchResults = results;
        _searching = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _searchResults = [];
        _searching = false;
      });
    }
  }

  Future<String?> _showAlreadyCountedDialog({
    required String code,
    required String name,
    String? barcode,
    String? uom,
    required Map<String, dynamic> lastCount,
    Map<String, dynamic>? sapQuantity,
  }) async {
    final qty = lastCount['qty']?.toString() ?? '';
    final username = lastCount['username']?.toString() ?? '';
    final createdAt = lastCount['created_at']?.toString() ?? '';
    final note = lastCount['note']?.toString();
    final uomText = uom != null && uom.isNotEmpty ? ' ($uom)' : '';

    return await showDialog<String>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('تم الجرد مسبقاً'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('$code — $name$uomText', style: Theme.of(ctx).textTheme.titleMedium),
              if (barcode != null && barcode.isNotEmpty)
                Text('باركود: $barcode', style: Theme.of(ctx).textTheme.bodySmall),
              const SizedBox(height: 12),
              Text('آخر جرد:', style: Theme.of(ctx).textTheme.labelLarge),
              Text('الكمية: $qty'),
              Text('المستخدم: $username'),
              Text('الوقت: $createdAt'),
              if (note != null && note.isNotEmpty) Text('ملاحظة: $note'),
              // عرض كمية SAP إن وجدت
              if (sapQuantity != null) ...[
                const Divider(height: 24),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue.shade200, width: 2),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.cloud_sync, size: 18, color: Colors.blue.shade700),
                          const SizedBox(width: 6),
                          Text(
                            'كمية SAP الحالية:',
                            style: Theme.of(ctx).textTheme.labelLarge?.copyWith(
                              color: Colors.blue.shade900,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const Divider(height: 16),
                      _buildSAPRow(ctx, 'الكمية الموجودة', sapQuantity['quantity']?.toString() ?? '0', color: Colors.blue),
                      const SizedBox(height: 6),
                      _buildSAPRow(ctx, 'الكمية المحجوزة', sapQuantity['committed']?.toString() ?? '0', color: Colors.orange),
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: Colors.green.shade300, width: 2),
                        ),
                        child: _buildSAPRow(ctx, '✅ الكمية المتاحة', sapQuantity['available']?.toString() ?? '0', 
                          color: Colors.green, isHighlight: true),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 12),
              const Text('هل تريد تعديل أو إضافة كمية؟'),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(null),
              child: const Text('إلغاء'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop('add'),
              style: FilledButton.styleFrom(backgroundColor: Colors.green),
              child: const Text('إضافة كمية إضافية'),
            ),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop('replace'),
              child: const Text('تعديل الكمية'),
            ),
          ],
        );
      },
    );
  }

  Future<void> _onSelectSearchResult(Map<String, dynamic> item) async {
    final itemId = (item['id'] as num).toInt();
    final barcodeId = item['barcode_id'] != null ? (item['barcode_id'] as num).toInt() : null;
    final code = item['item_code']?.toString() ?? '';
    final name = item['item_name']?.toString() ?? '';
    final barcode = item['barcode']?.toString();
    final uom = item['uom']?.toString();
    final lastCount = (item['lastCount'] as Map?)?.cast<String, dynamic>();

    setState(() {
      _searchController.clear();
      _searchResults = [];
    });

    // جلب كمية SAP (إن كان مفعلاً)
    Map<String, dynamic>? sapQuantity;
    try {
      if (barcode != null && barcode.isNotEmpty) {
        sapQuantity = await widget.api.getSAPItemByBarcode(barcode);
      }
      if (sapQuantity == null) {
        sapQuantity = await widget.api.getSAPItemQuantity(code);
      }
    } catch (e) {
      // تجاهل خطأ SAP والاستمرار
    }

    // إذا كان مجرود مسبقاً، اعرض دايلوج "تم الجرد - هل تريد التعديل؟"
    double? lastQty;
    if (lastCount != null) {
      final action = await _showAlreadyCountedDialog(
        code: code,
        name: name,
        barcode: barcode,
        uom: uom,
        lastCount: lastCount,
        sapQuantity: sapQuantity,
      );
      if (action == null) return;
      if (action == 'add') {
        lastQty = double.tryParse(lastCount['qty']?.toString() ?? '0') ?? 0;
      }
    }

    // تحديد نوع الوحدة
    final unitType = _getUnitType(uom);
    
    // اختيار Dialog المناسب
    double? finalQty;
    
    if (unitType != 'default') {
      // استخدام Dialog الوحدات المتعددة
      final result = await _multiUnitDialog(
        code: code,
        name: name,
        unitType: unitType,
        barcode: barcode,
        sapQuantity: sapQuantity,
      );
      
      if (result == null) return;
      
      finalQty = result['total']!;
      
      // إذا كان في وضع الإضافة، أضف الكمية للكمية السابقة
      if (lastQty != null) {
        finalQty = finalQty + lastQty;
      }
      
      // حفظ الجرد مع تفاصيل الوحدات
      try {
        await widget.api.saveCount(
          itemId: itemId,
          qty: finalQty,
          note: null,
          sapQty: sapQuantity?['quantity']?.toDouble(),
          sapCommitted: sapQuantity?['committed']?.toDouble(),
          sapAvailable: sapQuantity?['available']?.toDouble(),
          qtyPieces: result['pieces']!,
          qtyDozen: result['dozen']!,
          qtyCarton: result['carton']!,
        );
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('تم الحفظ بنجاح')),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('خطأ في الحفظ: ${e.toString()}')),
          );
        }
      }
      
    } else {
      // استخدام Dialog العادي
      final qty = await _qtyDialog(
        code: code, 
        name: name, 
        barcode: barcode,
        uom: uom,
        addMode: lastQty != null,
        lastQty: lastQty,
        sapQuantity: sapQuantity,
      );
      
      if (qty == null) return;

      // إذا كان في وضع الإضافة، أضف الكمية للكمية السابقة
      finalQty = lastQty != null ? qty + lastQty : qty;

      try {
        await widget.api.saveCount(
          itemId: itemId,
          qty: finalQty,
          sapQty: sapQuantity?['quantity'],
          sapCommitted: sapQuantity?['committed'],
          sapAvailable: sapQuantity?['available'],
        );
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('تم الحفظ بنجاح')),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('خطأ في الحفظ: ${e.toString()}')),
          );
        }
      }
    }
  }

  void _resumeSoon() {
    Future.delayed(const Duration(milliseconds: 500), () {
      if (!mounted) return;
      setState(() {
        _paused = false;
        _status = null;
      });
    });
  }

  // دالة تنظيف وتصحيح الباركود
  String _cleanAndValidateBarcode(String raw) {
    // إزالة المسافات البيضاء من البداية والنهاية
    String cleaned = raw.trim();
    
    // إزالة مسافات داخلية غير ضرورية
    cleaned = cleaned.replaceAll(RegExp(r'\s+'), '');
    
    // تصحيح أخطاء OCR شائعة في QR codes
    // O -> 0, l -> 1, I -> 1
    // (فقط إذا كان الكود يبدو رقمياً)
    if (RegExp(r'^[A-Z0-9]+$', caseSensitive: false).hasMatch(cleaned)) {
      // لا نصحح تلقائياً لتجنب أخطاء
      // يمكن تفعيل هذا إذا لزم الأمر
    }
    
    // التحقق من الحد الأدنى للطول
    if (cleaned.length < 3) return '';
    
    // التحقق من الحد الأقصى للطول (معظم الباركودات < 100 حرف)
    if (cleaned.length > 100) {
      cleaned = cleaned.substring(0, 100);
    }
    
    return cleaned;
  }

  // دالة للحصول على اسم نوع الباركود
  String _getBarcodeTypeName(BarcodeFormat? format) {
    if (format == null) return '';
    
    switch (format) {
      case BarcodeFormat.qrCode:
        return '(QR)';
      case BarcodeFormat.ean13:
        return '(EAN-13)';
      case BarcodeFormat.ean8:
        return '(EAN-8)';
      case BarcodeFormat.code128:
        return '(Code 128)';
      case BarcodeFormat.code39:
        return '(Code 39)';
      case BarcodeFormat.code93:
        return '(Code 93)';
      case BarcodeFormat.dataMatrix:
        return '(Data Matrix)';
      case BarcodeFormat.pdf417:
        return '(PDF417)';
      case BarcodeFormat.aztec:
        return '(Aztec)';
      case BarcodeFormat.upcA:
        return '(UPC-A)';
      case BarcodeFormat.upcE:
        return '(UPC-E)';
      case BarcodeFormat.codabar:
        return '(Codabar)';
      case BarcodeFormat.itf:
        return '(ITF)';
      default:
        return '';
    }
  }

  Future<double?> _qtyDialog({
    required String code, 
    required String name, 
    String? barcode,
    String? uom,
    bool addMode = false,
    double? lastQty,
    Map<String, dynamic>? sapQuantity,
  }) async {
    final c = TextEditingController();
    final uomText = uom != null && uom.isNotEmpty ? ' ($uom)' : '';
    final r = await showDialog<double>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        return AlertDialog(
          title: Text(addMode ? 'إضافة كمية إضافية' : 'إضافة كمية'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('$code — $name$uomText', textAlign: TextAlign.center),
              if (barcode != null && barcode.isNotEmpty)
                Text('باركود: $barcode', style: Theme.of(ctx).textTheme.bodySmall),
              if (addMode && lastQty != null)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(
                    'الكمية الحالية: $lastQty',
                    style: Theme.of(ctx).textTheme.bodyMedium?.copyWith(
                      color: Colors.green,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              // عرض كمية SAP إن وجدت
              if (sapQuantity != null) ...[
                const Divider(height: 24),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue.shade200, width: 2),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(Icons.cloud_sync, size: 18, color: Colors.blue.shade700),
                          const SizedBox(width: 6),
                          Text(
                            'كمية SAP الحالية:',
                            style: Theme.of(ctx).textTheme.labelLarge?.copyWith(
                              color: Colors.blue.shade900,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const Divider(height: 16),
                      _buildSAPRow(ctx, 'الكمية الموجودة', sapQuantity['quantity']?.toString() ?? '0', color: Colors.blue),
                      const SizedBox(height: 6),
                      _buildSAPRow(ctx, 'الكمية المحجوزة', sapQuantity['committed']?.toString() ?? '0', color: Colors.orange),
                      const SizedBox(height: 6),
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(6),
                          border: Border.all(color: Colors.green.shade300, width: 2),
                        ),
                        child: _buildSAPRow(ctx, '✅ الكمية المتاحة', sapQuantity['available']?.toString() ?? '0',
                          color: Colors.green, isHighlight: true),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: 12),
              TextField(
                controller: c,
                autofocus: true,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: addMode ? 'الكمية الإضافية' : 'الكمية',
                ),
                onSubmitted: (_) => Navigator.of(ctx).pop(double.tryParse(c.text.trim())),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.of(ctx).pop(null), child: const Text('إلغاء')),
            FilledButton(
              onPressed: () => Navigator.of(ctx).pop(double.tryParse(c.text.trim())),
              child: const Text('حفظ'),
            ),
          ],
        );
      },
    );
    c.dispose();
    return r;
  }

  Widget _buildSAPRow(BuildContext ctx, String label, String value, {bool isSecondary = false, bool isHighlight = false, Color? color}) {
    final MaterialColor effectiveColor = color != null 
      ? (color == Colors.blue ? Colors.blue : color == Colors.orange ? Colors.orange : Colors.green)
      : (isSecondary ? Colors.grey : Colors.blue);
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: Theme.of(ctx).textTheme.bodySmall?.copyWith(
              color: effectiveColor.shade700,
              fontSize: isHighlight ? 14 : 13,
              fontWeight: isHighlight ? FontWeight.bold : FontWeight.normal,
            ),
          ),
          Text(
            value,
            style: Theme.of(ctx).textTheme.bodyMedium?.copyWith(
              fontWeight: isHighlight ? FontWeight.bold : FontWeight.w600,
              color: effectiveColor.shade700,
              fontSize: isHighlight ? 16 : 14,
            ),
          ),
        ],
      ),
    );
  }

  // تحديد نوع الوحدة من UOM
  String _getUnitType(String? uom) {
    if (uom == null || uom.isEmpty) return 'default';
    
    final normalized = uom.toLowerCase().trim();
    
    // قطعة
    if (normalized == 'قطعة' || normalized == 'قطعه' || 
        normalized == 'piece' || normalized == 'pcs') {
      return 'piece';
    }
    
    // باكيت
    if (normalized == 'باكيت' || normalized == 'packet' || normalized == 'pack') {
      return 'packet';
    }
    
    // سيت
    if (normalized == 'سيت' || normalized == 'set') {
      return 'set';
    }
    
    // درزن
    if (normalized == 'درزن' || normalized == 'dozen') {
      return 'dozen';
    }
    
    // كارتون
    if (normalized == 'كارتون' || normalized == 'carton') {
      return 'carton';
    }
    
    return 'default';
  }

  // الحصول على اسم الوحدة بالعربي
  String _getUnitLabel(String unitType) {
    switch (unitType) {
      case 'piece':
        return 'قطعة';
      case 'packet':
        return 'باكيت';
      case 'set':
        return 'سيت';
      case 'dozen':
        return 'درزن';
      case 'carton':
        return 'كارتون';
      default:
        return 'الكمية';
    }
  }

  // Dialog الوحدات المتعددة
  Future<Map<String, double>?> _multiUnitDialog({
    required String code,
    required String name,
    required String unitType,
    String? barcode,
    Map<String, dynamic>? sapQuantity,
  }) async {
    final piecesController = TextEditingController();
    final dozenController = TextEditingController();
    final cartonController = TextEditingController();

    final result = await showDialog<Map<String, double>>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('إضافة كمية'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('$code — $name', textAlign: TextAlign.center),
                if (barcode != null && barcode.isNotEmpty)
                  Text('باركود: $barcode', style: Theme.of(ctx).textTheme.bodySmall),
                
                // عرض كمية SAP إن وجدت
                if (sapQuantity != null) ...[
                  const Divider(height: 24),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.blue.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.blue.shade200, width: 2),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(Icons.cloud_sync, size: 18, color: Colors.blue.shade700),
                            const SizedBox(width: 6),
                            Text(
                              'كمية SAP الحالية:',
                              style: Theme.of(ctx).textTheme.labelLarge?.copyWith(
                                color: Colors.blue.shade900,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        const Divider(height: 16),
                        _buildSAPRow(ctx, 'الكمية الموجودة', sapQuantity['quantity']?.toString() ?? '0', color: Colors.blue),
                        const SizedBox(height: 6),
                        _buildSAPRow(ctx, 'الكمية المحجوزة', sapQuantity['committed']?.toString() ?? '0', color: Colors.orange),
                        const SizedBox(height: 6),
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Colors.green.shade50,
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(color: Colors.green.shade300, width: 2),
                          ),
                          child: _buildSAPRow(ctx, '✅ الكمية المتاحة', sapQuantity['available']?.toString() ?? '0',
                            color: Colors.green, isHighlight: true),
                        ),
                      ],
                    ),
                  ),
                ],

                const SizedBox(height: 16),
                
                // حقل الوحدة الأساسية (قطعة/باكيت/سيت)
                TextField(
                  controller: piecesController,
                  autofocus: true,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: _getUnitLabel(unitType),
                    prefixIcon: const Icon(Icons.inventory_2),
                    border: const OutlineInputBorder(),
                  ),
                ),
                
                const SizedBox(height: 12),
                
                // حقل الدرزن
                TextField(
                  controller: dozenController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'درزن',
                    prefixIcon: Icon(Icons.grid_view),
                    border: OutlineInputBorder(),
                  ),
                ),
                
                const SizedBox(height: 12),
                
                // حقل الكارتون
                TextField(
                  controller: cartonController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(
                    labelText: 'كارتون',
                    prefixIcon: Icon(Icons.all_inbox),
                    border: OutlineInputBorder(),
                  ),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(ctx).pop(null),
              child: const Text('إلغاء'),
            ),
            FilledButton(
              onPressed: () {
                final pieces = double.tryParse(piecesController.text) ?? 0;
                final dozen = double.tryParse(dozenController.text) ?? 0;
                final carton = double.tryParse(cartonController.text) ?? 0;
                
                if (pieces <= 0 && dozen <= 0 && carton <= 0) {
                  ScaffoldMessenger.of(ctx).showSnackBar(
                    const SnackBar(content: Text('يجب إدخال كمية واحدة على الأقل')),
                  );
                  return;
                }
                
                Navigator.of(ctx).pop({
                  'pieces': pieces,
                  'dozen': dozen,
                  'carton': carton,
                  'total': pieces, // نحفظ القطع كإجمالي
                });
              },
              child: const Text('حفظ'),
            ),
          ],
        );
      },
    );

    piecesController.dispose();
    dozenController.dispose();
    cartonController.dispose();

    return result;
  }

  @override
  void initState() {
    super.initState();
    _searchController.addListener(() => _onSearchChanged(_searchController.text));
    _loadUsername();
  }

  Future<void> _loadUsername() async {
    try {
      final userInfo = await widget.api.getUserInfo();
      if (mounted) {
        setState(() {
          _username = userInfo['username']?.toString() ?? '';
        });
      }
    } catch (e) {
      // تجاهل الخطأ
    }
  }

  @override
  void dispose() {
    _searchDebounce?.cancel();
    _searchController.dispose();
    _scanner.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Text('الجرد'),
            if (_username.isNotEmpty) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.white.withOpacity(0.2),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.person, size: 16),
                    const SizedBox(width: 4),
                    Text(
                      _username,
                      style: const TextStyle(fontSize: 14),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
        actions: [
          IconButton(
            onPressed: () => Navigator.of(context).pushReplacementNamed('/warehouse'),
            icon: const Icon(Icons.store),
          ),
          IconButton(
            onPressed: () async {
              await widget.api.logout();
              if (context.mounted) Navigator.of(context).pushReplacementNamed('/login');
            },
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: Column(
        children: [
          // النصف العلوي: البحث اليدوي
          Container(
            height: MediaQuery.of(context).size.height * 0.5,
            padding: const EdgeInsets.all(12),
            child: Column(
              children: [
                TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    labelText: 'بحث يدوي (كود / باركود / اسم)',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear),
                            onPressed: () {
                              _searchController.clear();
                              setState(() => _searchResults = []);
                            },
                          )
                        : null,
                    border: const OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 8),
                Expanded(
                  child: _searching
                      ? const Center(child: CircularProgressIndicator())
                      : _searchResults.isEmpty
                          ? Center(
                              child: Text(
                                _searchController.text.isEmpty
                                    ? 'ابدأ بالبحث...'
                                    : 'لا توجد نتائج',
                                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                      color: Colors.grey,
                                    ),
                              ),
                            )
                          : ListView.builder(
                              itemCount: _searchResults.length,
                              itemBuilder: (ctx, idx) {
                                final item = _searchResults[idx];
                                final code = item['item_code']?.toString() ?? '';
                                final name = item['item_name']?.toString() ?? '';
                                final barcode = item['barcode']?.toString();
                                final uom = item['uom']?.toString();
                                
                                // بناء نص العرض
                                String displayName = name;
                                if (uom != null && uom.isNotEmpty) {
                                  displayName += ' ($uom)';
                                }
                                
                                return Card(
                                  margin: const EdgeInsets.only(bottom: 8),
                                  child: ListTile(
                                    title: Text(code),
                                    subtitle: Text(displayName),
                                    trailing: barcode != null
                                        ? Chip(
                                            label: Text('باركود: $barcode', style: const TextStyle(fontSize: 11)),
                                            padding: EdgeInsets.zero,
                                          )
                                        : null,
                                    onTap: () => _onSelectSearchResult(item),
                                  ),
                                );
                              },
                            ),
                ),
              ],
            ),
          ),
          const Divider(height: 1),
          // النصف السفلي: الماسح المحسّن
          Expanded(
            child: Stack(
              children: [
                MobileScanner(
                  controller: _scanner,
                  onDetect: _onDetect,
                ),
                // إطار التوجيه البصري
                Center(
                  child: Container(
                    width: 250,
                    height: 250,
                    decoration: BoxDecoration(
                      border: Border.all(
                        color: _paused ? Colors.green : Colors.blue,
                        width: 3,
                      ),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: _paused
                        ? null
                        : Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(
                                Icons.qr_code_scanner,
                                color: Colors.white.withOpacity(0.8),
                                size: 80,
                              ),
                              const SizedBox(height: 8),
                              Text(
                                'وجّه الكاميرا للكود',
                                style: TextStyle(
                                  color: Colors.white.withOpacity(0.9),
                                  fontSize: 14,
                                  fontWeight: FontWeight.bold,
                                  shadows: [
                                    Shadow(
                                      color: Colors.black.withOpacity(0.8),
                                      blurRadius: 4,
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                  ),
                ),
                // زر الفلاش في الأعلى
                Positioned(
                  top: 16,
                  right: 16,
                  child: FloatingActionButton(
                    mini: true,
                    backgroundColor: _torchEnabled ? Colors.yellow : Colors.black54,
                    onPressed: () {
                      setState(() {
                        _torchEnabled = !_torchEnabled;
                      });
                      _scanner.toggleTorch();
                    },
                    child: Icon(
                      _torchEnabled ? Icons.flash_on : Icons.flash_off,
                      color: Colors.white,
                    ),
                  ),
                ),
                // مؤشر المعالجة
                if (_paused)
                  Container(
                    color: Colors.black45,
                    alignment: Alignment.center,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const CircularProgressIndicator(
                          color: Colors.green,
                          strokeWidth: 5,
                        ),
                        const SizedBox(height: 16),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 24,
                            vertical: 12,
                          ),
                          decoration: BoxDecoration(
                            color: Colors.green,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Text(
                            '✓ تمت القراءة بنجاح',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: _paused ? Colors.green.shade50 : Colors.blue.shade50,
              border: Border(
                top: BorderSide(
                  color: _paused ? Colors.green : Colors.blue,
                  width: 2,
                ),
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  _paused ? Icons.check_circle : Icons.camera_alt,
                  color: _paused ? Colors.green : Colors.blue,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    _status ?? 'وجّه الكاميرا إلى الباركود أو QR Code',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      color: _paused ? Colors.green.shade900 : Colors.blue.shade900,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}


