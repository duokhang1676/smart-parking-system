import '../services/api_service.dart';

class AuthService {
  // Login user - matching your Flask endpoint structure
  static Future<Map<String, dynamic>> login(String phone, String password) async {
    final data = {
      'user_id': phone,  // Your Flask expects 'user_id' for phone
      'password': password,
    };
    
    try {
      final response = await ApiService.post('/users/login', data);
      return response;
    } catch (e) {
      // Re-throw the specific exception to preserve error type
      rethrow;
    }
  }

  // Register user - matching your Flask signin endpoint
  static Future<Map<String, dynamic>> register(String phone, String name, String password) async {
    final data = {
      'user_id': phone,  // Your Flask expects 'user_id' for phone
      'name': name,
      'password': password,
    };
    
    try {
      final response = await ApiService.post('/users/signin', data);
      return response;
    } catch (e) {
      // Re-throw the specific exception to preserve error type
      rethrow;
    }
  }

  // Get user profile - userId is the phone number stored in database user_id field
  static Future<Map<String, dynamic>> getUserProfile(String userId) async {
    try {
      final response = await ApiService.get('/users/$userId');
      return response;
    } catch (e) {
      throw Exception('Failed to get user profile: $e');
    }
  }

  // Update user profile
  static Future<Map<String, dynamic>> updateUserProfile(String userId, Map<String, dynamic> userData) async {
    try {
      final response = await ApiService.put('/users/$userId', userData);
      return response;
    } catch (e) {
      throw Exception('Failed to update profile: $e');
    }
  }

  // Helper method to check login response status
  static bool isLoginSuccessful(Map<String, dynamic> response) {
    return response['status'] == 'success';
  }

  // Helper method to get user ID from successful login response
  static String? getUserIdFromResponse(Map<String, dynamic> response) {
    if (isLoginSuccessful(response)) {
      return response['message']; // Your Flask returns user_id in message field
    }
    return null;
  }

  // Helper method to get error message from failed login
  static String getErrorMessage(Map<String, dynamic> response) {
    return response['message'] ?? 'Unknown error occurred';
  }

  // Helper method to check registration response status
  static bool isRegistrationSuccessful(Map<String, dynamic> response) {
    return response['status'] == 'success';
  }

  // Helper method to check if user already exists
  static bool isUserAlreadyExists(Map<String, dynamic> response) {
    return response['status'] == 'exists';
  }

  // Helper method to get registration error message
  static String getRegistrationErrorMessage(Map<String, dynamic> response) {
    return response['message'] ?? 'Registration failed';
  }
}