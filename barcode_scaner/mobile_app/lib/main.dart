import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'api.dart';
import 'screens/inventory_screen.dart';
import 'screens/login_screen.dart';
import 'screens/warehouse_screen.dart';

void main() {
  runApp(const App());
}

class App extends StatefulWidget {
  const App({super.key});

  @override
  State<App> createState() => _AppState();
}

class _AppState extends State<App> {
  final _storage = const FlutterSecureStorage();
  late final ApiClient _api = ApiClient(_storage);
  late Future<bool> _hasToken = _storage.read(key: 'token').then((v) => (v ?? '').isNotEmpty);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Inventory',
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue), useMaterial3: true),
      home: FutureBuilder<bool>(
        future: _hasToken,
        builder: (context, snap) {
          if (!snap.hasData) return const Scaffold(body: Center(child: CircularProgressIndicator()));
          if (snap.data == true) return WarehouseScreen(api: _api);
          return LoginScreen(
            api: _api,
            onLoggedIn: () => setState(() => _hasToken = Future.value(true)),
          );
        },
      ),
      routes: {
        '/login': (_) => LoginScreen(
              api: _api,
              onLoggedIn: () => setState(() => _hasToken = Future.value(true)),
            ),
        '/warehouse': (_) => WarehouseScreen(api: _api),
        '/inventory': (_) => InventoryScreen(api: _api),
      },
    );
  }
}












