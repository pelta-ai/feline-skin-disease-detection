import 'dart:developer';
import 'package:flutter/material.dart';
import 'package:final_design/utils/custom_app_bar.dart';
import 'package:final_design/utils/custom_text_fields.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/utils/validators.dart';
import 'package:final_design/auth/index.dart';
import 'package:final_design/storage/index.dart';

class SignUpScreen extends StatelessWidget {
  const SignUpScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: "Pelta AI",
        height: getScreenHeight(context) * 0.30,
        action: TextButton(
          onPressed: () {
            Navigator.pushReplacementNamed(context, '/');
          },
          style: TextButton.styleFrom(
            backgroundColor: colorMainLight,
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
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  bool _isLoading = false;

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _signUpAndCreateFolder() async {
    // Validate inputs
    final nameError = Validators.validateName(_nameController.text);
    if (nameError != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(nameError)),
      );
      return;
    }

    final emailError = Validators.validateEmail(_emailController.text);
    if (emailError != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(emailError)),
      );
      return;
    }

    final passwordError = Validators.validatePassword(_passwordController.text);
    if (passwordError != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(passwordError)),
      );
      return;
    }

    final confirmError = Validators.validateConfirmPassword(
      _passwordController.text,
      _confirmPasswordController.text,
    );
    if (confirmError != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(confirmError)),
      );
      return;
    }

    setState(() => _isLoading = true);

    try {
      // 1. Create user with auth provider (handles display name internally)
      final result = await auth.signUp(
        _emailController.text.trim(),
        _passwordController.text.trim(),
        _nameController.text.trim(),
      );

      if (!mounted) return;

      if (!result.success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result.errorMessage ?? 'Sign-up failed')),
        );
        return;
      }

      log("User created: ${result.userId}");

      // 2. Try to create storage folder (non-blocking - don't prevent navigation if this fails)
      if (result.userId != null) {
        try {
          await storage.createUserFolder(result.userId!);
          log("Storage folder created for user: ${result.userId}");
        } catch (storageError) {
          // Storage folder creation failed (backend might be down)
          // Don't block sign-up - folder can be created later on first upload
          log("Warning: Storage folder creation failed: $storageError");
        }
      }

      // SECURITY: Clear password fields after successful auth
      _passwordController.clear();
      _confirmPasswordController.clear();

      if (mounted) {
        Navigator.pushReplacementNamed(context, '/verify_email');
      }
    } catch (e) {
      log("Sign up failed: $e");
      // SECURITY: Clear password fields even on failure
      _passwordController.clear();
      _confirmPasswordController.clear();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text("Sign-up failed: ${e.toString()}")),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
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
            PasswordTextField(
              controller: _passwordController,
              hint: "PASSWORD",
            ),
            const SizedBox(height: 16),
            PasswordTextField(
              controller: _confirmPasswordController,
              hint: "CONFIRM PASSWORD",
            ),
            const SizedBox(height: 20),
            Align(
              alignment: Alignment.center,
              child: SizedBox(
                width: double.infinity,
                child: TextButton(
                  onPressed: _isLoading ? null : _signUpAndCreateFolder,
                  style: TextButton.styleFrom(
                    backgroundColor: colorMain,
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
