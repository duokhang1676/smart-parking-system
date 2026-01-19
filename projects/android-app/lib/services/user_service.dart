import '../services/api_service.dart';

class UserService {
  // Get user information using getUserInfo API
  static Future<Map<String, dynamic>> getUserInfo(String userId) async {
    final data = {
      'action': 'get_user_info',
      'user_id': userId,
    };
    
    try {
      final response = await ApiService.post('/users/getUserInfo', data);
      
      if (response['status'] == 'success') {
        return response['data'];
      } else {
        throw Exception(response['message'] ?? 'Failed to get user information');
      }
    } catch (e) {
      rethrow;
    }
  }

  // Get user's registered parkings using dedicated API
  static Future<List<String>> getUserRegisters(String userId) async {
    final data = {
      'user_id': userId,
    };
    
    try {
      final response = await ApiService.post('/users/registered-parkings', data);
      
      if (response['status'] == 'success') {
        // Return the registered_parkings list directly
        return List<String>.from(response['registered_parkings'] ?? []);
      } else {
        throw Exception(response['message'] ?? 'No registered parkings found');
      }
    } catch (e) {
      rethrow;
    }
  }

  // Get parking information
  static Future<Map<String, dynamic>> getParkingInfo(String userId, String parkingId) async {
    final data = {
      'action': 'get_parking_info',
      'user_id': userId,
      'parking_id': parkingId,
    };
    
    try {
      final response = await ApiService.post('/users/getUserInfo', data);
      
      if (response['status'] == 'success') {
        return response['data'];
      } else {
        throw Exception(response['message'] ?? 'Parking information not found');
      }
    } catch (e) {
      rethrow;
    }
  }

  // Get registered vehicles for a user
  static Future<List<Map<String, dynamic>>> getRegisteredVehicles(String userId) async {
    try {
      final response = await ApiService.post('/registers/get_registered_vehicles', {
        'user_id': userId,
      });
      
      if (response['status'] == 'success') {
        return List<Map<String, dynamic>>.from(response['data'] ?? []);
      } else {
        throw Exception(response['message'] ?? 'Failed to get registered vehicles');
      }
    } catch (e) {
      rethrow;
    }
  }

  // Get parking histories for a user
  static Future<List<Map<String, dynamic>>> getParkingHistories(String userId) async {
    try {
      final response = await ApiService.post('/histories/get_parking_histories', {
        'user_id': userId,
      });
      
      if (response['status'] == 'success') {
        return List<Map<String, dynamic>>.from(response['data'] ?? []);
      } else {
        throw Exception(response['message'] ?? 'Failed to get parking histories');
      }
    } catch (e) {
      rethrow;
    }
  }
}