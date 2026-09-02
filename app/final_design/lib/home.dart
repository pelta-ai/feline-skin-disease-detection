import 'dart:developer';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:final_design/storage/index.dart';
import 'package:final_design/diagnosis_store.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/utils/responsive.dart';
import 'package:final_design/web_shell.dart';
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
    if (isWide(context)) {
      return WebShell(
        active: '/home',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Hello ${_getDisplayName()}!",
                style: textThemeColor.displayMedium),
            const SizedBox(height: 6),
            Text("Let's check on your cat today.",
                style: textThemeColor.bodyMedium),
            const SizedBox(height: 12),
            const Home(),
          ],
        ),
      );
    }
    return _buildMobile(context);
  }

  Widget _buildMobile(BuildContext context) {
    return Scaffold(
        appBar: PreferredSize(
            preferredSize: Size.fromHeight(getScreenHeight(context) * 0.20),
            child: AppBar(
              backgroundColor: colorPrimary,
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
                      //StaticMiniCalendar(),
                      SizedBox(height: getScreenHeight(context) * 0.01),
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
                                  backgroundColor: Colors.white24,
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
                                        content:
                                            Text('Daily Check coming soon!'),
                                        duration: Duration(seconds: 2),
                                      ),
                                    );
                                  },
                                  style: TextButton.styleFrom(
                                    backgroundColor: Colors.white24,
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
  bool _isLoading = false;

  /// Processes the picked image: runs AI predictions on the backend, stores the
  /// result, notifies the user, and opens the Recent Diagnosis screen.
  /// The image is sent directly to the backend and is not stored in the cloud.
  Future<void> _processImage(XFile pickedFile) async {
    final fileName = pickedFile.name;
    final userId = currentUser!;

    final bytes = await pickedFile.readAsBytes();

    setState(() {
      _isLoading = true;
    });

    try {
      // Run predictions directly on the picked image bytes (no cloud upload)
      final result = await storage.generateAIPredictions(
        userId: userId,
        fileName: fileName,
        imageBytes: bytes,
      );

      if (!mounted || result == null) return;

      // Save the completed diagnosis so the Recent Diagnosis screen can show it.
      DiagnosisStore.save(DiagnosisResult.fromResponse(
        imageBytes: bytes,
        response: result,
        timestamp: DateTime.now(),
      ));

      if (!mounted) return;

      // In-app "analysis done" notification.
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Analysis complete — view it in Recent Diagnosis'),
          duration: Duration(seconds: 3),
        ),
      );

      // Show the result on the Recent Diagnosis screen instead of here.
      Navigator.pushNamed(context, '/recent_diagnosis');
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
    if (isWide(context)) return _buildWideDashboard(context);
    return _buildMobileScan(context);
  }

  // ---- Wide (web) dashboard -------------------------------------------------
  Widget _buildWideDashboard(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(flex: 3, child: _scanCard()),
        const SizedBox(width: 24),
        Expanded(
          flex: 2,
          child: Column(
            children: [
              _howItWorksCard(),
              const SizedBox(height: 20),
              _quickLinkCard(
                icon: Icons.history,
                title: "Recent Diagnosis",
                subtitle: "Review your past scans and results.",
                onTap: () => Navigator.pushNamed(context, '/recent_diagnosis'),
              ),
              const SizedBox(height: 20),
              _trustNote(),
            ],
          ),
        ),
      ],
    );
  }

  Widget _cardBox({required Widget child, EdgeInsets? padding}) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: colorSurface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: colorBorder),
      ),
      padding: padding ?? const EdgeInsets.all(24),
      child: child,
    );
  }

  Widget _scanCard() {
    return _cardBox(
      padding: const EdgeInsets.symmetric(horizontal: 40, vertical: 44),
      child: Column(
        children: [
          Container(
            width: 92,
            height: 92,
            decoration:
                const BoxDecoration(color: colorMain, shape: BoxShape.circle),
            child: const Icon(Icons.pets, size: 42, color: colorPrimary),
          ),
          const SizedBox(height: 22),
          Text("New Scan", style: textThemeColor.displayMedium),
          const SizedBox(height: 10),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 380),
            child: Text(
              "Upload or take a clear photo of your cat's affected skin, and Pelta will screen it for common conditions.",
              textAlign: TextAlign.center,
              style: textThemeColor.bodyMedium,
            ),
          ),
          const SizedBox(height: 28),
          if (_isLoading)
            _loadingState()
          else
            Wrap(
              spacing: 14,
              runSpacing: 14,
              alignment: WrapAlignment.center,
              children: [
                ElevatedButton.icon(
                  onPressed: _pickImageFromGallery,
                  icon: const Icon(Icons.upload_outlined, size: 20),
                  label: const Text("Upload Image"),
                ),
                OutlinedButton.icon(
                  onPressed: _pickImageFromCamera,
                  icon: const Icon(Icons.photo_camera_outlined, size: 20),
                  label: const Text("Use Camera"),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: colorPrimary,
                    side: const BorderSide(color: colorPrimary),
                    padding: const EdgeInsets.symmetric(
                        vertical: 16, horizontal: 24),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16)),
                    textStyle: textThemeColor.bodyLarge,
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }

  Widget _loadingState() {
    return Column(
      children: [
        const CircularProgressIndicator(color: colorPrimary),
        const SizedBox(height: 16),
        Text("Analyzing image...", style: textThemeColor.bodyLarge),
        const SizedBox(height: 6),
        Text("This may take a few seconds", style: textThemeColor.bodySmall),
      ],
    );
  }

  Widget _howItWorksCard() {
    Widget step(String n, String title, String body) {
      return Padding(
        padding: const EdgeInsets.only(top: 16),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Container(
              width: 28,
              height: 28,
              alignment: Alignment.center,
              decoration: const BoxDecoration(
                  color: colorMain, shape: BoxShape.circle),
              child: Text(n,
                  style: textThemeColor.bodyLarge?.copyWith(
                      color: colorPrimary, fontWeight: FontWeight.w700)),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: textThemeColor.bodyLarge),
                  const SizedBox(height: 2),
                  Text(body, style: textThemeColor.bodyMedium),
                ],
              ),
            ),
          ],
        ),
      );
    }

    return _cardBox(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text("How it works", style: textThemeColor.titleMedium),
          step("1", "Add a photo",
              "Upload or snap a picture of the affected area."),
          step("2", "AI screening",
              "Pelta checks it against common feline skin conditions."),
          step("3", "Get guidance",
              "See the result and whether to consult a vet."),
        ],
      ),
    );
  }

  Widget _quickLinkCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(20),
        onTap: onTap,
        child: _cardBox(
          child: Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: const BoxDecoration(
                    color: colorMain, shape: BoxShape.circle),
                child: Icon(icon, color: colorPrimary, size: 22),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(title, style: textThemeColor.bodyLarge),
                    const SizedBox(height: 2),
                    Text(subtitle, style: textThemeColor.bodyMedium),
                  ],
                ),
              ),
              const Icon(Icons.chevron_right, color: colorGrayDark),
            ],
          ),
        ),
      ),
    );
  }

  Widget _trustNote() {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: colorMain,
        borderRadius: BorderRadius.circular(20),
      ),
      padding: const EdgeInsets.all(20),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.info_outline, color: colorPrimary, size: 22),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              "Pelta is a screening aid, not a veterinary diagnosis. Always consult a vet for medical concerns.",
              style: textThemeColor.bodyMedium?.copyWith(color: colorBlack),
            ),
          ),
        ],
      ),
    );
  }

  // ---- Mobile scan ----------------------------------------------------------
  Widget _buildMobileScan(BuildContext context) {
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
                            backgroundColor:
                                _isLoading ? Colors.grey : colorPrimary,
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
                              backgroundColor:
                                  _isLoading ? Colors.grey : colorPrimary,
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
                    color: colorPrimary,
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
        ],
      ),
    ));
  }
}
