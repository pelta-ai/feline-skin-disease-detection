import 'dart:convert';
import 'dart:io';
import 'dart:developer';
import 'package:http/http.dart' as http;
import 'package:final_design/utils/app_config.dart';
import 'package:final_design/utils/request_id.dart';

/// Default headers for all API requests
Map<String, String> _defaultHeaders() => {
      'X-Request-ID': RequestId.generate(),
    };

/// Extension for fluent header building on Map
extension HeadersExtension on Map<String, String> {
  Map<String, String> withJson() => {...this, 'Content-Type': 'application/json'};
}

/// Extension for adding headers to MultipartRequest
extension MultipartRequestExtension on http.MultipartRequest {
  http.MultipartRequest withDefaultHeaders() {
    headers.addAll(_defaultHeaders());
    return this;
  }
}

class S3ApiService {
  /// Backend URL configured via AppConfig
  static String get baseUrl => AppConfig.backendUrl;

  // List S3 objects under a prefix
  static Future<List<String>> listObjectPaths({String prefix = ''}) async {
    final uri = Uri.parse('$baseUrl/list-objects?prefix=$prefix');
    final response = await http.get(uri, headers: _defaultHeaders());

    if (response.statusCode == 200) {
      List<dynamic> data = json.decode(response.body);
      return data.map((e) => e.toString()).toList();
    } else {
      throw Exception('Failed to load keys');
    }
  }

  // Check if a folder exists
  static Future<bool> folderExists(String path) async {
    final response = await http.get(
      Uri.parse('$baseUrl/folder-exists?path=$path'),
      headers: _defaultHeaders(),
    );

    if (response.statusCode == 200) {
      return jsonDecode(response.body)['exists'];
    } else {
      throw Exception('Failed to check folder existence');
    }
  }

  // Create user folder
  static Future<void> createUserFolder(String userId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/create-user-folder'),
      headers: _defaultHeaders().withJson(),
      body: jsonEncode({'user_id': userId}),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to create user folder');
    }
  }

  // Create today's folder for a user
  static Future<void> createTodayFolder(String userId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/create-today-folder'),
      headers: _defaultHeaders().withJson(),
      body: jsonEncode({'user_id': userId}),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to create today folder');
    }
  }

  // Upload a file
  static Future<void> uploadFile(
      File file, String userId, bool isAnnotated) async {
    try {
      final uri = Uri.parse('$baseUrl/add-file');
      final request = http.MultipartRequest('POST', uri)
        ..fields['user_id'] = userId
        ..fields['is_annotated'] = isAnnotated.toString()
        ..files.add(await http.MultipartFile.fromPath('file', file.path));

      final response = await request.withDefaultHeaders().send();

      if (response.statusCode == 200) {
        log('Upload successful');
      } else {
        log('Upload failed: ${response.statusCode}');
      }
    } catch (e) {
      log("Upload error: $e");
    }
  }

  // Get presigned file URL
  static Future<String?> getFileUrl(String filePath) async {
    final url = Uri.parse('$baseUrl/get-file-url?path=$filePath');
    final response = await http.get(url, headers: _defaultHeaders());

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['url'];
    }
    return null;
  }

  static Future<void> triggerDownloadFromS3(
      {required File pickedFile, required String userId}) async {
    try {
      final fullPath = pickedFile.path;
      final fileName = fullPath.split('/').last;

      final today = await getTodayDateFromBackend();
      if (today == null) {
        log('Failed to fetch date from backend');
        return;
      }
      final s3Key = '$userId/$today/images/$fileName';

      final uri = Uri.parse('$baseUrl/download-file');
      final request = http.MultipartRequest('POST', uri)
        ..fields['user_id'] = userId
        ..fields['file_name'] = fileName
        ..fields['s3_key'] = s3Key;

      final response = await request.withDefaultHeaders().send();
      final body = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        log('Download-from-S3 triggered OK: $body');
      } else {
        log('Download-from-S3 failed: ${response.statusCode} — $body');
      }
    } catch (e) {
      log('Error calling download-from-s3: $e');
    }
  }

  static Future<String?> getTodayDateFromBackend() async {
    try {
      final url = Uri.parse('$baseUrl/get-today-date');
      final response = await http.get(url, headers: _defaultHeaders());

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['date'];
      }
      return null;
    } catch (e) {
      log("Error fetching date: $e");
      return null;
    }
  }

  static Future<Map<String, dynamic>?> generateAIPredictions({
    required String userId,
    required String fileName,
    required String s3Key,
  }) async {
    final uri = Uri.parse("$baseUrl/generate-ai-predictions");
    final request = http.MultipartRequest('POST', uri)
      ..fields['user_id'] = userId
      ..fields['file_name'] = fileName
      ..fields['s3_key'] = s3Key;

    final response = await request.withDefaultHeaders().send();
    final body = await response.stream.bytesToString();

    if (response.statusCode == 200) {
      return jsonDecode(body) as Map<String, dynamic>;
    } else {
      log("Error generating AI predictions: $body");
      return null;
    }
  }
}
