import 'dart:developer';

import 'package:final_design/utils/aws_s3_api.dart';
import 'package:flutter/material.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/mini_calendar.dart';
import 'package:final_design/drawer.dart';
import 'package:image_picker/image_picker.dart';
import 'dart:io';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: PreferredSize(
            preferredSize: Size.fromHeight(getScreenHeight(context) * 0.30),
            child: AppBar(
              backgroundColor: COLOR_MAIN,
              automaticallyImplyLeading: true,
              iconTheme: IconThemeData(color: COLOR_WHITE),
              flexibleSpace: Stack(
                children: [
                  Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(top: 60),
                        child: Text(
                          "Hello [Username]!",
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
                                  backgroundColor: COLOR_MAIN_TRANSPARENT,
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
                                  onPressed: () {},
                                  style: TextButton.styleFrom(
                                    backgroundColor: COLOR_MAIN_TRANSPARENT,
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
  XFile? _imageFile;
  String? _predictedLabel;
  String? _annotatedImageUrl;

  Future<void> _pickImageFromCamera() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.camera);
    if (pickedFile == null) return;

    final file = File(pickedFile.path);
    final fileName = pickedFile.name; // or: path.split('/').last
    final userId = CURRENT_USER!; // or handle null safely

    setState(() {
      _imageFile = pickedFile;
      _predictedLabel = null;
      _annotatedImageUrl = null;
    });

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
                color: COLOR_MAIN_TRANSPARENT,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                  children: [
                    Padding(padding: const EdgeInsets.only(top: 65)),
                    Expanded(
                      child: TextButton(
                          onPressed: () {},
                          style: TextButton.styleFrom(
                            backgroundColor: COLOR_MAIN,
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
                            onPressed: _pickImageFromCamera,
                            style: TextButton.styleFrom(
                              backgroundColor: COLOR_MAIN,
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
          if (_annotatedImageUrl != null)
            Padding(
              padding: const EdgeInsets.only(top: 20),
              child: Image.network(
                _annotatedImageUrl!,
                width: 200,
                height: 200,
                fit: BoxFit.cover,
              ),
            )
        ],
      ),
    ));
  }
}
