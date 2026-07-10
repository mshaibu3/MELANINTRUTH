import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class StoredSession {
  const StoredSession({
    required this.sessionId,
    required this.refreshToken,
  });

  final String sessionId;
  final String refreshToken;
}

abstract interface class SessionStore {
  Future<void> save(StoredSession session);
  Future<StoredSession?> read();
  Future<void> clear();
}

class SecureSessionStore implements SessionStore {
  SecureSessionStore({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  static const _sessionIdKey = 'melanintruth.session_id';
  static const _refreshTokenKey = 'melanintruth.refresh_token';

  final FlutterSecureStorage _storage;

  @override
  Future<void> save(StoredSession session) async {
    await _storage.write(key: _sessionIdKey, value: session.sessionId);
    await _storage.write(key: _refreshTokenKey, value: session.refreshToken);
  }

  @override
  Future<StoredSession?> read() async {
    final sessionId = await _storage.read(key: _sessionIdKey);
    final refreshToken = await _storage.read(key: _refreshTokenKey);
    if (sessionId == null || refreshToken == null) {
      return null;
    }
    return StoredSession(sessionId: sessionId, refreshToken: refreshToken);
  }

  @override
  Future<void> clear() async {
    await _storage.delete(key: _sessionIdKey);
    await _storage.delete(key: _refreshTokenKey);
  }
}

class MemorySessionStore implements SessionStore {
  StoredSession? _session;

  @override
  Future<void> save(StoredSession session) async {
    _session = session;
  }

  @override
  Future<StoredSession?> read() async => _session;

  @override
  Future<void> clear() async {
    _session = null;
  }
}
