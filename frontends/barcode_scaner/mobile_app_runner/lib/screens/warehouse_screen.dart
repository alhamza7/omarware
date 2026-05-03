import 'package:flutter/material.dart';

import '../api.dart';

class WarehouseScreen extends StatefulWidget {
  const WarehouseScreen({super.key, required this.api});

  final ApiClient api;

  @override
  State<WarehouseScreen> createState() => _WarehouseScreenState();
}

class _WarehouseScreenState extends State<WarehouseScreen> {
  int? _current;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    try {
      final wh = await widget.api.getWarehouse();
      setState(() => _current = wh);
    } catch (_) {
      // ignore
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _select(int wh) async {
    setState(() => _loading = true);
    try {
      final newWh = await widget.api.setWarehouse(wh);
      setState(() => _current = newWh);
      if (mounted) Navigator.of(context).pushReplacementNamed('/inventory');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('اختيار المخزن ${_current != null ? "(الحالي: $_current)" : ""}'),
        actions: [
          IconButton(
            onPressed: () async {
              await widget.api.logout();
              if (context.mounted) Navigator.of(context).pushReplacementNamed('/login');
            },
            icon: const Icon(Icons.logout),
          )
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : GridView.count(
              crossAxisCount: 3,
              padding: const EdgeInsets.all(16),
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              children: [
                for (var i = 1; i <= 18; i++)
                  FilledButton(
                    onPressed: () => _select(i),
                    style: FilledButton.styleFrom(
                      backgroundColor: (_current == i) ? Colors.blue : null,
                    ),
                    child: Text('مخزن $i'),
                  ),
              ],
            ),
    );
  }
}


