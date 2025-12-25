class AppConfig {
  /// غيّر هذا إلى IP الكمبيوتر الذي يشغّل السيرفر داخل الشبكة
  /// مثال: http://192.168.116.204:3000
  static const String baseUrl = String.fromEnvironment(
    'BASE_URL',
    defaultValue: 'http://10.0.2.2:3000', // Android emulator -> host
  );
}












