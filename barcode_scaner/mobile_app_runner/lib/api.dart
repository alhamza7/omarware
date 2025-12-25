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

  Future<Map<String, dynamic>?> getSAPItemQuantity(String itemCode) async {
    try {
      final r = await _dio.get<Map<String, dynamic>>('/api/sap/item-quantity/$itemCode');
      final data = r.data ?? {};
      if (data['ok'] == true && data['data'] != null) {
        return data['data'] as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      // SAP غير مفعل أو حدث خطأ
      return null;
    }
  }

  Future<Map<String, dynamic>?> getSAPItemByBarcode(String barcode) async {
    try {
      final r = await _dio.get<Map<String, dynamic>>('/api/sap/item-by-barcode/$barcode');
      final data = r.data ?? {};
      if (data['ok'] == true && data['data'] != null) {
        return data['data'] as Map<String, dynamic>;
      }
      return null;
    } catch (e) {
      // SAP غير مفعل أو حدث خطأ
      return null;
    }
  }

  Future<Map<String, dynamic>> getSAPStatus() async {
    try {
      final r = await _dio.get<Map<String, dynamic>>('/api/sap/status');
      return r.data ?? {'enabled': false, 'connected': false};
    } catch (e) {
      return {'enabled': false, 'connected': false};
    }
  }

  Future<List<Map<String, dynamic>>> searchItems(String query) async {
    final r = await _dio.get<Map<String, dynamic>>(
      '/api/items/search',
      queryParameters: {'q': query},
    );
    final data = r.data ?? {};
    final items = (data['items'] as List?)?.cast<Map<String, dynamic>>() ?? [];
    return items;
  }

  Future<void> saveCount({
    required int itemId,
    required num qty,
    String? note,
    num? sapQty,
    num? sapCommitted,
    num? sapAvailable,
    num? qtyPieces,
    num? qtyDozen,
    num? qtyCarton,
  }) async {
    final whStr = await _storage.read(key: 'warehouse_id');
    final wh = int.tryParse(whStr ?? '') ?? 1;
    // في السيرفر: المخزن يُقرأ من user، لكن نخزن محلياً أيضاً.
    await _dio.post(
      '/api/counts',
      data: {
        'item_id': itemId,
        'qty': qty,
        'note': note,
        if (sapQty != null) 'sap_qty': sapQty,
        if (sapCommitted != null) 'sap_committed': sapCommitted,
        if (sapAvailable != null) 'sap_available': sapAvailable,
        if (qtyPieces != null) 'qty_pieces': qtyPieces,
        if (qtyDozen != null) 'qty_dozen': qtyDozen,
        if (qtyCarton != null) 'qty_carton': qtyCarton,
      },
      options: Options(headers: {'X-Warehouse': wh}),
    );
  }

  Future<void> logout() async {
    await _storage.delete(key: 'token');
  }
}


