import 'dart:developer';
import 'package:final_design/utils/custom_text_fields.dart';
import 'package:flutter/material.dart';
import 'package:final_design/utils/custom_app_bar.dart';
import 'package:final_design/utils/constants.dart';
import 'package:final_design/utils/auth_service.dart';

class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
        appBar: CustomAppBar(
          title: "[App Name]",
          height: getScreenHeight(context) * 0.30,
          action: TextButton(
              onPressed: () {
                Navigator.pushReplacementNamed(context, '/sign_up');
              },
              style: TextButton.styleFrom(
                backgroundColor: COLOR_MAIN_LIGHT,
                padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(20),
                ),
              ),
              child: Text(
                "Get Started",
                style: textThemeColor.bodySmall,
              )),
        ),
        body: Login());
  }
}

class Login extends StatefulWidget {
  @override
  State<Login> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<Login> {
  final _auth = AuthService();

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
          CustomTextFields.buildTextFieldDesign1(
              _passwordController, "PASSWORD",
              obscure: true),

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
                        backgroundColor: COLOR_MAIN,
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
                onPressed: () {
                  // TODO: Navigate to reset password screen or show dialog
                },
                child: Text(
                  "Forgot Password?",
                  style: textThemeColor.bodySmall,
                ),
              ),
            ),
          ),
        ],
      ),
    ));
  }

  _signIn() async {
    final user = await _auth.loginUserWithEmailAndPassword(
        email: _emailController.text, password: _passwordController.text);

    if (user != null) {
      log("User Created Succesfully");
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      // Show error: user does not exist or wrong credentials
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Invalid email or password')),
      );
    }
  }
}
