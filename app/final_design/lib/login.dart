import 'dart:developer';
import 'package:final_design/utils/custom_text_fields.dart';
import 'package:flutter/material.dart';
import 'package:final_design/utils/custom_app_bar.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/utils/validators.dart';
import 'package:final_design/auth/index.dart';

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: CustomAppBar(
          title: "Pelta AI",
          height: getScreenHeight(context) * 0.30,
        ),
        body: Login());
  }
}

class Login extends StatefulWidget {
  const Login({super.key});

  @override
  State<Login> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<Login> {
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  void dispose() {
    super.dispose();
    _emailController.dispose();
    _passwordController.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
        child: Container(
      padding: const EdgeInsets.only(top: 34, left: 61, right: 61),
      child: Column(
        children: [
          // "Welcome!" Text
          Align(
              alignment: Alignment.center,
              child: Text(
                "Welcome!",
                style: textThemeColor.displayMedium,
                textAlign: TextAlign.center,
              )),

          // "Sign in to continue!" text
          Align(
              alignment: Alignment.center,
              child: Padding(
                  padding: const EdgeInsets.only(top: 55),
                  child: Text(
                    "Sign in to continue!",
                    style: textThemeColor.bodySmall,
                    textAlign: TextAlign.center,
                  ))),

          const SizedBox(height: 16),
          CustomTextFields.buildTextFieldDesign1(_emailController, "EMAIL"),
          const SizedBox(height: 16),
          PasswordTextField(
            controller: _passwordController,
            hint: "PASSWORD",
          ),

          // Log in text button
          Align(
              alignment: Alignment.center,
              child: Padding(
                padding: const EdgeInsets.only(top: 16),
                child: SizedBox(
                  width: double.infinity,
                  child: TextButton(
                      onPressed: () {
                        _signIn();
                      },
                      style: TextButton.styleFrom(
                        backgroundColor: colorMain,
                        padding:
                            EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(30),
                        ),
                      ),
                      child: Text(
                        "Log in",
                        style: textThemeWhite.titleSmall,
                      )),
                ),
              )),

          // "Forgot Password?" text button
          Align(
            alignment: Alignment.center,
            child: Padding(
              padding: const EdgeInsets.only(top: 45),
              child: TextButton(
                onPressed: () => _resetPassword(),
                child: Text(
                  "Forgot Password?",
                  style: textThemeColor.bodySmall,
                ),
              ),
            ),
          ),

          // "New user? Sign up" text button
          Align(
            alignment: Alignment.center,
            child: Padding(
              padding: const EdgeInsets.only(top: 16),
              child: TextButton(
                onPressed: () {
                  Navigator.pushReplacementNamed(context, '/sign_up');
                },
                child: Text(
                  "New user? Sign up",
                  style: textThemeColor.bodySmall?.copyWith(
                    decoration: TextDecoration.underline,
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    ));
  }

  Future<void> _signIn() async {
    // Validate inputs
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

    final result = await auth.signIn(
      _emailController.text.trim(),
      _passwordController.text,
    );

    if (!mounted) return;

    if (result.success) {
      log("User Logged In Successfully");
      // SECURITY: Clear password field after successful auth
      _passwordController.clear();
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      // SECURITY: Clear password field on failure too
      _passwordController.clear();
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result.errorMessage ?? 'Login failed')),
      );
    }
  }

  Future<void> _resetPassword() async {
    final email = _emailController.text.trim();

    if (email.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please enter your email address first'),
        ),
      );
      return;
    }

    final result = await auth.sendPasswordResetEmail(email);

    if (!mounted) return;

    if (result.success) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Password reset email sent! Check your inbox.'),
          duration: Duration(seconds: 4),
        ),
      );
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(result.errorMessage ?? 'Failed to send reset email')),
      );
    }
  }
}
