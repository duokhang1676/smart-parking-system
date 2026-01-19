import 'package:flutter/foundation.dart';
import 'user_service.dart';

class UserSession extends ChangeNotifier {
  static final UserSession _instance = UserSession._internal();
  factory UserSession() => _instance;
  UserSession._internal();

  // Private user data
  String? _userId;
  String? _userName;
  String? _userPhone;
  bool _isLoggedIn = false;
  bool _isLoading = false;

  // Getters (read-only access)
  String get userId => _userId ?? '';
  String get userName => _userName ?? 'User';
  String get userPhone => _userPhone ?? '';
  bool get isLoggedIn => _isLoggedIn;
  bool get isLoading => _isLoading;

  // Initialize session after login
  Future<void> initializeSession({
    required String userId,
    required String userPhone,
  }) async {
    try {
      _isLoading = true;
      notifyListeners();

      _userId = userId;
      _userPhone = userPhone;
      _isLoggedIn = true;
      
      // Load real user data from API once
      print('UserSession: Loading user info for userId: $userId');
      final userInfo = await UserService.getUserInfo(userId);
      _userName = userInfo['name'] ?? 'User';
      
      _isLoading = false;
      notifyListeners();
      
      print('UserSession initialized: userId=$userId, name=$_userName, phone=$userPhone');
    } catch (e) {
      print('Failed to initialize user session: $e');
      // Keep basic info even if API fails
      _userName = 'User';
      _isLoading = false;
      notifyListeners();
    }
  }

  // Get user data as Map for backward compatibility
  Map<String, dynamic> getUserData() {
    return {
      'userId': userId,
      'userPhone': userPhone,
      'userName': userName,
    };
  }

  // Clear session on logout
  void clearSession() {
    _userId = null;
    _userName = null;
    _userPhone = null;
    _isLoggedIn = false;
    _isLoading = false;
    notifyListeners();
    print('UserSession cleared');
  }

  // Validate session
  bool isValidSession() {
    return _isLoggedIn && 
           _userId != null && 
           _userId!.isNotEmpty;
  }

  // Debug info
  void printSessionInfo() {
    print('UserSession Info:');
    print('  - UserId: $_userId');
    print('  - UserName: $_userName');
    print('  - UserPhone: $_userPhone');
    print('  - IsLoggedIn: $_isLoggedIn');
    print('  - IsLoading: $_isLoading');
  }
}