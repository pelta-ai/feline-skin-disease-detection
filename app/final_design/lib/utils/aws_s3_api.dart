import 'dart:convert';
import 'dart:io';
import 'dart:developer';
import 'package:http/http.dart' as http;

class S3ApiService {
  static const baseUrl =
      "https://d610ce6c86f7.ngrok-free.app"; // replace with your deployed endpoint in production

  // List S3 objects under a prefix
  static Future<List<String>> listObjectPaths({String prefix = ''}) async {
    final uri = Uri.parse('$baseUrl/list-objects?prefix=$prefix');
    final response = await http.get(uri);

    if (response.statusCode == 200) {
      List<dynamic> data = json.decode(response.body);
      return data.map((e) => e.toString()).toList(); // Convert each to String
    } else {
      throw Exception('Failed to load keys');
    }
  }

  // Check if a folder exists
  static Future<bool> folderExists(String path) async {
    final response =
        await http.get(Uri.parse('$baseUrl/folder-exists?path=$path'));

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
      headers: {'Content-Type': 'application/json'},
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
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'user_id': userId}),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to create today folder');
    }
  }

  // Upload a file
  static Future<void> uploadFile(File file, String userId) async {
    try {
      var uri = Uri.parse('$baseUrl/add-file');
      var request = http.MultipartRequest('POST', uri)
        ..fields['user_id'] = userId
        ..files.add(await http.MultipartFile.fromPath('file', file.path));
      var response = await request.send();
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
    final response = await http.get(url);
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['url'];
    }
    return null;
  }
}
