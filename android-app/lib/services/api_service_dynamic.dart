// import 'dart:convert';
// import 'package:http/http.dart' as http;
// import 'dart:io' show Platform;
// import 'package:flutter/foundation.dart' show kIsWeb;

// class ApiService {
//   // Dynamic base URL based on platform
//   static String get baseUrl {
//     if (kIsWeb) {
//       // Web - use localhost
//       return 'http://localhost:5000/api';
//     } else if (Platform.isAndroid) {
//       // Android emulator - use special IP
//       return 'http://10.0.2.2:5000/api';
//     } else if (Platform.isIOS) {
//       // iOS simulator - use localhost
//       return 'http://127.0.0.1:5000/api';
//     } else {
//       // Default fallback
//       return 'http://127.0.0.1:5000/api';
//     }
//   }
  
//   static const Map<String, String> headers = {
//     'Content-Type': 'application/json',
//     'Accept': 'application/json',
//   };

//   // Generic GET request
//   static Future<Map<String, dynamic>> get(String endpoint) async {
//     try {
//       final url = Uri.parse('$baseUrl$endpoint');
//       print('Making GET request to: $url'); // Debug log
      
//       final response = await http.get(url, headers: headers);
      
//       if (response.statusCode == 200) {
//         return json.decode(response.body);
//       } else {
//         throw ApiException('Failed to load data: ${response.statusCode}');
//       }
//     } catch (e) {
//       print('GET request error: $e'); // Debug log
//       throw ApiException('Network error: $e');
//     }
//   }

//   // Generic POST request
//   static Future<Map<String, dynamic>> post(String endpoint, Map<String, dynamic> data) async {
//     try {
//       final url = Uri.parse('$baseUrl$endpoint');
//       print('Making POST request to: $url'); // Debug log
//       print('POST data: $data'); // Debug log
      
//       final response = await http.post(
//         url,
//         headers: headers,
//         body: json.encode(data),
//       );
      
//       print('Response status: ${response.statusCode}'); // Debug log
//       print('Response body: ${response.body}'); // Debug log
      
//       if (response.statusCode == 200 || response.statusCode == 201) {
//         return json.decode(response.body);
//       } else {
//         final errorBody = json.decode(response.body);
//         throw ApiException(errorBody['message'] ?? 'Request failed: ${response.statusCode}');
//       }
//     } catch (e) {
//       print('POST request error: $e'); // Debug log
//       if (e is ApiException) {
//         rethrow;
//       }
//       throw ApiException('Network error: $e');
//     }
//   }

//   // Generic PUT request
//   static Future<Map<String, dynamic>> put(String endpoint, Map<String, dynamic> data) async {
//     try {
//       final url = Uri.parse('$baseUrl$endpoint');
//       final response = await http.put(
//         url,
//         headers: headers,
//         body: json.encode(data),
//       );
      
//       if (response.statusCode == 200) {
//         return json.decode(response.body);
//       } else {
//         final errorBody = json.decode(response.body);
//         throw ApiException(errorBody['message'] ?? 'Update failed: ${response.statusCode}');
//       }
//     } catch (e) {
//       if (e is ApiException) {
//         rethrow;
//       }
//       throw ApiException('Network error: $e');
//     }
//   }

//   // Generic DELETE request
//   static Future<Map<String, dynamic>> delete(String endpoint) async {
//     try {
//       final url = Uri.parse('$baseUrl$endpoint');
//       final response = await http.delete(url, headers: headers);
      
//       if (response.statusCode == 200) {
//         return json.decode(response.body);
//       } else {
//         final errorBody = json.decode(response.body);
//         throw ApiException(errorBody['message'] ?? 'Delete failed: ${response.statusCode}');
//       }
//     } catch (e) {
//       if (e is ApiException) {
//         rethrow;
//       }
//       throw ApiException('Network error: $e');
//     }
//   }
// }

// // Custom exception class for API errors
// class ApiException implements Exception {
//   final String message;
//   ApiException(this.message);
  
//   @override
//   String toString() => 'ApiException: $message';
// }