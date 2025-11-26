import 'package:flutter/material.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/drawer.dart';
import 'package:final_design/utils/aws_s3_api.dart';

class RecentDiagnosisScreen extends StatelessWidget {
  const RecentDiagnosisScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: PreferredSize(
            preferredSize: Size.fromHeight(getScreenHeight(context) * 0.20),
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
                      ),
                      Center(
                        child: Text(
                          "Recent Diagnosis",
                          style: textThemeWhite.displaySmall,
                        ),
                      ),
                      Padding(
                        padding: const EdgeInsets.only(top: 20),
                      ),
                      Center(
                        child: Text(
                          DateTime.now().toLocal().toString().split(' ')[0],
                          style: textThemeWhite.displaySmall,
                        ),
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
        body: RecentDiagnosis());
  }
}

class RecentDiagnosis extends StatelessWidget {
  const RecentDiagnosis({super.key});

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<bool>(
      future: S3ApiService.folderExists("$CURRENT_USER/$TODAY_DATE/"),
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return Center(child: CircularProgressIndicator());
        } else if (snapshot.hasError) {
          return Center(child: Text("Error: ${snapshot.error}"));
        } else if (snapshot.data == false) {
          return Center(child: Text("No images found."));
        }

        // If folder exists, fetch object paths
        return FutureBuilder<List<String>>(
          future: S3ApiService.listObjectPaths(
              prefix: "$CURRENT_USER/$TODAY_DATE/annotated_images/"),
          builder: (context, listSnapshot) {
            if (listSnapshot.connectionState == ConnectionState.waiting) {
              return Center(child: CircularProgressIndicator());
            } else if (listSnapshot.hasError) {
              return Center(child: Text("Error: ${listSnapshot.error}"));
            } else if (!listSnapshot.hasData || listSnapshot.data!.isEmpty) {
              return Center(child: Text("No images in this folder."));
            }

            final paths = listSnapshot.data!;

            return Column(
              children: [
                SizedBox(height: 40),
                Padding(
                  padding: EdgeInsets.all(20),
                  child: Container(
                      width: double.infinity,
                      height: 300,
                      padding: EdgeInsets.all(20),
                      color: COLOR_MAIN,
                      child: Column(
                        children: [
                          Text(
                            "Images",
                            style: textThemeWhite.displaySmall,
                          ),
                          SizedBox(height: 20),
                          SingleChildScrollView(
                            scrollDirection: Axis.horizontal,
                            child: Row(
                              children: paths.map((path) {
                                return FutureBuilder<String?>(
                                  future: S3ApiService.getFileUrl(path),
                                  builder: (context, urlSnapshot) {
                                    if (urlSnapshot.connectionState ==
                                        ConnectionState.waiting) {
                                      return SizedBox(
                                          width: 120,
                                          height: 180,
                                          child: Center(
                                              child:
                                                  CircularProgressIndicator()));
                                    } else if (urlSnapshot.hasError ||
                                        urlSnapshot.data == null) {
                                      return SizedBox(
                                          width: 120,
                                          height: 180,
                                          child:
                                              Center(child: Icon(Icons.error)));
                                    }
                                    return Padding(
                                      padding: const EdgeInsets.all(8.0),
                                      child: Image.network(
                                        urlSnapshot.data!,
                                        width: 120,
                                        height: 180,
                                        fit: BoxFit.cover,
                                      ),
                                    );
                                  },
                                );
                              }).toList(),
                            ),
                          ),
                        ],
                      )),
                )
              ],
            );
          },
        );
      },
    );
  }
}
