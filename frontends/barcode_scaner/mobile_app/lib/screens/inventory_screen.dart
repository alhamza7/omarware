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
  final _scanner = MobileScannerController(detectionSpeed: DetectionSpeed.noDuplicates);
  bool _paused = false;
  String? _status;

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_paused) return;
    final raw = capture.barcodes.first.rawValue?.trim();
    if (raw == null || raw.isEmpty) return;

    setState(() {
      _paused = true;
      _status = 'تمت القراءة: $raw';
    });

    try {
      final data = await widget.api.getItemByCode(Uri.encodeComponent(raw));
      final item = (data['item'] as Map?)?.cast<String, dynamic>();
      if (item == null) throw Exception('not found');

      final itemId = (item['id'] as num).toInt();
      final code = item['item_code']?.toString() ?? '';
      final name = item['item_name']?.toString() ?? '';

      final qty = await _qtyDialog(code: code, name: name);
      if (qty == null) {
        _resumeSoon();
        return;
      }

      await widget.api.saveCount(itemId: itemId, qty: qty);
      _resumeSoon();
    } catch {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('باركود غير موجود أو خطأ اتصال')),
        );
      }
      _resumeSoon();
    }
  }

  void _resumeSoon() {
    Future.delayed(const Duration(milliseconds: 250), () {
      if (!mounted) return;
      setState(() {
        _paused = false;
        _status = null;
      });
    });
  }

  Future<double?> _qtyDialog({required String code, required String name}) async {
    final c = TextEditingController();
    final r = await showDialog<double>(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('إضافة كمية'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('$code — $name', textAlign: TextAlign.center),
              const SizedBox(height: 12),
              TextField(
                controller: c,
                autofocus: true,
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                decoration: const InputDecoration(labelText: 'الكمية'),
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

  @override
  void dispose() {
    _scanner.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('الجرد (Scan-first)'),
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
          Expanded(
            child: Stack(
              children: [
                MobileScanner(
                  controller: _scanner,
                  onDetect: _onDetect,
                ),
                if (_paused)
                  Container(
                    color: Colors.black45,
                    alignment: Alignment.center,
                    child: const CircularProgressIndicator(),
                  ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    _status ?? 'وجّه الكاميرا إلى الباركود…',
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            ),
          )
        ],
      ),
    );
  }
}












