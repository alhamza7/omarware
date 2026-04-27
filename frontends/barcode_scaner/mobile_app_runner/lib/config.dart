class AppConfig {
  /// غيّر هذا إلى IP الكمبيوتر الذي يشغّل السيرفر داخل الشبكة
  /// مثال: http://192.168.116.211:8020
  static const String baseUrl = String.fromEnvironment(
    'BASE_URL',
    // افتراضيًا: IP الجهاز الذي يشغّل السيرفر (عدّل إذا تغيّر)
    defaultValue: 'http://192.168.116.211:8020',
  );
}


