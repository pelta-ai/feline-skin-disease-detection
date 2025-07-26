import 'dart:developer';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:final_design/utils/auth_service.dart';
import 'package:final_design/utils/aws_s3_api.dart';
import 'package:final_design/utils/custom_app_bar.dart';
import 'package:final_design/utils/custom_text_fields.dart';
import 'package:final_design/utils/constants.dart';

class SignUpScreen extends StatelessWidget {
  const SignUpScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: "[App Name]",
        height: getScreenHeight(context) * 0.30,
        action: TextButton(
          onPressed: () {
            Navigator.pushReplacementNamed(context, '/');
          },
          style: TextButton.styleFrom(
            backgroundColor: COLOR_MAIN_LIGHT,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
          ),
          child: Text("Sign In", style: textThemeColor.bodySmall),
        ),
      ),
      body: const SignUp(),
    );
  }
}

class SignUp extends StatefulWidget {
  const SignUp({super.key});

  @override
  State<SignUp> createState() => _SignUpScreenState();
}

class _SignUpScreenState extends State<SignUp> {
  final _auth = AuthService();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _isLoading = false;

  Future<void> _signUpAndCreateFolder() async {
    try {
      setState(() => _isLoading = true);

      // 1. Create Firebase user
      User? user = await _auth.createUserWithEmailAndPassword(
        email: _emailController.text.trim(),
        password: _passwordController.text.trim(),
      );

      if (user == null) throw Exception("User creation failed");

      log("User created: ${user.uid}");

      // 2. Create S3 folder for the new user
      await S3ApiService.createUserFolder(user.uid);
      log("S3 folder created for user: ${user.uid}");

      if (mounted) {
        Navigator.pushReplacementNamed(context, '/home');
      }
    } catch (e) {
      log("Sign up failed: $e");
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text("Sign-up failed: ${e.toString()}")),
      );
    } finally {
      setState(() => _isLoading = false);
    }
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
                "Create new Account",
                style: textThemeColor.displayMedium,
                textAlign: TextAlign.center,
              ),
            ),
            const SizedBox(height: 16),
            CustomTextFields.buildTextFieldDesign1(_nameController, "NAME"),
            const SizedBox(height: 16),
            CustomTextFields.buildTextFieldDesign1(_emailController, "EMAIL"),
            const SizedBox(height: 16),
            CustomTextFields.buildTextFieldDesign1(
                _passwordController, "PASSWORD",
                obscure: true),
            const SizedBox(height: 20),
            Align(
              alignment: Alignment.center,
              child: SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: _isLoading ? null : _signUpAndCreateFolder,
                  style: TextButton.styleFrom(
                    backgroundColor: COLOR_MAIN,
                    padding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(30),
                    ),
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : Text("Sign up", style: textThemeWhite.titleSmall),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
