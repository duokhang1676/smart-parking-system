import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Your Flask server URL - Android Emulator uses special IP
  // static const String baseUrl = 'http://10.0.2.2:5000/api';
  static const String baseUrl = 'https://parking-cloud-server.onrender.com/api';
  
  // Alternative IPs for different environments:
  // static const String baseUrl = 'http://192.168.1.19:5000/api'; // Physical device
  // static const String baseUrl = 'http://127.0.0.1:5000/api';    // iOS simulator
  // static const String baseUrl = 'http://localhost:5000/api';    // Web browser
  
  static const Map<String, String> headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  // Generic GET request
  static Future<Map<String, dynamic>> get(String endpoint) async {
    try {
      final url = Uri.parse('$baseUrl$endpoint');
      final response = await http.get(url, headers: headers);
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw ApiException('Failed to load data: ${response.statusCode}');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw NetworkException('Unable to connect to server. Please check your internet connection.');
    }
  }

  // Generic GET request that returns raw JSON (for APIs that return arrays)
  static Future<dynamic> getRaw(String endpoint) async {
    try {
      final url = Uri.parse('$baseUrl$endpoint');
      final response = await http.get(url, headers: headers);
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw ApiException('Failed to load data: ${response.statusCode}');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw NetworkException('Unable to connect to server. Please check your internet connection.');
    }
  }

  // Generic POST request
  static Future<Map<String, dynamic>> post(String endpoint, Map<String, dynamic> data) async {
    try {
      final url = Uri.parse('$baseUrl$endpoint');
      final response = await http.post(
        url,
        headers: headers,
        body: json.encode(data),
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        return json.decode(response.body);
      } else {
        // Handle different HTTP status codes
        final errorBody = json.decode(response.body);
        final errorMessage = errorBody['message'] ?? 'Request failed';
        
        switch (response.statusCode) {
          case 400:
            throw BadRequestException(errorMessage);
          case 401:
            throw UnauthorizedException(errorMessage);
          case 404:
            throw NotFoundException(errorMessage);
          case 409:
            throw ConflictException(errorMessage);
          case 500:
            throw ServerException(errorMessage);
          default:
            throw ApiException(errorMessage);
        }
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      // Network connectivity issues
      throw NetworkException('Unable to connect to server. Please check your internet connection.');
    }
  }

  // Generic PUT request
  static Future<Map<String, dynamic>> put(String endpoint, Map<String, dynamic> data) async {
    try {
      final url = Uri.parse('$baseUrl$endpoint');
      final response = await http.put(
        url,
        headers: headers,
        body: json.encode(data),
      );
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final errorBody = json.decode(response.body);
        throw ApiException(errorBody['message'] ?? 'Update failed: ${response.statusCode}');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw NetworkException('Unable to connect to server. Please check your internet connection.');
    }
  }

  // Generic DELETE request
  static Future<Map<String, dynamic>> delete(String endpoint) async {
    try {
      final url = Uri.parse('$baseUrl$endpoint');
      final response = await http.delete(url, headers: headers);
      
      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        final errorBody = json.decode(response.body);
        throw ApiException(errorBody['message'] ?? 'Delete failed: ${response.statusCode}');
      }
    } catch (e) {
      if (e is ApiException) {
        rethrow;
      }
      throw NetworkException('Unable to connect to server. Please check your internet connection.');
    }
  }
}

// Custom exception classes for different types of errors
class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  
  @override
  String toString() => 'ApiException: $message';
}

class NetworkException extends ApiException {
  NetworkException(String message) : super(message);
  
  @override
  String toString() => 'NetworkException: $message';
}

class BadRequestException extends ApiException {
  BadRequestException(String message) : super(message);
  
  @override
  String toString() => 'BadRequestException: $message';
}

class UnauthorizedException extends ApiException {
  UnauthorizedException(String message) : super(message);
  
  @override
  String toString() => 'UnauthorizedException: $message';
}

class NotFoundException extends ApiException {
  NotFoundException(String message) : super(message);
  
  @override
  String toString() => 'NotFoundException: $message';
}

class ServerException extends ApiException {
  ServerException(String message) : super(message);
  
  @override
  String toString() => 'ServerException: $message';
}

class ConflictException extends ApiException {
  ConflictException(String message) : super(message);
  
  @override
  String toString() => 'ConflictException: $message';
}