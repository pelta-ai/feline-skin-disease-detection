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

  Future<void> _pickImageFromCamera() async {
    final picker = ImagePicker();
    final pickedFile = await picker.pickImage(source: ImageSource.camera);
    if (pickedFile != null) {
      setState(() async {
        _imageFile = pickedFile;
        File file = File(_imageFile!.path);
        await S3ApiService.uploadFile(file, "$CURRENT_USER");
        await S3ApiService.triggerDownloadFromS3(
          pickedFile: file,
          userId: "$CURRENT_USER",
        );
      });
    }

    Navigator.pushNamed(context, '/recent_diagnosis');
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
          if (_imageFile != null)
            Padding(
              padding: const EdgeInsets.only(top: 20),
              child: Image.file(
                File(_imageFile!.path),
                width: 200,
                height: 200,
                fit: BoxFit.cover,
              ),
            ),
        ],
      ),
    ));
  }
}
