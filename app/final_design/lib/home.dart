import 'dart:developer';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:final_design/utils/aws_s3_api.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/mini_calendar.dart';
import 'package:final_design/drawer.dart';
import 'package:final_design/auth/index.dart';

/// Gets user's display name, falling back to email or "there"
String _getDisplayName() {
  if (!auth.isLoggedIn) return "there";
  final displayName = auth.currentUserDisplayName;
  if (displayName != null && displayName.isNotEmpty) {
    return displayName;
  }
  final email = auth.currentUserEmail;
  if (email != null && email.isNotEmpty) {
    // Use part before @ for email
    return email.split('@').first;
  }
  return "there";
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: PreferredSize(
            preferredSize: Size.fromHeight(getScreenHeight(context) * 0.30),
            child: AppBar(
              backgroundColor: colorMain,
              automaticallyImplyLeading: true,
              iconTheme: IconThemeData(color: colorWhite),
              flexibleSpace: Stack(
                children: [
                  Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(top: 60),
                        child: Text(
                          "Hello ${_getDisplayName()}!",
                          style: textThemeWhite.displaySmall,
                        ),
                      ),
                      StaticMiniCalendar(),
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                        children: [
                          Padding(
                              padding:
                                  const EdgeInsets.symmetric(horizontal: 20)),
                          Expanded(
                            child: TextButton(
                                onPressed: () {
                                  Navigator.pushNamed(
                                      context, '/recent_diagnosis');
                                },
                                style: TextButton.styleFrom(
                                  backgroundColor: colorMainTransparent,
                                  padding: EdgeInsets.symmetric(
                                      horizontal: 16, vertical: 20),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(30),
                                  ),
                                ),
                                child: Text(
                                  "Recent Diagnosis",
                                  style: textThemeWhite.titleSmall,
                                )),
                          ),
                          SizedBox(width: 12),
                          Expanded(
                              child: TextButton(
                                  onPressed: () {
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      const SnackBar(
                                        content: Text('Daily Check coming soon!'),
                                        duration: Duration(seconds: 2),
                                      ),
                                    );
                                  },
                                  style: TextButton.styleFrom(
                                    backgroundColor: colorMainTransparent,
                                    padding: EdgeInsets.symmetric(
                                        horizontal: 16, vertical: 20),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(30),
                                    ),
                                  ),
                                  child: Text(
                                    "Daily Check",
                                    style: textThemeWhite.titleSmall,
                                  ))),
                          Padding(
                              padding:
                                  const EdgeInsets.symmetric(horizontal: 20)),
                        ],
                      )
                    ],
                  )
                ],
              ),
              shape: const RoundedRectangleBorder(
                borderRadius:
                    BorderRadius.vertical(bottom: Radius.circular(20)),
              ),
            )),
        drawer: createDrawer(context, "Home"),
        body: Home());
  }
}

class Home extends StatefulWidget {
  const Home({super.key});

  @override
  State<Home> createState() => _HomeState();
}

class _HomeState extends State<Home> {
  String? _predictedLabel;
  String? _annotatedImageUrl;
  bool _isLoading = false;

  /// Processes the picked image: uploads to S3, runs AI predictions, and displays results
  Future<void> _processImage(XFile pickedFile) async {
    final file = File(pickedFile.path);
    final fileName = pickedFile.name;
    final userId = currentUser!;

    setState(() {
      _predictedLabel = null;
      _annotatedImageUrl = null;
      _isLoading = true;
    });

    try {
      // 1. Upload image
      await S3ApiService.uploadFile(file, userId, false);

      // 2. Get today's folder name from backend
      final today = await S3ApiService.getTodayDateFromBackend();
      if (today == null) {
        log("Could not get date from backend");
        return;
      }

      final s3Key = "$userId/$today/images/$fileName";

      // 3. Generate predictions (this will download from S3 + run YOLO+CNN)
      final result = await S3ApiService.generateAIPredictions(
        userId: userId,
        fileName: fileName,
        s3Key: s3Key,
      );

      if (!mounted || result == null) return;

      final label = result['label'] as String?;
      final annotatedUrl = result['annotated_url'] as String?;

      setState(() {
        _predictedLabel = label;
        _annotatedImageUrl = annotatedUrl;
      });
    } catch (e) {
      log("Error processing image: $e");
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Error processing image. Please try again.")),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _pickImageFromCamera() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.camera);
    if (pickedFile == null) return;
    await _processImage(pickedFile);
  }

  Future<void> _pickImageFromGallery() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.gallery);
    if (pickedFile == null) return;
    await _processImage(pickedFile);
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
        child: Container(
      padding: const EdgeInsets.only(top: 34, left: 61, right: 61),
      child: Column(
        children: [
          Align(
              alignment: Alignment.center,
              child: Text(
                "New Scan",
                style: textThemeColor.displayMedium,
                textAlign: TextAlign.center,
              )),
          Padding(padding: const EdgeInsets.only(top: 40)),
          Align(
              alignment: Alignment.center,
              child: Container(
                width: 333,
                height: 333,
                color: colorMainTransparent,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    Padding(padding: const EdgeInsets.only(top: 65)),
                    Expanded(
                      child: TextButton(
                          onPressed: _isLoading ? null : _pickImageFromGallery,
                          style: TextButton.styleFrom(
                            backgroundColor: _isLoading ? Colors.grey : colorMain,
                            padding: EdgeInsets.symmetric(
                                horizontal: 60, vertical: 25),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(30),
                            ),
                          ),
                          child: Text(
                            "Upload Image",
                            style: textThemeWhite.titleSmall,
                          )),
                    ),
                    SizedBox(height: 40),
                    Expanded(
                        child: TextButton(
                            onPressed: _isLoading ? null : _pickImageFromCamera,
                            style: TextButton.styleFrom(
                              backgroundColor: _isLoading ? Colors.grey : colorMain,
                              padding: EdgeInsets.symmetric(
                                  horizontal: 60, vertical: 25),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(30),
                              ),
                            ),
                            child: Text(
                              "Use Camera",
                              style: textThemeWhite.titleSmall,
                            ))),
                    Padding(padding: const EdgeInsets.only(bottom: 65)),
                  ],
                ),
              )),
          if (_isLoading)
            Padding(
              padding: const EdgeInsets.only(top: 30),
              child: Column(
                children: [
                  CircularProgressIndicator(
                    color: colorMain,
                  ),
                  SizedBox(height: 16),
                  Text(
                    "Analyzing image...",
                    style: textThemeColor.bodyLarge,
                  ),
                  SizedBox(height: 8),
                  Text(
                    "This may take a few seconds",
                    style: textThemeColor.bodySmall,
                  ),
                ],
              ),
            ),
          if (_annotatedImageUrl != null && !_isLoading)
            Padding(
              padding: const EdgeInsets.only(top: 20),
              child: Column(
                children: [
                  if (_predictedLabel != null)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Text(
                        "Detected: $_predictedLabel",
                        style: textThemeColor.titleMedium,
                      ),
                    ),
                  ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: Image.network(
                      _annotatedImageUrl!,
                      width: 280,
                      height: 280,
                      fit: BoxFit.cover,
                      loadingBuilder: (context, child, loadingProgress) {
                        if (loadingProgress == null) return child;
                        return SizedBox(
                          width: 280,
                          height: 280,
                          child: Center(
                            child: CircularProgressIndicator(
                              color: colorMain,
                            ),
                          ),
                        );
                      },
                    ),
                  ),
                ],
              ),
            )
        ],
      ),
    ));
  }
}
