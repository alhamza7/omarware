import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'config.dart';

class ApiClient {
  ApiClient(this._storage) {
    _dio = Dio(BaseOptions(baseUrl: AppConfig.baseUrl));
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          final token = await _storage.read(key: 'token');
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
      ),
    );
  }

  final FlutterSecureStorage _storage;
  late final Dio _dio;

  Future<(String token, int warehouseId)> login({
    required String username,
    required String password,
  }) async {
    final r = await _dio.post<Map<String, dynamic>>(
      '/api/auth/login',
      data: {'username': username, 'password': password},
    );
    final data = r.data ?? {};
    final token = (data['token'] ?? '').toString();
    final wh = (data['warehouse_id'] is num) ? (data['warehouse_id'] as num).toInt() : 1;
    if (token.isEmpty) throw Exception('no token');
    await _storage.write(key: 'token', value: token);
    await _storage.write(key: 'warehouse_id', value: wh.toString());
    return (token, wh);
  }

  Future<int> getWarehouse() async {
    final r = await _dio.get<Map<String, dynamic>>('/api/me');
    final data = r.data ?? {};
    final wh = (data['warehouse_id'] is num) ? (data['warehouse_id'] as num).toInt() : 1;
    await _storage.write(key: 'warehouse_id', value: wh.toString());
    return wh;
  }

  Future<int> setWarehouse(int warehouseId) async {
    final r = await _dio.post<Map<String, dynamic>>(
      '/api/me/warehouse',
      data: {'warehouse_id': warehouseId},
    );
    final data = r.data ?? {};
    final wh = (data['warehouse_id'] is num) ? (data['warehouse_id'] as num).toInt() : warehouseId;
    await _storage.write(key: 'warehouse_id', value: wh.toString());
    return wh;
  }

  Future<Map<String, dynamic>> getItemByCode(String code) async {
    final r = await _dio.get<Map<String, dynamic>>('/api/items/by-code/$code');
    return r.data ?? {};
  }

  Future<void> saveCount({
    required int itemId,
    required num qty,
    String? note,
  }) async {
    final whStr = await _storage.read(key: 'warehouse_id');
    final wh = int.tryParse(whStr ?? '') ?? 1;
    // في السيرفر: المخزن يُقرأ من user، لكن نخزن محلياً أيضاً.
    await _dio.post(
      '/api/counts',
      data: {'item_id': itemId, 'qty': qty, 'note': note},
      options: Options(headers: {'X-Warehouse': wh}),
    );
  }

  Future<void> logout() async {
    await _storage.delete(key: 'token');
  }
}












